"""Run once with internet access. Gameplay itself is entirely offline."""
from pathlib import Path
import urllib.request
import os
URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'
TARGET = Path(__file__).resolve().parent / 'models' / 'pose_landmarker_lite.task'

def main():
    TARGET.parent.mkdir(exist_ok=True)
    if TARGET.exists():
        print(f'Model already exists: {TARGET}')
        return
    tmp = TARGET.with_suffix('.part')
    try:
        print('Downloading Google MediaPipe Pose Landmarker Lite model...')
        with urllib.request.urlopen(URL, timeout=90) as src, tmp.open('wb') as dst:
            while chunk := src.read(1024*1024):
                dst.write(chunk)
        if tmp.stat().st_size < 1000000:
            raise RuntimeError('Incomplete model download')
        os.replace(tmp, TARGET)
        print(f'Ready: {TARGET}')
    finally:
        tmp.unlink(missing_ok=True)

if __name__ == '__main__':
    main()
