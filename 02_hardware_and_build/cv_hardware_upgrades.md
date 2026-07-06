# CV Hardware Upgrades — Procurement Notes

**Date:** 2026-07-06 · **Owner:** Matthews · **For:** hardware-procurement phase
Research for making the vision system better than the Pi-5-CPU baseline
(~5–10 fps YOLOv8n, 80 fixed COCO classes). UK prices, VAT-in, mid-2026.

## The key distinction (read first)

Hardware changes **speed**; the **model** changes *what* it can recognise.
- AI accelerator → run a bigger/faster model, same or more classes, real-time.
- To recognise more than YOLO's 80 classes you need **YOLO-World**
  (open-vocabulary, already wired into `target_chat.py` as "AI search"), and
  YOLO-World only becomes real-time *with* an accelerator. That's the real
  reason to buy the AI HAT+.
- Landing beacons don't affect object detection at all — landing only.

## Buy (best value first)

| # | Item | ~GBP | fps effect | Improves |
|---|------|------|-----------|----------|
| 1 | **Pi AI HAT+ 13 TOPS (Hailo-8L)** | £70 | 5–10 → **20–30+** (YOLOv8s), unlocks YOLO-World live | frame rate + open-vocabulary |
| 2 | **Global Shutter Camera (IMX296)** + lens | £50 + £25 | — | kills motion-blur/jello in flight |
| 3 | **IR-LOCK beacon + sensor** | £130–160 | — | cm-accurate precision landing |

- **#1 is the single best upgrade.** Bolts onto the Pi 5 we already have; no
  new computer. Bigger model = more reliable, longer-range detection of the
  same classes; also makes the "type any phrase" AI search usable in flight.
  26 TOPS (Hailo-8) ~£110 if headroom wanted — 13 TOPS is enough for one camera.
- **#2**: drones vibrate; rolling shutter smears fast motion. Camera Module 3
  (£25) is fine for first flights — upgrade to global shutter once vibration bites.
- **#3**: plugs into Cube Orange+ over **I2C, zero Pi load**, ArduPilot-native
  (PLND_ENABLED/PLND_TYPE), works in all light. Best "impressive + reliable"
  spend for the delivery demo.

## Consider (pick one, not both with #1)

- **Luxonis OAK-D Lite ~£130** — depth AI camera, runs detection on-camera
  (4 TOPS) + 3D distance; used on real ArduPilot drones for person-tracking.
  Overlaps the AI HAT+. Choose AI HAT+ (cheaper, faster inference) *or* OAK-D
  (adds depth). AI HAT+ is the better first buy.

## Skip

- **Jetson Orin Nano Super ~£250** — runs YOLO 30–60 fps and could do
  open-vocab live, but *replaces* the Pi 5, needs own power/cooling/reflash,
  heavier, and a real user got **2 fps on a 5 MP stream at 15 W**. The £70 AI
  HAT+ gets ~80% of the benefit at ⅓ cost/weight. Revisit only if live
  open-vocabulary *in flight* becomes a hard requirement.
- **Gimbal for CV** — global shutter fixes blur more cheaply. Add later for
  video polish, not detection.

## Recommendation

**AI HAT+ (£70) + IR-LOCK (£150) first — ~£220.** Upgrades the two things a
laptop can never fake: real-time speed (which also unlocks open-vocabulary)
and precision landing. Camera upgrade when flight testing starts.

## Sources
- Pi AI HAT+ YOLOv8 benchmark — https://wiki.seeedstudio.com/benchmark_on_rpi5_and_cm4_running_yolov8s_with_rpi_ai_kit/
- Jeff Geerling, Pi AI Kit 13 TOPS — https://www.jeffgeerling.com/blog/2024/testing-raspberry-pis-ai-kit-13-tops-70/
- Jetson Orin Nano Super — https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/
- Global Shutter Camera — https://www.raspberrypi.com/products/raspberry-pi-global-shutter-camera/
- Luxonis OAK-D Lite — https://shop.luxonis.com/products/oak-d-lite-1
- IR-LOCK precision landing (ArduPilot) — https://ardupilot.org/copter/docs/precision-landing-irlock.html
