"""AeroMed Phase 1.5 — ArUco marker landing target (gap 4).

Person detection *guesses* (a learned model with a confidence score); an
ArUco marker *measures*. Markers are binary-coded squares OpenCV detects with
effectively zero false positives, and — because the printed size is known —
one detection gives full 3D pose: distance AND lateral offset in metres, not
pixels. Proven at 32 m altitude (goodrobots/vision_landing). Rule of thumb:
if anyone can place a marker at the delivery point beforehand, the marker IS
the primary landing system and person detection is the fallback — not the
other way round.

Make one:  .venv/bin/python aruco_landing.py --make-marker
           (writes marker_0.png — print ~10 cm wide, or full-screen it on a phone)
Run:       .venv/bin/python aruco_landing.py              (webcam; show it the marker)
           .venv/bin/python aruco_landing.py --size 0.06  (marker printed 6 cm wide)
Selfcheck: .venv/bin/python aruco_landing.py --selfcheck  (no camera needed)
"""
import argparse
import sys

import cv2
import numpy as np

import detect

DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
MARKER_M = 0.10  # printed marker side in metres — must match reality for true distance


def make_detector():
    return cv2.aruco.ArucoDetector(DICT, cv2.aruco.DetectorParameters())


def guess_intrinsics(w, h):
    """No-calibration camera matrix: fx=fy=w is roughly a 60-degree lens.
    Distances come out +/-10-20% until the real Pi camera is chessboard-
    calibrated (Phase 3, needs the physical camera)."""
    return np.array([[w, 0, w / 2], [0, w, h / 2], [0, 0, 1]], dtype=float)


def find_marker(frame, detector):
    """-> (corners (4,2) float array, id) of the first marker, or (None, None)."""
    corners, ids, _ = detector.detectMarkers(frame)
    if ids is None:
        return None, None
    return corners[0][0], int(ids[0][0])


def marker_pose(corners, cam_mtx, size_m=MARKER_M):
    """corners (4,2) -> (x, y, z) of the marker centre in metres, camera frame.
    z = distance straight out of the lens; x right, y down. Corner order from
    detectMarkers (TL,TR,BR,BL) matches SOLVEPNP_IPPE_SQUARE's expected order."""
    half = size_m / 2
    obj = np.array([[-half, half, 0], [half, half, 0],
                    [half, -half, 0], [-half, -half, 0]], dtype=float)
    ok, _, tvec = cv2.solvePnP(obj, corners.astype(float), cam_mtx, None,
                               flags=cv2.SOLVEPNP_IPPE_SQUARE)
    return tuple(tvec.ravel()) if ok else None


def make_marker(marker_id=0, px=600):
    img = cv2.aruco.generateImageMarker(DICT, marker_id, px)
    img = cv2.copyMakeBorder(img, px // 8, px // 8, px // 8, px // 8,
                             cv2.BORDER_CONSTANT, value=255)  # white quiet zone — keep it when printing
    name = f"marker_{marker_id}.png"
    cv2.imwrite(name, img)
    print(f"wrote {name} — print it {MARKER_M * 100:.0f} cm wide (or pass --size), keep the white border")


def selfcheck():
    # closed loop, no camera: generate a marker, detect it, recover its pose
    px = 400
    img = cv2.aruco.generateImageMarker(DICT, 7, px)
    img = cv2.copyMakeBorder(img, 100, 100, 100, 100, cv2.BORDER_CONSTANT, value=255)
    frame = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    corners, mid = find_marker(frame, make_detector())
    assert mid == 7, mid
    h, w = frame.shape[:2]
    pose = marker_pose(corners, guess_intrinsics(w, h))
    # marker spans px pixels under focal length w => distance ~= w * size / px
    expect = w * MARKER_M / px
    assert pose is not None and abs(pose[2] - expect) / expect < 0.1, (pose, expect)
    print("selfcheck OK")


def main(size_m):
    detector = make_detector()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. System Settings > Privacy & Security > Camera.")
    cam, font = None, cv2.FONT_HERSHEY_SIMPLEX
    while True:
        ok, frame = cap.read()
        if not ok:
            sys.exit("No frame from camera.")
        h, w = frame.shape[:2]
        if cam is None:
            cam = guess_intrinsics(w, h)
        corners, mid = find_marker(frame, detector)
        if corners is None:
            cv2.putText(frame, "no marker", (10, 30), font, 0.8, (0, 0, 255), 2)
        else:
            xs, ys = corners[:, 0], corners[:, 1]
            box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
            _, _, hint = detect.steering_hint(box, w, h)
            pose = marker_pose(corners, cam, size_m)
            dist = f"  dist {pose[2]:.2f} m" if pose else ""
            locked = hint == "CENTERED"
            color = (0, 255, 0) if locked else (0, 200, 255)
            cv2.polylines(frame, [corners.astype("int32")], True, color, 2)
            cv2.putText(frame, f"{'LOCKED  ' if locked else ''}id {mid}  {hint}{dist}",
                        (10, 30), font, 0.8, color, 2)
        cv2.imshow("AeroMed ArUco - q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--make-marker", action="store_true")
    p.add_argument("--id", type=int, default=0)
    p.add_argument("--size", type=float, default=MARKER_M, help="printed marker side, metres")
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    if a.selfcheck:
        selfcheck()
    elif a.make_marker:
        make_marker(a.id)
    else:
        main(a.size)
