import unittest
from controls import Body, Command, Gestures
from engine import Runner, Obstacle

BASE = Body(.5,.55,.3,.9,.25)

class GestureTests(unittest.TestCase):
    def ready(self):
        g=Gestures()
        for i in range(65):
            g.update(BASE,i/30)
        self.assertIsNotNone(g.baseline)
        return g

    def test_calibration_requires_visible_still_body(self):
        g=Gestures()
        for i in range(65):
            g.update(Body(.3 if i%2 else .7,.55,.3,.9,.25),i/30)
        self.assertIsNone(g.baseline)
        g.update(None,3)
        self.assertEqual(g.progress,0)

    def test_lateral_edge_and_rearm(self):
        g=self.ready()
        left=Body(.25,.55,.3,.9,.25)
        self.assertEqual(g.update(left,3).move,-1)
        self.assertEqual(g.update(left,3.1).move,0)
        for i in range(12):
            g.update(BASE,3.2+i*.04)
        moves=[g.update(left,4+i/30).move for i in range(8)]
        self.assertEqual(sum(moves),-1)

    def test_small_steps_change_lanes_both_directions(self):
        g=self.ready()
        left=Body(leg_x=.46,hip_y=.55,shoulder_y=.3,ankle_y=.9,torso=.25)
        right=Body(leg_x=.54,hip_y=.55,shoulder_y=.3,ankle_y=.9,torso=.25)
        self.assertIn(-1,[g.update(left,3+i/30).move for i in range(8)])
        for i in range(12):
            g.update(BASE,3.3+i*.04)
        self.assertIn(1,[g.update(right,4+i/30).move for i in range(8)])

    def test_jump_once_per_takeoff_and_diagonal(self):
        g=self.ready()
        b=Body(.75,.43,.18,.78,.25)
        c=g.update(b,3)
        self.assertTrue(c.jump)
        self.assertEqual(c.move,1)
        self.assertFalse(g.update(b,3.1).jump)
        for i in range(12):
            g.update(BASE,3.2+i*.04)
        self.assertTrue(g.update(b,4).jump)

    def test_squat_is_not_jump(self):
        g=self.ready()
        c=g.update(Body(.5,.66,.50,.9,.16),3)
        self.assertTrue(c.duck)
        self.assertFalse(c.jump)
        for i in range(10):
            self.assertFalse(g.update(BASE,3.1+i*.04).jump)

    def test_raised_hands_hold_and_release(self):
        g=self.ready()
        b=Body(.5,.55,.3,.9,.25,True)
        self.assertFalse(g.update(b,3).activate)
        # Actual camera frames arrive continuously.
        triggers=[g.update(b,3+i/30).activate for i in range(1,60)]
        self.assertEqual(sum(triggers),1)
        g.update(BASE,5)
        triggers=[g.update(b,5.1+i/30).activate for i in range(60)]
        self.assertEqual(sum(triggers),1)

    def test_tracking_loss_cancels_hand_hold(self):
        g=self.ready()
        b=Body(.5,.55,.3,.9,.25,True)
        g.update(b,3)
        g.update(None,3.5)
        self.assertFalse(g.update(b,5).activate)

class EngineTests(unittest.TestCase):
    def hit(self,kind,cmd):
        r=Runner(1)
        r.obstacles=[Obstacle(1,kind,.121)]
        r.update(.02,cmd)
        return r

    def test_barrier_requires_jump(self):
        self.assertFalse(self.hit('barrier',Command()).alive)
        self.assertTrue(self.hit('barrier',Command(jump=True)).alive)

    def test_beam_requires_duck(self):
        self.assertFalse(self.hit('beam',Command()).alive)
        self.assertTrue(self.hit('beam',Command(duck=True)).alive)

    def test_train_requires_lane_change(self):
        self.assertFalse(self.hit('train',Command(jump=True)).alive)
        self.assertTrue(self.hit('train',Command(move=1)).alive)

    def test_coin_scored_once(self):
        r=self.hit('coin',Command())
        self.assertEqual(r.coins,1)
        for _ in range(20):
            r.update(.02,Command())
        self.assertEqual(r.coins,1)

    def test_lane_bounds_and_dead_freeze(self):
        r=Runner()
        for _ in range(10):
            r.update(.01,Command(move=-1))
        self.assertEqual(r.lane,0)
        r.alive=False
        distance=r.distance
        r.update(.1,Command())
        self.assertEqual(r.distance,distance)

if __name__=='__main__':
    unittest.main()
