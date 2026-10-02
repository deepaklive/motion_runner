"""Motion Runner: an original three-lane endless runner with body controls."""
import argparse
import math
from pathlib import Path
import sys
import time
import pygame
from controls import Gestures
from engine import Runner

W,H = 1100,720
BG=(12,18,36)
WHITE=(231,240,255)
CYAN=(55,219,229)

class Display:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W,H))
        pygame.display.set_caption('Motion Runner | Webcam controlled')
        self.font = pygame.font.Font(None,27)
        self.big = pygame.font.Font(None,54)

    def text(self, s, pos, color=WHITE, big=False):
        self.screen.blit((self.big if big else self.font).render(s,True,color),pos)

    def point(self, lane, z):
        p = max(0,min(1.15,1-z))**1.65
        return (int(400+(lane-1)*(35+185*p)),int(175+480*p)), p

    def draw(self, game, frame, message, calibrated, progress, gesture, paused):
        s=self.screen
        s.fill(BG)
        pygame.draw.circle(s,(30,55,84),(410,180),100)
        # Original procedural city skyline and perspective track.
        for i in range(12):
            x=i*69
            height=55+(i*43)%100
            pygame.draw.rect(s,(24,36,59),(x,175-height,49,height))
            for yy in range(185-height,165,24):
                pygame.draw.rect(s,(50,89,111),(x+9,yy,8,9))
        pygame.draw.polygon(s,(37,47,65),[(345,175),(455,175),(770,690),(30,690)])
        for edge in [-1.5,-.5,.5,1.5]:
            pygame.draw.line(s,(79,106,126),(int(400+edge*35),175),(int(400+edge*220),690),3)
        for i in range(13):
            z=(i/13+game.distance/140)%1
            (x,y),p=self.point(1,z)
            pygame.draw.line(s,(55,72,89),(int(x-330*p),y),(int(x+330*p),y),max(1,int(4*p)))
        for obj in sorted(game.obstacles,key=lambda o:o.z,reverse=True):
            (x,y),p=self.point(obj.lane,obj.z)
            width=int(16+65*p)
            if obj.kind=='coin':
                pygame.draw.circle(s,(255,214,67),(x,y-20),max(5,width//4))
            elif obj.kind=='beam':
                height=int(20+105*p)
                pygame.draw.rect(s,(233,123,200),(x-width//2,y-height,width,18))
                for xx in [x-width//2,x+width//2-6]:
                    pygame.draw.rect(s,(149,73,136),(xx,y-height,6,height))
            else:
                height=int((145 if obj.kind=='train' else 55)*(.25+p))
                rect=pygame.Rect(x-width//2,y-height,width,height)
                pygame.draw.rect(s,(79,132,210) if obj.kind=='train' else (246,131,72),rect,border_radius=5)
                pygame.draw.rect(s,WHITE,rect,2,border_radius=5)
                if obj.kind=='train':
                    pygame.draw.rect(s,(20,47,75),(rect.x+8,rect.y+12,max(1,width-16),height//3))
        (x,y),_=self.point(game.lane,.12)
        lift=math.sin(math.pi*(1-game.jump_left/.95))*100 if game.jump_left>0 else 0
        pygame.draw.ellipse(s,(16,24,35),(x-30,y-7,60,15))
        height=42 if game.duck else 85
        foot=int(y-lift)
        pygame.draw.rect(s,CYAN,(x-18,foot-height+22,36,height-25),border_radius=9)
        pygame.draw.circle(s,(255,210,160),(x,foot-height+10),15)
        pygame.draw.line(s,WHITE,(x-9,foot-5),(x-12,foot+3),5)
        pygame.draw.line(s,WHITE,(x+9,foot-5),(x+12,foot+3),5)
        pygame.draw.rect(s,(18,28,49),(810,0,290,H))
        self.text('MOTION RUNNER',(24,20),CYAN,True)
        self.text(f'Score {game.score}   Coins {game.coins}',(25,75))
        self.text('LIVE CAMERA',(835,24),CYAN)
        if frame is not None:
            surface=pygame.image.frombuffer(frame.tobytes(),(frame.shape[1],frame.shape[0]),'RGB')
            s.blit(pygame.transform.smoothscale(surface,(260,195)),(825,60))
        else:
            self.text('Camera unavailable',(830,120))
        self.text('BODY CONTROLS',(830,285),CYAN)
        for i,line in enumerate(['Jump: clear orange barriers','Bend: pass under pink beams','Move left/right: change lane','Blue trains: change lane','Gold coins: collect for points','','Return to center between','each left/right movement.','','Both hands up for 1.2 sec:','start / restart / pause.']):
            self.text(line,(825,325+i*25))
        self.text(f'Action: {gesture}',(825,625),CYAN)
        self.text('All camera processing is local',(825,680))
        if message:
            panel=pygame.Surface((750,110),pygame.SRCALPHA)
            panel.fill((9,16,31,225))
            s.blit(panel,(25,245))
            self.text(message,(42,263),WHITE)
            if not calibrated:
                pygame.draw.rect(s,(40,60,78),(42,305,700,14),border_radius=6)
                pygame.draw.rect(s,CYAN,(42,305,int(700*progress),14),border_radius=6)
        pygame.display.flip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera',type=int,default=0)
    parser.add_argument('--lateral',type=float,default=.65,help='Lateral threshold in torso lengths')
    parser.add_argument('--jump',type=float,default=.22,help='Jump threshold in torso lengths')
    parser.add_argument('--duck',type=float,default=.35,help='Duck threshold in torso lengths')
    args=parser.parse_args()
    if min(args.lateral,args.jump,args.duck)<=0:
        parser.error('Gesture thresholds must be positive')
    model=Path(__file__).resolve().parent/'models'/'pose_landmarker_lite.task'
    if not model.is_file():
        print('Model missing. Run: python download_model.py',file=sys.stderr)
        return 1
    from vision import Camera
    camera=None
    try:
        camera=Camera(args.camera,model)
        ui=Display()
        controls=Gestures(args.lateral,args.jump,args.duck)
        game=Runner()
        state='ready'
        clock=pygame.time.Clock()
        last=time.monotonic()
        resume_at=0.0
        was_tracked=False
        while True:
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    return 0
            body,frame=camera.read()
            now=time.monotonic()
            dt=min(.1,now-last)
            last=now
            cmd=controls.update(body,now)
            tracked=body is not None
            if tracked and not was_tracked:
                resume_at=now+1.0
            was_tracked=tracked
            if cmd.activate:
                if state=='ready' or state=='over':
                    game=Runner()
                    state='playing'
                    resume_at=now+1.5
                elif state=='playing':
                    state='paused'
                elif state=='paused':
                    state='playing'
                    resume_at=now+1.5
            message=''
            if controls.baseline is None:
                message='Stand still in the center for 2 seconds. Keep your full body visible.'
            elif not tracked:
                message='Tracking lost: paused. Step back until your body is visible.'
            elif state=='ready':
                message='Ready! Raise BOTH hands for 1.2 seconds to start.'
            elif state=='over':
                message=f'Game over! Score {game.score}. Raise both hands to play again.'
            elif state=='paused':
                message='Paused. Raise both hands again to resume.'
            elif now<resume_at:
                message='Get ready... lower your hands and return to center.'
            elif state=='playing':
                game.update(dt,cmd)
                if not game.alive:
                    state='over'
            gesture='LEFT' if cmd.move<0 else 'RIGHT' if cmd.move>0 else 'JUMP' if game.jump_left>0 else 'DUCK' if cmd.duck else 'CENTER'
            ui.draw(game,frame,message,controls.baseline is not None,controls.progress,gesture,bool(message))
            clock.tick(30)
    except (RuntimeError,ValueError,OSError) as exc:
        print(f'Cannot start/run Motion Runner: {exc}',file=sys.stderr)
        return 1
    finally:
        if camera is not None:
            camera.close()
        pygame.quit()

if __name__=='__main__':
    raise SystemExit(main())
