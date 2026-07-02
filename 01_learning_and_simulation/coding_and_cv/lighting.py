"""AeroMed Phase 1.5 — lighting robustness (gap 3).

Indoor light is one condition; a real delivery happens in any of them.
Instead of flying, record ONE short webcam clip (or use any downloaded
footage with people in it) and re-run the identical detector over
programmatically altered copies: dusk, overexposure, flat overcast, hard
shadow. The output table shows exactly where detection degrades and what a
lower confidence threshold buys back.

What this demonstrates about tuning:
  conf  0.5 collapses first in bad light; ~0.25 is the outdoor starting
        point — but pair it with a minimum-box floor (altitude.py) and
        confirm-over-frames (mission.py) so false positives stay out.
  NMS   iou= matters for overlapping people in crowds, not for lighting —
        leave the 0.7 default alone.
  Real fix: fine-tuning with augmentation on drone footage — Phase 3.

Record:    .venv/bin/python lighting.py --record 10   (10 s webcam -> clip.mp4)
Test:      .venv/bin/python lighting.py clip.mp4
Selfcheck: .venv/bin/python lighting.py --selfcheck   (no camera/model needed)
"""
import argparse
import os
import sys
import time

import cv2
import numpy as np


def _gamma(frame, g):
    lut = ((np.arange(256) / 255.0) ** g * 255).astype(np.uint8)
    return cv2.LUT(frame, lut)


def _dusk(f):  # dark + cold colour cast (BGR: blue up, red down)
    return (_gamma(f, 2.4) * np.array([1.15, 1.0, 0.85])).clip(0, 255).astype(np.uint8)


def _shadow(f):  # hard shadow edge across the scene
    ramp = np.linspace(0.25, 1.0, f.shape[1], dtype=np.float32)
    return (f * ramp[None, :, None]).astype(np.uint8)


CONDITIONS = {
    "baseline": lambda f: f,
    "dusk": _dusk,
    "overexposed": lambda f: cv2.convertScaleAbs(f, alpha=1.7, beta=30),
    "overcast": lambda f: cv2.convertScaleAbs(f, alpha=0.55, beta=100),  # flat, low contrast
    "hard_shadow": _shadow,
}


def run(video, step=3):
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(video)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    cap.release()
    frames = frames[::step]
    if not frames:
        sys.exit(f"no frames in {video} — record one with: lighting.py --record 10")
    print(f"{len(frames)} frames x {len(CONDITIONS)} conditions "
          f"(detector runs once at conf=0.2; columns re-threshold the same results)\n")
    print(f"{'condition':<12} {'person@0.50':>12} {'person@0.25':>12} {'mean best conf':>15}")
    for name, fn in CONDITIONS.items():
        best = []
        for f in frames:
            boxes = model(fn(f), verbose=False, conf=0.2)[0].boxes
            best.append(max((float(b.conf[0]) for b in boxes if int(b.cls[0]) == 0), default=0.0))
        n = len(best)
        print(f"{name:<12} {sum(b >= 0.5 for b in best) / n:>11.0%} "
              f"{sum(b >= 0.25 for b in best) / n:>12.0%} {sum(best) / n:>15.2f}")
    print("\nIf @0.25 rescues dusk/shadow but @0.50 misses: that gap is your threshold")
    print("tuning. Anything still missed at 0.25 needs better data (Phase 3), not tuning.")


def record(seconds, out="clip.mp4"):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. System Settings > Privacy & Security > Camera.")
    ok, f = cap.read()
    if not ok:
        sys.exit("No frame from camera.")
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 20, (f.shape[1], f.shape[0]))
    print(f"recording {seconds} s — step back so your whole body is in frame, move around")
    t0, n = time.time(), 0
    while time.time() - t0 < seconds:
        ok, f = cap.read()
        if not ok:
            break
        vw.write(f)
        n += 1
    vw.release()
    cap.release()
    print(f"wrote {out} ({n} frames) — now run: .venv/bin/python lighting.py {out}")


def selfcheck():
    base = np.tile((np.arange(80) * 3).astype(np.uint8), (60, 1))
    f = np.stack([base] * 3, axis=-1)
    for name, fn in CONDITIONS.items():
        g = fn(f)
        assert g.shape == f.shape and g.dtype == np.uint8, name
    assert CONDITIONS["dusk"](f).mean() < f.mean()               # dusk darkens
    assert CONDITIONS["overexposed"](f).mean() > f.mean()        # overexposure brightens
    assert CONDITIONS["overcast"](f).std() < f.std()             # overcast flattens contrast
    s = CONDITIONS["hard_shadow"](f)
    assert s[:, :10].mean() < s[:, -10:].mean()                  # shadow side is darker
    print("selfcheck OK")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse local yolov8n.pt
    p = argparse.ArgumentParser()
    p.add_argument("video", nargs="?", help="video file to test (e.g. clip.mp4)")
    p.add_argument("--record", type=int, metavar="SECONDS")
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    if a.selfcheck:
        selfcheck()
    elif a.record:
        record(a.record)
    elif a.video:
        run(a.video)
    else:
        p.print_help()
