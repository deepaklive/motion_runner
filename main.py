"""Motion Runner: an original three-lane endless runner with body controls."""
import argparse
import math
from pathlib import Path
import sys
import time
import pygame
from controls import DEFAULT_LATERAL, Gestures
from engine import Runner

W,H = 1100,720
BG=(12,18,36)
WHITE=(231,240,255)
CYAN=(55,219,229)

class Display:
    def __init__(self, fullscreen=False, display=0):
        pygame.init()
        self.fullscreen = fullscreen
        self.display = display
        count = pygame.display.get_num_displays()
        if not 0 <= display < count:
            raise ValueError(f'Display {display} is unavailable. Detected {count} display(s); choose 0 to {count-1}.')
        self.window = pygame.display.set_mode((0,0) if fullscreen else (W,H), pygame.FULLSCREEN if fullscreen else 0, display=self.display)
        self.screen = pygame.Surface((W,H))
        self.full_button = pygame.Rect(825,645,170,30)
        self.exit_button = pygame.Rect(1005,645,75,30)
        pygame.display.set_caption('Motion Runner | Webcam controlled')
        self.font = pygame.font.Font(None,27)
        self.small = pygame.font.Font(None,20)
        self.big = pygame.font.Font(None,54)

    def handle_click(self, pos):
        width,height = self.window.get_size()
        scale = min(width/W,height/H)
        logical = ((pos[0]-(width-W*scale)/2)/scale,
                   (pos[1]-(height-H*scale)/2)/scale)
        if self.exit_button.collidepoint(logical):
            return True
        if self.full_button.collidepoint(logical):
            self.fullscreen = not self.fullscreen
            self.window = pygame.display.set_mode((0,0) if self.fullscreen else (W,H),
                                                  pygame.FULLSCREEN if self.fullscreen else 0, display=self.display)
        return False

    def text(self, s, pos, color=WHITE, big=False):
        self.screen.blit((self.big if big else self.font).render(s,True,color),pos)

    def point(self, lane, z):
        p = max(0,min(1.15,1-z))**1.65
        return (int(400+(lane-1)*(35+185*p)),int(175+480*p)), p

    def draw_coin(self, surface, x, y, size):
        radius=max(5,size//4)
        center=(x,y-max(4,radius))
        pygame.draw.ellipse(surface,(16,22,30),(x-radius,y-2,radius*2,6))
        pygame.draw.ellipse(surface,(150,92,24),(center[0]-radius,center[1]-radius+2,
                               radius*2,radius*2))
        pygame.draw.circle(surface,(255,185,35),center,radius)
        pygame.draw.circle(surface,(255,224,91),center,max(2,radius-2),max(1,radius//5))
        pygame.draw.arc(surface,(255,248,190),(center[0]-radius//2,center[1]-radius//2,
                                               radius,radius),.8,4.8,max(1,radius//6))
        pygame.draw.circle(surface,(255,250,204),(center[0]-radius//3,center[1]-radius//3),
                           max(1,radius//6))

    def draw_beam(self, surface, x, ground_y, width, p):
        height=max(20,int(105*p))
        beam_height=max(9,int(18*(.45+p)))
        left=x-width//2
        post_width=max(5,width//9)
        pygame.draw.ellipse(surface,(18,23,31),(left-post_width,ground_y-4,width+post_width*2,8))
        pygame.draw.rect(surface,(123,54,107),(left,ground_y-height,post_width,height))
        pygame.draw.rect(surface,(255,164,218),(left+post_width//3,ground_y-height,2,height))
        pygame.draw.rect(surface,(123,54,107),(left+width-post_width,ground_y-height,post_width,height))
        pygame.draw.rect(surface,(255,164,218),(left+width-post_width+post_width//3,
                                                  ground_y-height,2,height))
        pygame.draw.polygon(surface,(154,69,132),[(left,ground_y-height),
                           (left+width,ground_y-height),(left+width+max(2,width//14),
                           ground_y-height-beam_height//2),(left+max(2,width//14),
                           ground_y-height-beam_height//2)])
        pygame.draw.rect(surface,(211,101,174),(left,ground_y-height-beam_height,width,beam_height))
        pygame.draw.line(surface,(255,190,226),(left+3,ground_y-height-beam_height+2),
                         (left+width-3,ground_y-height-beam_height+2),max(1,int(p*2)))
        for post_x in (left,left+width-post_width):
            pygame.draw.rect(surface,(255,193,55),(post_x,ground_y-height+height//3,
                                                    post_width,max(2,int(3*p))))
            pygame.draw.rect(surface,(82,43,78),(post_x-2,ground_y-3,post_width+4,4))

    def draw_barrier(self, surface, x, ground_y, width, p):
        height=max(18,int(55*(.25+p)))
        depth=max(3,int(width*.12))
        left=x-width//2
        top=ground_y-height
        pygame.draw.ellipse(surface,(16,22,30),(left-depth,ground_y-4,width+depth*2,9))
        pygame.draw.polygon(surface,(151,66,37),[(left+width,top+3),(left+width+depth,top),
                           (left+width+depth,ground_y-depth),(left+width,ground_y)])
        pygame.draw.polygon(surface,(255,185,97),[(left,top+3),(left+depth,top),
                           (left+width+depth,top),(left+width,top+3)])
        front=pygame.Rect(left,top+3,width,height-3)
        pygame.draw.rect(surface,(224,94,45),front,border_radius=max(2,int(p*4)))
        stripe_h=max(2,int(6*p))
        for fraction in (.2,.5,.8):
            band_y=top+int(height*fraction)
            pygame.draw.rect(surface,(255,207,132),(left+2,band_y,width-4,stripe_h))
        pygame.draw.line(surface,(255,224,174),(left+3,top+5),(left+3,ground_y-3),max(1,int(p*2)))
        pygame.draw.line(surface,(125,52,36),(left+width-3,top+5),(left+width-3,ground_y-3),1)

    def draw_train(self, surface, x, ground_y, width, p):
        height=max(36,int(145*(.25+p)))
        depth=max(4,int(width*.13))
        left=x-width//2
        top=ground_y-height
        front=pygame.Rect(left,top,width,height)
        pygame.draw.ellipse(surface,(15,22,31),(left-depth,ground_y-4,width+depth*2,10))
        pygame.draw.polygon(surface,(28,61,94),[(left+width,top+5),(left+width+depth,top),
                           (left+width+depth,ground_y-depth),(left+width,ground_y)])
        pygame.draw.polygon(surface,(120,169,207),[(left+2,top+4),(left+depth,top),
                           (left+width+depth,top),(left+width,top+4)])
        pygame.draw.rect(surface,(47,112,169),front,border_radius=max(2,int(p*5)))
        pygame.draw.line(surface,(161,208,236),(left+3,top+6),(left+3,ground_y-5),max(1,int(p*2)))
        pygame.draw.line(surface,(25,60,94),(left+width-3,top+5),(left+width-3,ground_y-5),2)
        if width > 27 and height > 55:
            glass=pygame.Rect(left+max(4,width//7),top+max(8,height//9),
                              max(4,width*5//7),max(8,height//3))
            pygame.draw.rect(surface,(14,39,63),glass,border_radius=3)
            pygame.draw.rect(surface,(100,177,217),glass,2,border_radius=3)
            pygame.draw.line(surface,(158,215,240),(glass.left+3,glass.top+3),
                             (glass.right-4,glass.top+3),max(1,int(p*2)))
            pygame.draw.line(surface,(24,66,98),(x,glass.top),(x,glass.bottom),max(1,int(p*2)))
            grille_y=top+height*2//3
            pygame.draw.line(surface,(22,67,101),(left+width//7,grille_y),
                             (left+width*6//7,grille_y),max(2,int(p*3)))
            for light_x in (left+width//5,left+width*4//5):
                light_y=ground_y-max(8,int(height*.13))
                pygame.draw.circle(surface,(255,190,86),(light_x,light_y),max(2,int(3*p)))
                pygame.draw.circle(surface,(255,239,174),(light_x,light_y),max(1,int(p)))
            pygame.draw.line(surface,(177,205,221),(left+width//6,ground_y-4),
                             (left+width*5//6,ground_y-4),max(1,int(p*3)))

    def draw(self, game, frame, message, calibrated, progress, gesture, paused,
             baseline=None, lateral=DEFAULT_LATERAL):
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
                self.draw_coin(s,x,y,width)
            elif obj.kind=='beam':
                self.draw_beam(s,x,y,width,p)
            elif obj.kind=='train':
                self.draw_train(s,x,y,width,p)
            else:
                self.draw_barrier(s,x,y,width,p)
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
            if baseline is not None:
                preview=pygame.Rect(825,60,260,195)
                center_x=preview.left+round(baseline.waist_x*preview.width)
                threshold=round(lateral*max(.08,baseline.torso)*preview.width)
                left_x=max(preview.left,min(preview.right,center_x-threshold))
                right_x=max(preview.left,min(preview.right,center_x+threshold))
                band=pygame.Surface((max(1,right_x-left_x),preview.height),pygame.SRCALPHA)
                band.fill((55,219,229,28))
                s.blit(band,(left_x,preview.top))
                pygame.draw.line(s,(255,190,83),(left_x,preview.top),(left_x,preview.bottom),2)
                pygame.draw.line(s,(255,190,83),(right_x,preview.top),(right_x,preview.bottom),2)
                pygame.draw.line(s,CYAN,(center_x,preview.top),(center_x,preview.bottom),2)
                waist_y=preview.top+round(baseline.hip_y*preview.height)
                pygame.draw.line(s,WHITE,(left_x,waist_y),(right_x,waist_y),1)
                pygame.draw.circle(s,CYAN,(center_x,waist_y),4)
                pygame.draw.rect(s,WHITE,preview,1)
                pygame.draw.line(s,CYAN,(827,272),(845,272),3)
                s.blit(self.small.render('Waist center',True,WHITE),(850,263))
                pygame.draw.line(s,(255,190,83),(960,272),(978,272),3)
                s.blit(self.small.render('Shift limit',True,WHITE),(983,263))
        else:
            self.text('Camera unavailable',(830,120))
        self.text('BODY CONTROLS',(830,285),CYAN)
        for i,line in enumerate(['Jump: clear orange barriers','Bend: pass under pink beams','Shift waist left/right: lane','Blue trains: change lane','Gold coins: collect for points','','Return waist to center between','left/right movements.','','Both hands up for 1.2 sec:','start / restart / pause.']):
            self.text(line,(825,325+i*25))
        self.text(f'Action: {gesture}',(825,610),CYAN)
        for rect in [self.full_button,self.exit_button]:
            pygame.draw.rect(s,(40,65,87),rect,border_radius=6)
        self.text('Windowed' if self.fullscreen else 'Full screen',(835,650))
        self.text('Exit',(1020,650))
        self.text('All camera processing is local',(825,680))
        if message:
            panel=pygame.Surface((750,110),pygame.SRCALPHA)
            panel.fill((9,16,31,225))
            s.blit(panel,(25,245))
            self.text(message,(42,263),WHITE)
            if not calibrated:
                pygame.draw.rect(s,(40,60,78),(42,305,700,14),border_radius=6)
                pygame.draw.rect(s,CYAN,(42,305,int(700*progress),14),border_radius=6)
        width,height = self.window.get_size()
        scale = min(width/W,height/H)
        size = (round(W*scale),round(H*scale))
        self.window.fill(BG)
        self.window.blit(pygame.transform.smoothscale(s,size),
                         ((width-size[0])//2,(height-size[1])//2))
        pygame.display.flip()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera',type=int,default=0,help='Camera index (use --list-cameras to see available indices)')
    parser.add_argument('--list-cameras',action='store_true',help='List available camera indices and exit')
    parser.add_argument('--fullscreen',action='store_true',help='Start in fullscreen mode')
    parser.add_argument('--display',type=int,default=0,help='Monitor index: 0 for first, 1 for second')
    parser.add_argument('--lateral',type=float,default=DEFAULT_LATERAL,help='Lateral threshold in torso lengths')
    parser.add_argument('--jump',type=float,default=.22,help='Jump threshold in torso lengths')
    parser.add_argument('--duck',type=float,default=.35,help='Duck threshold in torso lengths')
    args=parser.parse_args()
    if min(args.lateral,args.jump,args.duck)<=0:
        parser.error('Gesture thresholds must be positive')
    if args.list_cameras:
        from vision import available_cameras
        cameras=available_cameras()
        if cameras:
            print('Available cameras: '+', '.join(str(index) for index in cameras))
            print('Select one with: python main.py --camera INDEX')
        else:
            print('No cameras detected. Check camera permissions and connections.')
        return 0
    model=Path(__file__).resolve().parent/'models'/'pose_landmarker_lite.task'
    if not model.is_file():
        print('Model missing. Run: python download_model.py',file=sys.stderr)
        return 1
    from vision import Camera
    camera=None
    music_loaded=False
    try:
        camera=Camera(args.camera,model)
        ui=Display(args.fullscreen,args.display)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(Path(__file__).resolve().parent/'sound'/'theme.mp3'))
            music_loaded=True
        except pygame.error as exc:
            print(f'Audio unavailable; continuing without music: {exc}',file=sys.stderr)
        controls=Gestures(args.lateral,args.jump,args.duck)
        game=Runner()
        state='ready'
        music_playing=False
        clock=pygame.time.Clock()
        last=time.monotonic()
        resume_at=0.0
        was_tracked=False
        while True:
            for event in pygame.event.get():
                if event.type==pygame.QUIT or (event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and ui.handle_click(event.pos)):
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
                message='Stand still in the center for 2 seconds. Keep shoulders through knees visible.'
            elif not tracked:
                message='Tracking lost: paused. Keep shoulders through knees visible.'
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
            should_play_music=state=='playing' and now>=resume_at and tracked
            if music_loaded and should_play_music != music_playing:
                if should_play_music:
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.stop()
                music_playing=should_play_music
            gesture='LEFT' if cmd.move<0 else 'RIGHT' if cmd.move>0 else 'JUMP' if game.jump_left>0 else 'DUCK' if cmd.duck else 'CENTER'
            ui.draw(game,frame,message,controls.baseline is not None,controls.progress,gesture,bool(message),
                    controls.baseline,controls.lateral)
            clock.tick(30)
    except (RuntimeError,ValueError,OSError) as exc:
        print(f'Cannot start/run Motion Runner: {exc}',file=sys.stderr)
        return 1
    finally:
        if music_loaded:
            pygame.mixer.music.stop()
        if camera is not None:
            camera.close()
        pygame.quit()

if __name__=='__main__':
    raise SystemExit(main())
