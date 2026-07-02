# AeroMed CV — Phase 1 → 1.5 (webcam pipeline for precision landing)

Webcam stands in for the Pi camera; everything here runs on the MacBook today
and moves to the Pi 5 with a one-line capture change later.
Designs: [Phase 1](../../docs/superpowers/specs/2026-07-01-aeromed-cv-webcam-design.md) ·
[Phase 1.5](../../docs/superpowers/specs/2026-07-02-aeromed-cv-gaps-design.md)

## Setup (once)
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
No new dependencies since Phase 1 — pose models come with ultralytics, ArUco
with OpenCV. Models (`yolov8n.pt`, `yolov8n-pose.pt`) auto-download on first
run (internet needed once). Press `q` to quit any window.

**First run:** macOS asks for camera access → Allow (System Settings > Privacy
& Security > Camera > your terminal). Black feed = permission denied.

## The modules — in teaching order

| # | File | Gap it closes | Try it |
|---|------|--------------|--------|
| 0 | `detect.py` | detection + steering hint (Phase 1) | `.venv/bin/python detect.py` |
| 1 | `waving.py` | waving person vs bystander | `.venv/bin/python waving.py` |
| 2 | `camera.py` | capture vs inference threading | `.venv/bin/python camera.py --bench` |
| 3 | `aruco_landing.py` | marked-address landing target | `--make-marker`, then run it |
| 4 | `altitude.py` | small targets from 10–50 m | `.venv/bin/python altitude.py --sweep` |
| 5 | `lighting.py` | robustness across light | `--record 10`, then `lighting.py clip.mp4` |
| 6 | `mission.py` | CV → landing decision handoff | `.venv/bin/python mission.py --live` |

**Every module runs `--selfcheck` with no camera and no model** — that's the
five-minute health check after any edit: 
`for f in detect waving camera aruco_landing altitude lighting mission; do .venv/bin/python $f.py --selfcheck; done`

## The lesson in each (the 2-minute version for teaching)

**1. Waving (`waving.py`)** — YOLO can't see verbs, only nouns. So we get 17
body keypoints per person from `yolov8n-pose` and define the verb ourselves:
wrist above shoulder AND swinging side-to-side (≥2 direction changes in 2 s,
travel measured in shoulder-widths so it works at any distance; brief keypoint
dropouts from motion blur are tolerated, not reset). Raised-only =
someone holding a phone; motion-only = someone walking. Both together = a wave.

**2. Threading (`camera.py`)** — the camera produces frames faster than the Pi
can run YOLO, and OpenCV queues the extras. A naive loop therefore processes
the *past*. One background thread keeps only the newest frame; inference
always starts from *now*. This is the difference between landing on the
target and landing where the target was two seconds ago.

**3. ArUco (`aruco_landing.py`)** — a person detector guesses; a marker
*measures*. Because the printed size is known, one detection returns distance
and offset in metres, with near-zero false positives, proven from 32 m up in
other drone projects. **Decision rule: if someone can place a marker at the
delivery point, the marker is the primary system and person detection is the
fallback.** Person detection is for unprepared sites only.

**4. Altitude (`altitude.py`)** — a person at 30 m is ~80 px at 1080p; YOLO's
default 640-px input shrinks that to ~27 px and loses it. Fixes in order of
power: raise `imgsz` (costs fps), lower `conf` to ~0.15–0.25 (needs the
min-box-size floor to block noise), bigger model (decide on the Pi, not the
Mac). Verified here: at simulated 30 m the person scores 0.28 — invisible at
the stock conf 0.5, caught at 0.25.

**5. Lighting (`lighting.py`)** — record one clip, test five lighting worlds
for free. The table shows which conditions only *lower confidence* (fix =
threshold tuning) versus which *kill detection* (fix = better training data,
Phase 3 — no threshold rescues what the model never saw).

**6. Mission (`mission.py`)** — detection is an opinion 30×/s; landing is a
decision over time. `SEARCH → CONFIRM (1 s of waving) → ALIGN → DESCEND →
LAND`, marker skips CONFIRM, losing the target mid-descent → `ABORT` (climb,
go around). Non-waving people never advance the mission. The CONFIRM state is
also our false-positive filter: one bad frame can't trigger a landing.
Flight integration later swaps the printed command for a MAVLink call —
nothing else changes.

## What a laptop cannot validate (honest list)

- **Real fps on the Pi 5** — the Mac is ~10× faster; all thresholds that
  depend on frame *counts* (CONFIRM_FRAMES, LOST_FRAMES) get re-tuned there.
- **Camera intrinsics** — ArUco distances are ±10–20 % until the actual Pi
  camera is chessboard-calibrated (Phase 3).
- **True altitude imagery** — the simulator shrinks pixels; it can't create
  the motion blur, haze, and top-down foreshortening of real flight. First
  real flights must re-run the altitude + lighting numbers.
- **Vibration & downwash** — gimbal and prop-wash effects on both camera and
  the waving person. Hardware phase only.

## Later (on the Pi)
`cv2.VideoCapture(0)` → Pi camera source, wrap it in `camera.VideoStream`,
re-tune the frame-count constants. Detection, wave logic, ArUco maths and the
mission FSM move over unchanged.
