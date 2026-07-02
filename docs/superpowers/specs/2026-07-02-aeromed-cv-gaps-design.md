# AeroMed CV — Phase 1.5: Closing the Six Detection Gaps (Design)

**Date:** 2026-07-02
**Owner:** Jean-Paul (CV lead), Matthews (review)
**Status:** Approved for implementation (Matthews pre-authorised autonomous build)
**Location in repo:** `01_learning_and_simulation/coding_and_cv/`
**Builds on:** [2026-07-01 webcam detection design](2026-07-01-aeromed-cv-webcam-design.md) — `detect.py` stays untouched; new modules import its helpers.

---

## 1. Goal

Extend the Phase 1 pipeline (webcam → YOLO → steering hint) toward what precision
landing actually needs: distinguish a *waving* person from a bystander, stay reliable
at altitude and in variable light, fall back to ArUco markers, not drop frames on the
Pi 5, and hand detections to a landing decision state machine. Everything testable on
the MacBook webcam **today**; hardware-only validation is flagged per module.

## 2. Approach decisions (with rejected alternatives)

| Gap | Chosen | Rejected & why |
|---|---|---|
| 1. Waving | **YOLOv8n-pose keypoints**: wrist above shoulder + wrist-x oscillation (≥3 direction reversals in a 2s window, amplitude scaled by shoulder width) | MediaPipe (new dependency, Python-version friction on Pi); optical flow in the person box (noisier, can't tell wave from walk — kept as documented fallback for extreme altitude where keypoints die) |
| 2. Altitude | **Digital altitude simulator**: shrink the live frame onto a full-size canvas so a person becomes a 20–60 px blob, then sweep `imgsz`/`conf`/min-box settings and print where detection dies | Buying a drone-view dataset pipeline now (VisDrone/SAHI tiling is the real Phase 3 fix — documented, not built) |
| 3. Lighting | **Offline robustness harness**: run the model over a recorded clip × lighting transforms (dark/bright/overcast/dusk/shadow), print detection-rate table | Flying to collect footage (can't yet); training augmentation (we don't train in Phase 1) |
| 4. Marked address | **cv2.aruco (built into OpenCV 4.13)**: marker generator + detector + solvePnP(IPPE_SQUARE) pose → distance + lateral offset | AprilTag lib (extra dependency, no gain at our scale); QR codes (no pose, poor range) |
| 5. Frame rate | **Latest-frame capture thread** (`VideoStream` class) + a benchmark showing naive vs threaded lag under simulated Pi-speed inference | multiprocessing (overkill, IPC cost); GStreamer pipelines (Phase 3, Pi-specific) |
| 6. Handoff | **Pure-Python landing FSM** (SEARCH→CONFIRM→ALIGN→DESCEND→LAND/ABORT) consuming detection events, emitting velocity-style commands; `--live` demo wires webcam+wave+ArUco into it | Full MAVLink/DroneKit integration (needs SITL wiring — separate workstream) |

**Zero new dependencies.** `ultralytics` already ships pose models (`yolov8n-pose.pt`
auto-downloads once, ~6 MB); `opencv-python` 4.13 includes ArUco. `requirements.txt` unchanged.

Prior art followed: Ultralytics pose-keypoint gesture examples (wave = shoulders/elbows/wrists),
[goodrobots/vision_landing](https://github.com/goodrobots/vision_landing) (ArUco lock at 32 m),
[GSNCodes ArUco pose estimation](https://github.com/GSNCodes/ArUCo-Markers-Pose-Estimation-Generation-Python).

## 3. Architecture

One file per gap — each is a lesson Jean-Paul can read top-to-bottom, and each runs
standalone on the webcam. Shared logic is imported, never copied.

```
coding_and_cv/
├── detect.py          # (existing, unchanged) steering_hint / nearest reused everywhere
├── stream.py          # (existing, unchanged)
├── wave.py            # 1. pose keypoints → WaveDetector (pure class) → overlay
├── altitude.py        # 2. altitude simulator + ground-sampling maths + settings sweep
├── lighting.py        # 3. record/load clip → transforms → detection-rate table
├── aruco_landing.py   # 4. marker generator + detection + pose (distance, offset)
├── camera.py          # 5. VideoStream thread + naive-vs-threaded FPS benchmark
├── mission.py         # 6. LandingFSM (pure) + --live integration demo
├── README.md          # rewritten: per-module lesson + hardware-validation flags
└── requirements.txt   # unchanged
```

Data flow at the end state (`mission.py --live`):

```
VideoStream (thread, latest frame only)
      │
      ├─ yolov8n-pose ─▶ WaveDetector ─▶ Detection(kind=WAVE, offset, conf)
      └─ cv2.aruco    ─▶ pose solve   ─▶ Detection(kind=MARKER, offset, dist)
                                │
                        LandingFSM.step(detection)
                                │
                 state + command string (what MAVLink would get)
```

## 4. Testing (ponytail: one runnable check per module)

Every module has `--selfcheck` needing **no camera and no model**:
- `wave.py` — synthetic sine-wave wrist track ⇒ wave; static wrist ⇒ no wave.
- `altitude.py` — person-height-in-pixels maths is monotonic and matches known values.
- `lighting.py` — each transform keeps shape/dtype and moves mean brightness the right way.
- `aruco_landing.py` — generates a marker in memory, detects it, recovers pose (closed loop).
- `camera.py` — stub capture proves `.read()` returns the *latest* frame, not a stale queue.
- `mission.py` — scripted event sequences assert every state transition incl. target-lost abort.

## 5. Hardware-validation flags (honest list)

Testable now: all logic, thresholds, state transitions, ArUco pose maths, threading pattern.
Needs Pi 5: real FPS numbers (Mac is ~10× faster), thermal throttling, camera driver.
Needs real camera: lens calibration matrix (webcam intrinsics are guessed — pose distance is ±10-20% until calibrated with a chessboard on the actual Pi cam).
Needs drone: vibration blur, downwash on subjects, true 10–50 m scale imagery, GPS+CV fusion.

## 6. Error handling

Camera-open failure → same clear macOS-permission message as `detect.py`. Missing video
file in `lighting.py` → offers `--record`. Keypoints below confidence → treated as
person-not-assessable, never a crash. FSM: unknown/no detection is a first-class event
(drives target-lost timeouts), not an error.
