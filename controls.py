"""Pure gesture logic: normalized image coordinates, independent of CV libraries."""
from dataclasses import dataclass
from collections import deque
from statistics import median

DEFAULT_LATERAL = .15

@dataclass
class Body:
    waist_x: float
    hip_y: float
    shoulder_y: float
    knee_y: float
    torso: float
    hands_up: bool = False
    knees_visible: bool = True

@dataclass
class Command:
    move: int = 0
    jump: bool = False
    duck: bool = False
    activate: bool = False

class Gestures:
    def __init__(self, lateral=DEFAULT_LATERAL, jump=.22, duck=.35):
        self.lateral, self.jump_threshold, self.duck_threshold = lateral, jump, duck
        self.samples = deque()
        self.baseline = None
        self.filtered = None
        self.side_armed = self.jump_armed = True
        self.hand_since = None
        self.hand_latched = False
        self.last_seen = None
        self.progress = 0.0

    def reset(self):
        self.__init__(self.lateral, self.jump_threshold, self.duck_threshold)

    def update(self, body, now):
        c = Command()
        if body is None:
            self.samples.clear()
            self.progress = 0.0
            self.filtered = None
            self.hand_since = None
            self.last_seen = None
            return c
        if self.last_seen is None or now - self.last_seen > .4:
            self.filtered = None
            self.hand_since = None
        self.last_seen = now
        if self.baseline is None:
            if body.hands_up or body.torso < .08 or not body.knees_visible:
                self.samples.clear()
                self.progress = 0.0
                return c
            self.samples.append((now, body))
            while self.samples and now - self.samples[0][0] > 2.1:
                self.samples.popleft()
            span = now - self.samples[0][0]
            self.progress = min(1, span / 2)
            hips = [b.hip_y for _, b in self.samples]
            xs = [b.waist_x for _, b in self.samples]
            if max(hips)-min(hips) > .035 or max(xs)-min(xs) > .04:
                self.samples.clear()
                self.progress = 0.0
            elif span >= 2 and len(self.samples) >= 15:
                bs = [b for _, b in self.samples]
                self.baseline = Body(*(median(getattr(b, key) for b in bs)
                                      for key in ['waist_x','hip_y','shoulder_y','knee_y','torso']))
            return c
        if body.hands_up:
            if self.hand_since is None:
                self.hand_since = now
            if now - self.hand_since >= 1.2 and not self.hand_latched:
                c.activate = True
                self.hand_latched = True
        else:
            self.hand_since = None
            self.hand_latched = False
        if self.filtered is None:
            self.filtered = body
        else:
            self.filtered = Body(*(getattr(self.filtered,k)*.45 + getattr(body,k)*.55
                                   for k in ['waist_x','hip_y','shoulder_y','knee_y','torso']),
                                  body.hands_up, body.knees_visible)
        b, base = self.filtered, self.baseline
        scale = max(.08, base.torso)
        dx = (b.waist_x-base.waist_x)/scale
        if b.knees_visible:
            if abs(dx) < self.lateral*.45:
                self.side_armed = True
            if self.side_armed and abs(dx) > self.lateral:
                c.move = -1 if dx < 0 else 1
                self.side_armed = False
        rise = (base.hip_y-b.hip_y)/scale
        knee_rise = (base.knee_y-b.knee_y)/scale
        c.duck = (not b.knees_visible or (
            ((b.shoulder_y-base.shoulder_y)/scale > self.duck_threshold
             or b.torso/base.torso < .68) and rise < .1))
        # Knees AND hips must rise; standing upright after a squat is not a jump.
        if b.knees_visible and rise < self.jump_threshold*.4 and knee_rise < self.jump_threshold*.4:
            self.jump_armed = True
        if (b.knees_visible and self.jump_armed and rise > self.jump_threshold
            and knee_rise > self.jump_threshold*.65 and not c.duck):
            c.jump = True
            self.jump_armed = False
        return c
