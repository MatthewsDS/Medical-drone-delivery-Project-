# AeroMed CV — Phase 1 (webcam detection + targeting)

Webcam stands in for the Pi camera. Detects a target class with pretrained YOLO,
locks onto the nearest one, prints a steering hint toward frame-center.
Design: `../../docs/superpowers/specs/2026-07-01-aeromed-cv-webcam-design.md`.

## Setup (once)
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run
```bash
.venv/bin/python detect.py                 # target = person
.venv/bin/python detect.py --target cup    # any YOLO class (person, cup, bottle, cell phone...)
.venv/bin/python detect.py --selfcheck     # test targeting math, no camera needed
```
Press `q` to quit the window.

**First run:** macOS asks for camera access → Allow (or System Settings > Privacy &
Security > Camera > enable your terminal). Black feed = permission denied.

## Later (on the Pi)
Change `cv2.VideoCapture(0)` to the Pi camera source. Detection + targeting logic unchanged.
