# AeroMed CV — Phase 1 Webcam Detection & Targeting (Design)

**Date:** 2026-07-01
**Owner:** Jean-Paul (CV lead), Matthews (review)
**Status:** Design — awaiting Matthews' review before implementation
**Location in repo:** `01_learning_and_simulation/coding_and_cv/`

---

## 1. Context

Per the vault ([[05-Computer-Vision-and-Targeting]]), the project is in **Phase 1: webcam-only OpenCV object detection on a laptop — no drone hardware**. A MacBook webcam stands in for the Pi Camera. OpenCV's `VideoCapture` is the *same API* for both, so a webcam-first build is thrown away when we move to the Pi — only the capture source (`0` → Pi camera) changes.

## 2. Goal & Scope

**Goal:** A running program that opens the webcam, detects a chosen target class with a pretrained YOLO model, locks onto the nearest instance, and outputs a steering hint toward frame-center — the seed of the real CV→flight-control handoff.

**In scope (Phase 1):**
- Live webcam capture.
- Pretrained YOLO (`yolov8n`) detection — no training.
- Configurable target class (default `person`).
- Nearest-target selection (largest bounding box).
- Targeting: pixel offset of target-center from frame-center + a plain steering hint (`LEFT / RIGHT / UP / DOWN / CENTERED`).
- On-screen overlay (box, label, offset, hint) and console print.

**Explicitly deferred (NOT built now — YAGNI until hardware/later phases):**
- YOLO/CNN training or fine-tuning — pretrained COCO model is enough.
- Camera calibration / distortion correction — only matters for real-world angle mapping on the Pi.
- ArUco precision-landing markers — Phase 2, needs the drone.
- Frame-capture threading — only matters when a slow CV loop could block a *flight-control* loop, which does not exist on a laptop.
- Building/address detection — not testable on an indoor webcam.
- Actual flight-control handoff (triggering descent) — coordinated later with [[06-GPS-Navigation-and-Flight-Control]]; Phase 1 only *produces* the steering signal.

## 3. Approach (decided)

- **Output = detection + targeting** (not detection alone). The offset/steering hint is the piece that maps to guiding the drone, and it's ~10 lines over plain detection.
- **Target = configurable class**, default `person`. YOLO's default 80-class COCO model already covers person/cup/bottle/cell phone, so testing doesn't require standing on camera.
- **Multiple matches → largest box wins** (largest ≈ nearest ≈ the delivery target).
- **Model = `yolov8n` (nano):** smallest, real-time on CPU / Apple-Silicon MPS. No reason for a heavier model for a webcam test.

## 4. Architecture

One file. The pipeline is genuinely small; splitting it would be premature.

```
01_learning_and_simulation/coding_and_cv/
├── detect.py          # webcam → YOLO → nearest target → steering hint → overlay
├── requirements.txt   # ultralytics, opencv-python
├── README.md          # run instructions + macOS camera-permission note
└── .venv/             # local virtualenv (gitignored)
```

**`detect.py` has three parts:**

1. **`steering_hint(box, frame_w, frame_h, deadzone=0.15)` — pure function.**
   Input: a bounding box `(x1, y1, x2, y2)` and frame size. Output: `(dx, dy, hint)` where `dx`/`dy` are the target-center offset from frame-center in pixels (sign = direction) and `hint` is a human-readable string. `deadzone` = fraction of frame treated as "centered" so it doesn't jitter. **No camera or model needed to test this** — it's plain arithmetic.

2. **`nearest(detections)` helper.** Picks the largest-area box among detections of the target class. Returns `None` if none.

3. **`main()` loop.** Open `VideoCapture(0)` → read frame → `model(frame)` → filter to target class → `nearest()` → `steering_hint()` → draw overlay + print → show window. `q` quits. Releases the camera on exit.

## 5. Data flow

```
webcam frame ─▶ YOLO inference ─▶ [boxes of target class] ─▶ nearest() ─▶ box
                                                                    │
                                                    steering_hint(box, w, h)
                                                                    │
                                          (dx, dy, "MOVE LEFT / DESCEND / CENTERED")
                                                                    │
                                              overlay on frame  +  print to console
```

## 6. Error handling

- **Camera won't open** (`VideoCapture(0)` fails / returns no frames): print a clear message pointing at macOS camera permission, exit non-zero. This is the #1 first-run failure.
- **No target in frame:** overlay shows `no target`; no crash, loop continues.
- **Model download:** `ultralytics` auto-downloads `yolov8n.pt` on first run (needs internet once). Note this in the README.

## 7. Testing (ponytail: one runnable check)

`detect.py` includes a `--selfcheck` / `__main__` assert block that exercises `steering_hint()` with known boxes:
- Box centered → hint `CENTERED`, `dx≈0`, `dy≈0`.
- Box in top-left quadrant → hint contains `LEFT` and `UP`, `dx<0`, `dy<0`.
- Box in bottom-right → hint contains `RIGHT` and `DOWN`.

Runs with no camera and no model — pure logic. If the targeting math breaks, this fails loudly. No test framework, no fixtures.

## 8. Setup (what Matthews installs / does)

Machine already has: Python 3.9.6, git. No Homebrew / pyenv / conda needed.

```bash
cd 01_learning_and_simulation/coding_and_cv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # pulls ultralytics + torch (~a few hundred MB, one time)
.venv/bin/python detect.py                       # yolov8n.pt auto-downloads on first run
```

**macOS camera permission (one-time, manual — cannot be automated by Claude):**
First run triggers an OS prompt → **Allow**. If missed: *System Settings → Privacy & Security → Camera →* enable your terminal app (Terminal / iTerm). Without this, frames come back black.

## 9. Reuse note (Phase 1 → hardware)

Moving to the Pi later changes exactly one thing: `VideoCapture(0)` → the Pi camera source. `steering_hint()` and the detection logic are unchanged. That's the whole point of building webcam-first.
