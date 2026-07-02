"""AeroMed Phase 1.5 — waving-person detection (gap 1).

Pretrained YOLO says "person", never "waving person". yolov8n-pose adds 17
body keypoints per person, so a wave becomes *behaviour over time*: a wrist
held above its shoulder that swings side-to-side. Either condition alone
fails (arm raised = maybe holding a phone up; side motion = maybe walking);
together they reject bystanders.

(File is named waving.py, not wave.py — `wave` is a Python stdlib module.)

Run:       .venv/bin/python waving.py               (webcam window; wave at it)
Selfcheck: .venv/bin/python waving.py --selfcheck   (no camera/model needed)

Pi note: identical code runs on the Pi 5 — just expect ~5-10 fps, not ~30.
"""
import argparse
import os
import sys
import time
from collections import deque

import detect

# COCO keypoint indices we use (of 17): shoulders and wrists
L_SH, R_SH, L_WR, R_WR = 5, 6, 9, 10
KP_CONF = 0.3  # keypoint confidence below this = not visible, don't judge it


class WaveDetector:
    """Wave = wrist above shoulder AND swinging side-to-side.

    Feed one sample per frame: update(wrist_x, raised, shoulder_w, t) -> bool.
    Travel and noise thresholds scale with shoulder width, so the same logic
    works close-up or from altitude. Pure logic — no camera needed to test.
    """

    def __init__(self, window=2.0, min_swings=2, min_travel=0.2, grace=0.4):
        self.window = window          # seconds of wrist history to judge
        self.min_swings = min_swings  # direction reversals required in the window
        self.min_travel = min_travel  # wrist travel required, in shoulder-widths
        self.grace = grace            # seconds of keypoint dropout tolerated
        self.track = deque()          # (t, x) samples while the wrist is raised
        self.last_raised = 0.0

    def update(self, wrist_x, raised, shoulder_w, t):
        if raised and shoulder_w > 0:
            self.last_raised = t
            self.track.append((t, wrist_x))
        elif t - self.last_raised > self.grace:
            self.track.clear()        # arm genuinely dropped, not a one-frame glitch
        if not self.track:
            return False
        while t - self.track[0][0] > self.window:
            self.track.popleft()
        xs = [x for _, x in self.track]
        if len(xs) < 5 or max(xs) - min(xs) < self.min_travel * shoulder_w:
            return False
        noise = 0.05 * shoulder_w     # ignore jitter smaller than this
        swings, last = 0, 0
        for a, b in zip(xs, xs[1:]):
            d = b - a
            if abs(d) < noise:
                continue
            s = 1 if d > 0 else -1
            if last and s != last:
                swings += 1           # wrist changed direction = one swing
            last = s
        return swings >= self.min_swings


def wave_status(result, wavers, t):
    """One frame's verdict for the nearest person in a yolov8-pose result.

    wavers = {"L": WaveDetector, "R": WaveDetector} kept across frames.
    Returns (box, waving): box of the nearest person or None.
    """
    boxes = [tuple(map(int, b)) for b in result.boxes.xyxy.tolist()]
    box = detect.nearest(boxes)
    if box is None or result.keypoints is None or result.keypoints.conf is None:
        for d in wavers.values():
            d.update(0, False, 0, t)
        return None, False
    i = boxes.index(box)
    kxy = result.keypoints.xy[i].tolist()
    kc = result.keypoints.conf[i].tolist()
    shoulder_w = abs(kxy[L_SH][0] - kxy[R_SH][0])  # scale reference at any distance
    waving = False
    for side, wr, sh in (("L", L_WR, L_SH), ("R", R_WR, R_SH)):
        seen = kc[wr] > KP_CONF and kc[sh] > KP_CONF
        raised = seen and kxy[wr][1] < kxy[sh][1]  # image y grows downward
        waving |= wavers[side].update(kxy[wr][0], raised, shoulder_w, t)
    return box, waving


def selfcheck():
    import math
    fps, sw = 30, 120
    # wrist raised + swinging (1.5 Hz, 200 px travel) => wave
    d = WaveDetector()
    assert any(d.update(100 * math.sin(2 * math.pi * 1.5 * i / fps), True, sw, i / fps)
               for i in range(2 * fps)), "sine swing should read as a wave"
    # raised but held still => no wave (holding a phone up is not a wave)
    d = WaveDetector()
    assert not any(d.update(300 + (i % 2), True, sw, i / fps) for i in range(2 * fps))
    # swinging but never raised => no wave (walking arm swing)
    d = WaveDetector()
    assert not any(d.update(100 * math.sin(2 * math.pi * 1.5 * i / fps), False, sw, i / fps)
                   for i in range(2 * fps))
    # keypoint flickering off every 5th frame (motion blur) must NOT reset the wave
    d = WaveDetector()
    assert any(d.update(100 * math.sin(2 * math.pi * 1.5 * i / fps), i % 5 != 0, sw, i / fps)
               for i in range(2 * fps)), "brief keypoint dropout should be tolerated"
    print("selfcheck OK")


def main():
    import cv2
    from ultralytics import YOLO
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse local model file
    model = YOLO("yolov8n-pose.pt")  # auto-downloads once (~6 MB)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. System Settings > Privacy & Security > Camera.")
    wavers = {"L": WaveDetector(), "R": WaveDetector()}
    font = cv2.FONT_HERSHEY_SIMPLEX
    while True:
        ok, frame = cap.read()
        if not ok:
            sys.exit("No frame from camera.")
        r = model(frame, verbose=False)[0]
        box, waving = wave_status(r, wavers, time.time())
        if box:
            arm_up = any(w.track for w in wavers.values())
            color = (0, 0, 255) if waving else (0, 200, 255) if arm_up else (0, 255, 0)
            label = ("WAVING - target confirmed" if waving
                     else "arm up - keep waving" if arm_up else "person (not waving)")
            cv2.rectangle(frame, box[:2], box[2:], color, 2)
            cv2.putText(frame, label, (10, 30), font, 0.8, color, 2)
        else:
            cv2.putText(frame, "no person", (10, 30), font, 0.8, (0, 0, 255), 2)
        cv2.imshow("AeroMed wave - q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--selfcheck", action="store_true")
    selfcheck() if p.parse_args().selfcheck else main()
