"""Local webcam pose inference using the MediaPipe Tasks API."""
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from controls import Body

EDGES = [(11,12),(11,23),(12,24),(23,24),(11,13),(13,15),
         (12,14),(14,16),(23,25),(24,26)]

def available_cameras(max_index=9):
    available = []
    for index in range(max_index + 1):
        capture = cv2.VideoCapture(index)
        if capture.isOpened():
            available.append(index)
        capture.release()
    return available

class Camera:
    def __init__(self, index, model):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.cap.release()
            raise RuntimeError('Cannot open camera. Close other camera apps, enable camera permission, or use --camera 1.')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        try:
            self.pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(model)),
                running_mode=vision.RunningMode.VIDEO,
                num_poses=1, min_pose_detection_confidence=.6,
                min_pose_presence_confidence=.6, min_tracking_confidence=.6))
        except Exception:
            self.cap.release()
            raise
        self.timestamp = -1

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return None, None
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.timestamp = max(self.timestamp+1, int(time.monotonic()*1000))
        result = self.pose.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), self.timestamp)
        body = None
        if result.pose_landmarks:
            lm = result.pose_landmarks[0]
            torso = [11,12,23,24]
            if all(lm[i].visibility > .55 and 0 < lm[i].x < 1 and 0 < lm[i].y < 1 for i in torso):
                sy = (lm[11].y+lm[12].y)/2
                hy = (lm[23].y+lm[24].y)/2
                hx = (lm[23].x+lm[24].x)/2
                knees_visible = all(lm[i].visibility > .55 and 0 < lm[i].x < 1 and 0 < lm[i].y < 1
                                    for i in [25,26])
                up = all(lm[i].visibility > .55 for i in [15,16]) and lm[15].y < sy-.08 and lm[16].y < sy-.08
                knee_y = (lm[25].y+lm[26].y)/2 if knees_visible else hy
                body = Body(hx, hy, sy, knee_y, max(.01,hy-sy), up, knees_visible)
            h,w = frame.shape[:2]
            for a,b in EDGES:
                if lm[a].visibility > .55 and lm[b].visibility > .55:
                    cv2.line(frame,(int(lm[a].x*w),int(lm[a].y*h)),
                             (int(lm[b].x*w),int(lm[b].y*h)),(80,240,140),2)
        return body, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def close(self):
        self.cap.release()
        self.pose.close()
