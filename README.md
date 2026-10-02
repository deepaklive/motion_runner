# Motion Runner

An original Python endless runner inspired by the three-lane genre. Play with your body using a webcam: no keyboard or controller during gameplay. Graphics are drawn procedurally; no Subway Surfers assets are used.

## Requirements

- Python 3.11 or 3.12, preferably 64-bit. A webcam and desktop display.
- Windows or Linux. Start with a 640 x 480 camera image and good room lighting.
- Stand far enough away that shoulders, hips, and feet remain in view, including when you jump. Keep the camera stationary and leave clear space around you.
- CPU inference is used; a dedicated GPU is not required. Actual speed and detection accuracy depend on your computer and lighting.

## Setup (Windows PowerShell)

Extract the ZIP, open a terminal in the `motion_runner` folder, then run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_model.py
.\.venv\Scripts\python.exe main.py
```

## Setup (Linux)

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python download_model.py
.venv/bin/python main.py
```

Internet is needed once for packages and the approximately 6 MB Google pose model. The downloader writes `models/pose_landmarker_lite.task`. Gameplay does not make network requests, upload video, or record frames. If the download is blocked, download the model at the URL in `download_model.py` on another machine and copy it into `models/`.

## How to play

1. Stand upright in the center with hands down. Hold still for two seconds to calibrate. Your feet must be visible.
2. Raise both hands above your shoulders for 1.2 seconds to start, then lower them. A short countdown gives you time to get ready.
3. Use these body movements:

| Movement | Game action |
| --- | --- |
| Jump upward | Jump over orange barriers |
| Bend down or squat | Duck beneath pink overhead beams |
| Hop or step left | Move one lane left |
| Hop or step right | Move one lane right |
| Jump diagonally | Jump and change lane together |
| Raise both hands for 1.2 seconds | Pause, resume, or restart after game over |

The camera preview is mirrored: movement to your left moves the runner left. Return to your original standing center between repeated sideways movements to rearm the lane gesture. This is relative movement control, not absolute screen-position lane selection. Holding a crouch keeps the runner ducking; each detected takeoff creates a 0.95-second game jump. Jump detection checks that both hips and feet rise, rather than treating recovery from a squat as a jump.

Avoid blue trains by changing lane. Gold coins add 25 points. Speed increases gradually. Losing body tracking freezes the simulation; restoring tracking adds a one-second grace period. Calibration is kept across restarts; close and reopen the game to recalibrate after moving the camera.

There are no keyboard gameplay bindings. Close the window using its close button to exit. Setup commands and window closing are outside gameplay.

## Tune the controls

```bash
python main.py --camera 1
python main.py --lateral 0.5 --jump 0.18 --duck 0.3
```

Thresholds are fractions of your calibrated torso height. Smaller values make detection more sensitive but can cause accidental actions. Defaults: lateral 0.65, jump 0.22, duck 0.35.

## Troubleshooting

- **Camera cannot open:** close video calls and other camera applications; allow desktop camera access in your OS settings; try `--camera 1`.
- **Calibration never completes:** ensure ankles, hips, and shoulders are visible; improve lighting; stay upright with hands down and stop moving for two seconds.
- **Missed jumps:** move farther from the camera so feet stay visible; lower `--jump` a little. The webcam estimates motion; it does not measure physical height precisely.
- **Duck not detected:** bend your upper body down further or lower `--duck`.
- **Repeated sideways hops do nothing:** return to the calibrated center before the next hop.
- **Slow video:** close background applications; use a well-lit scene. Inference and drawing are synchronous, targeting at most 30 FPS.
- **Linux GUI/OpenGL errors:** install your distribution's OpenGL and desktop GUI runtime packages (on Ubuntu/Debian, `sudo apt install libgles2 libegl1 libgl1`); this game needs a desktop session and cannot use a headless OpenCV installation.
- **Model error:** delete a damaged `.task` file and run the downloader again.

## Project structure

- `main.py`: window, graphics, game states, and camera integration.
- `vision.py`: OpenCV capture, local MediaPipe Tasks inference, skeleton preview.
- `controls.py`: calibration, smoothing, gesture thresholds, and gesture rearming.
- `engine.py`: obstacles, collision rules, scoring, speed progression.
- `download_model.py`: one-time model setup.
- `tests/test_game.py`: synthetic gesture and simulation regression checks.

Run tests from this folder:

```bash
python -m unittest discover -s tests -v
```

This is a playable MVP with stylized perspective graphics, not a full commercial 3D game. Single-person tracking only. Camera gestures are heuristic and may need tuning for your room. No external API calls are used during play.

## Validation

All 11 pure logic tests pass, Python compilation passes, and a headless Pygame renderer smoke test passes in the build environment (Python 3.12, Linux). Packages installed successfully and the model downloaded successfully. MediaPipe inference could not be exercised here because the environment lacks `libGLESv2.so.2`; live pose recognition remains unverified. Dependency versions are pinned to the installed versions. A live camera/end-to-end test must be performed on your own machine; synthetic landmark tests cannot establish real-world recognition accuracy.

## References and third-party licenses

MediaPipe Tasks API: https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/PoseLandmarker
Google pose guide and model assets: https://ai.google.dev/edge/mediapipe/solutions/pose_landmarker
Pygame: https://www.pygame.org/docs/
OpenCV: https://docs.opencv.org/

Dependencies and the downloaded model remain subject to their own licenses. This archive contains original project source, not the dependency packages or Google model.
