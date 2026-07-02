"""AeroMed Phase 1.5 — landing decision state machine (gap 6).

Detection is an opinion 30 times a second; landing is a decision over time.
This FSM is the contract between CV and flight control:

    CV  -> Detection(kind, dx, dy, dist) or None, once per frame
    FSM -> (state, command)   command = what MAVLink/DroneKit will be told

States:  SEARCH -> CONFIRM (wave seen) -> ALIGN -> DESCEND -> LAND
         a marker skips straight to ALIGN (markers need no confirmation)
         target lost too long: ALIGN -> SEARCH, DESCEND -> ABORT (climb, retry)
A person who is NOT waving never advances the mission — bystanders are not
delivery targets. Later, flight integration replaces exactly one thing: the
code that *prints* the command starts *sending* it.

Live demo: .venv/bin/python mission.py --live      (wave, or show marker_0.png)
Selfcheck: .venv/bin/python mission.py --selfcheck (no camera/model needed)
"""
import argparse
import os
import time
from collections import namedtuple

# dx, dy: offset of target from frame centre as a fraction of half-frame (-1..1)
# dist:   metres to a marker (None for person/wave detections)
Detection = namedtuple("Detection", "kind dx dy dist")  # kind: person | wave | marker

CONFIRM_FRAMES = 15  # ~1 s of sustained waving before we trust it
LOST_FRAMES = 30     # frames with no detection before a state gives up
ALIGNED = 0.15       # |dx|,|dy| under this = centred enough to descend
LAND_DIST = 0.5      # metres to marker = landed (demo stand-in for the TF-Luna LiDAR)


class LandingFSM:
    """Feed one step() per frame. Pure logic — the whole thing tests offline."""

    def __init__(self):
        self.state = "SEARCH"
        self.wave_streak = 0
        self.lost = 0

    def step(self, det):
        self.lost = 0 if det else self.lost + 1
        s = self.state

        if s == "SEARCH":
            self.wave_streak = 0
            if det and det.kind == "marker":
                self.state = "ALIGN"
            elif det and det.kind == "wave":
                self.state = "CONFIRM"
            return self.state, "fly search pattern"

        if s == "CONFIRM":
            if det and det.kind == "marker":
                self.state = "ALIGN"
            elif det and det.kind == "wave":
                self.wave_streak += 1
                if self.wave_streak >= CONFIRM_FRAMES:
                    self.state = "ALIGN"
            elif self.lost > LOST_FRAMES:
                self.state = "SEARCH"
            # ponytail: a visible-but-not-waving person holds CONFIRM open;
            # add a global mission timeout when flight integration lands
            return self.state, "hold position, confirming wave"

        if s == "ALIGN":
            # any detection kind counts here: a confirmed waver who pauses
            # mid-wave is still the target we are centring on
            if self.lost > LOST_FRAMES:
                self.state = "SEARCH"
                return self.state, "target lost - resume search"
            if det is None:
                return self.state, "hold (target flickered)"
            if abs(det.dx) < ALIGNED and abs(det.dy) < ALIGNED:
                self.state = "DESCEND"
                return self.state, "centred - begin descent"
            return self.state, f"strafe dx={det.dx:+.2f} dy={det.dy:+.2f}"

        if s == "DESCEND":
            if self.lost > LOST_FRAMES:
                self.state = "ABORT"
                return self.state, "climb 10 m, return to search"
            if det and det.dist is not None and det.dist < LAND_DIST:
                self.state = "LAND"
                return self.state, "cut throttle - landed"
            if det and (abs(det.dx) > 2 * ALIGNED or abs(det.dy) > 2 * ALIGNED):
                self.state = "ALIGN"  # drifted off centre - fix before descending further
                return self.state, "drifted - re-align"
            return self.state, "descend 0.5 m/s, keep centred"

        if s == "ABORT":
            self.state = "SEARCH"  # climb command was issued; go around
            return self.state, "fly search pattern"

        return self.state, "landed"  # LAND is terminal


def selfcheck():
    # a bystander (person, never waving) never advances the mission
    m = LandingFSM()
    for _ in range(100):
        s, _ = m.step(Detection("person", 0, 0, None))
    assert s == "SEARCH", s

    # wave -> confirm -> align -> descend -> land (marker measures the final metres)
    m = LandingFSM()
    m.step(Detection("wave", 0.9, 0.9, None))
    assert m.state == "CONFIRM"
    for _ in range(CONFIRM_FRAMES):
        m.step(Detection("wave", 0.9, 0.9, None))
    assert m.state == "ALIGN"
    m.step(Detection("wave", 0.5, 0.5, None))
    assert m.state == "ALIGN"  # not centred yet
    m.step(Detection("wave", 0.0, 0.0, None))
    assert m.state == "DESCEND"
    m.step(Detection("marker", 0.0, 0.0, 4.0))
    assert m.state == "DESCEND"  # still 4 m up
    s, cmd = m.step(Detection("marker", 0.0, 0.0, 0.3))
    assert s == "LAND" and "landed" in cmd, (s, cmd)

    # a marker skips confirmation entirely
    m = LandingFSM()
    m.step(Detection("marker", 0.8, 0.0, 6.0))
    assert m.state == "ALIGN"

    # losing the target during descent aborts, then goes around
    m = LandingFSM()
    m.step(Detection("marker", 0.0, 0.0, 6.0))
    m.step(Detection("marker", 0.0, 0.0, 6.0))
    assert m.state == "DESCEND"
    for _ in range(LOST_FRAMES + 1):
        m.step(None)
    assert m.state == "ABORT"
    s, _ = m.step(None)
    assert s == "SEARCH"
    print("selfcheck OK")


def live():
    import cv2
    from ultralytics import YOLO
    import aruco_landing
    import waving
    from camera import VideoStream

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    model = YOLO("yolov8n-pose.pt")
    aruco = aruco_landing.make_detector()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Camera won't open. System Settings > Privacy & Security > Camera.")
    vs = VideoStream(cap)
    while vs.read() is None:
        time.sleep(0.05)

    wavers = {"L": waving.WaveDetector(), "R": waving.WaveDetector()}
    fsm = LandingFSM()
    font = cv2.FONT_HERSHEY_SIMPLEX
    while True:
        frame = vs.read()
        if frame is None:
            break
        h, w = frame.shape[:2]

        det = None
        corners, _ = aruco_landing.find_marker(frame, aruco)
        if corners is not None:  # marker beats person: it measures, YOLO guesses
            cx, cy = corners[:, 0].mean(), corners[:, 1].mean()
            pose = aruco_landing.marker_pose(corners, aruco_landing.guess_intrinsics(w, h))
            det = Detection("marker", (cx - w / 2) / (w / 2), (cy - h / 2) / (h / 2),
                            pose[2] if pose else None)
            cv2.polylines(frame, [corners.astype("int32")], True, (255, 200, 0), 2)
        else:
            r = model(frame, verbose=False)[0]
            box, is_wave = waving.wave_status(r, wavers, time.time())
            if box:
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                det = Detection("wave" if is_wave else "person",
                                (cx - w / 2) / (w / 2), (cy - h / 2) / (h / 2), None)
                cv2.rectangle(frame, box[:2], box[2:], (0, 0, 255) if is_wave else (0, 255, 0), 2)

        state, cmd = fsm.step(det)
        cv2.putText(frame, f"{state}: {cmd}", (10, 30), font, 0.7, (0, 255, 255), 2)
        cv2.imshow("AeroMed mission - q quits, r resets", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        if k == ord("r"):
            fsm = LandingFSM()
    vs.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    live() if a.live else selfcheck()
