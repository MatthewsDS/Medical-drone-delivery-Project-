"""AeroMed Phase 1.5 — altitude & scale (gap 2).

At desk distance a person fills the frame; from a drone at 30 m they are a
~80-pixel blob at 1080p — and YOLO-nano at its default 640-px input misses
them, because 80 px at 1080p becomes ~27 px after downscaling. This module:

  1. the maths — person_px(): pixels a person occupies from a given altitude,
  2. a fake-altitude view — shrinks the live frame onto a full-size flat
     canvas, so the detector sees exactly the blob it would see from the sky,
  3. a settings sweep — which knobs keep small targets alive:
       imgsz  inference resolution: THE big one for small objects
       conf   small objects legitimately score lower; drop to ~0.15-0.25 but
              pair it with a minimum-box floor so noise doesn't sneak in
       model  yolov8s/m see smaller objects at fps cost — decide on the Pi

Run:       .venv/bin/python altitude.py             (w = climb, s = descend)
           .venv/bin/python altitude.py --imgsz 640 --conf 0.5   (stock settings — watch them fail)
Sweep:     .venv/bin/python altitude.py --sweep     (one frame, full settings grid)
Selfcheck: .venv/bin/python altitude.py --selfcheck (no camera/model needed)
"""
import argparse
import math
import os
import sys

import cv2
import numpy as np

PI_CAM_VFOV = 41.0  # degrees — Pi Camera Module 3 vertical field of view
MIN_BOX_PX = 8      # detections shorter than this are noise, not a landable target
ALTS = (5, 10, 20, 30, 40, 50)
SETTINGS = ((640, 0.5), (640, 0.25), (1280, 0.25), (1280, 0.15))  # (imgsz, conf)


def person_px(alt_m, frame_h=1080, vfov_deg=PI_CAM_VFOV, person_m=1.7):
    """Pixel height of a standing person seen from alt_m away (side-on view;
    straight-down foreshortening makes it smaller still)."""
    focal_px = frame_h / (2 * math.tan(math.radians(vfov_deg) / 2))
    return person_m * focal_px / alt_m


def fake_altitude(frame, alt_m, base_m=1.5):
    """Shrink the frame as if the camera backed off from base_m to alt_m,
    centred on a featureless canvas. Apparent size falls as base_m/alt_m."""
    h, w = frame.shape[:2]
    s = min(1.0, base_m / alt_m)
    small = cv2.resize(frame, (max(1, int(w * s)), max(1, int(h * s))))
    canvas = np.full_like(frame, 128)
    y, x = (h - small.shape[0]) // 2, (w - small.shape[1]) // 2
    canvas[y:y + small.shape[0], x:x + small.shape[1]] = small
    return canvas


def _person_boxes(model, frame, imgsz, conf):
    """Person boxes taller than the noise floor, with confidences."""
    out = []
    for b in model(frame, imgsz=imgsz, conf=conf, verbose=False)[0].boxes:
        x1, y1, x2, y2 = map(int, b.xyxy[0])
        if int(b.cls[0]) == 0 and (y2 - y1) >= MIN_BOX_PX:
            out.append(((x1, y1, x2, y2), float(b.conf[0])))
    return out


def _open_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. System Settings > Privacy & Security > Camera.")
    return cap


def sweep():
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    cap = _open_camera()
    for _ in range(5):  # warm-up frames while exposure settles
        ok, frame = cap.read()
    cap.release()
    if not ok:
        sys.exit("No frame from camera.")
    print("stand back so your whole body is in frame for a fair test\n")
    cols = [f"{i}/{c}" for i, c in SETTINGS]
    print(f"{'alt':>4} {'Pi-px':>6} " + " ".join(f"{c:>9}" for c in cols))
    for alt in ALTS:
        canvas = fake_altitude(frame, alt)
        row = []
        for imgsz, conf in SETTINGS:
            hits = _person_boxes(model, canvas, imgsz, conf)
            row.append(f"{max(c for _, c in hits):9.2f}" if hits else f"{'miss':>9}")
        print(f"{alt:>3}m {person_px(alt):>5.0f}px " + " ".join(row))
    print("\nPi-px = person height at 1080p on the Pi camera at that altitude.")
    print("Takeaway: raising imgsz rescues small targets; lowering conf helps but")
    print("needs the MIN_BOX_PX floor (and mission.py's confirm-over-frames) to")
    print("keep false positives out. Real footage from altitude: Phase 3.")


def live(imgsz, conf):
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    cap = _open_camera()
    alt, font = 10, cv2.FONT_HERSHEY_SIMPLEX
    while True:
        ok, frame = cap.read()
        if not ok:
            sys.exit("No frame from camera.")
        view = fake_altitude(frame, alt)
        hits = _person_boxes(model, view, imgsz, conf)
        for box, c in hits:
            cv2.rectangle(view, box[:2], box[2:], (0, 255, 0), 1)
            cv2.putText(view, f"{c:.2f}", (box[0], max(box[1] - 4, 10)), font, 0.4, (0, 255, 0), 1)
        status = "DETECTED" if hits else "MISSED"
        cv2.putText(view, f"sim alt {alt} m (~{person_px(alt):.0f}px on Pi cam)  imgsz {imgsz}"
                          f" conf {conf}  {status}", (10, 30), font, 0.6,
                    (0, 255, 0) if hits else (0, 0, 255), 2)
        cv2.imshow("AeroMed altitude - w/s climb/descend, q quits", view)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        alt = min(60, alt + 5) if k == ord("w") else max(2, alt - 5) if k == ord("s") else alt
    cap.release()
    cv2.destroyAllWindows()


def selfcheck():
    assert person_px(15) > person_px(30) > person_px(50)          # further = smaller
    assert abs(person_px(30) / person_px(15) - 0.5) < 1e-6        # inverse-linear in altitude
    assert 70 < person_px(30) < 95, person_px(30)                 # ~82 px at 30 m, 1080p
    f = fake_altitude(np.full((480, 640, 3), 200, np.uint8), 30)
    assert f.shape == (480, 640, 3) and f.dtype == np.uint8
    assert f[240, 320, 0] == 200 and f[5, 5, 0] == 128            # content centred, canvas around it
    print("selfcheck OK")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse local yolov8n.pt
    p = argparse.ArgumentParser()
    p.add_argument("--sweep", action="store_true")
    p.add_argument("--imgsz", type=int, default=1280)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    selfcheck() if a.selfcheck else sweep() if a.sweep else live(a.imgsz, a.conf)
