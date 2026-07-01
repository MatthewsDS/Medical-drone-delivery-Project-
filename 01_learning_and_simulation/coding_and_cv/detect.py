"""AeroMed Phase 1 — webcam detection + targeting.

Webcam -> pretrained YOLO -> nearest target -> steering hint toward center.
Swap VideoCapture(0) for the Pi camera later; nothing else changes.

Run:       .venv/bin/python detect.py            (native window, default target: person)
Class:     .venv/bin/python detect.py --target cup
Selfcheck: .venv/bin/python detect.py --selfcheck   (no camera/model needed)

Browser preview: run stream.py instead (imports the helpers below).
"""
import argparse
import sys


def steering_hint(box, frame_w, frame_h, deadzone=0.15):
    """Offset of box-center from frame-center + a human steering hint.

    box = (x1, y1, x2, y2). Returns (dx, dy, hint).
    dx>0 target is right of center, dy>0 target is below center.
    Within `deadzone` fraction of frame on an axis => that axis is centered.
    """
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    dx = cx - frame_w / 2
    dy = cy - frame_h / 2
    horiz = "RIGHT" if dx > deadzone * frame_w / 2 else "LEFT" if dx < -deadzone * frame_w / 2 else ""
    vert = "DOWN" if dy > deadzone * frame_h / 2 else "UP" if dy < -deadzone * frame_h / 2 else ""
    hint = " ".join(w for w in (vert, horiz) if w) or "CENTERED"
    return dx, dy, hint


def nearest(boxes):
    """Largest-area box (nearest target). boxes = list of (x1,y1,x2,y2). None if empty."""
    if not boxes:
        return None
    return max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))


def load(target="person"):
    """Return (model, want_class_ids) for the target class. Exits if class unknown."""
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    want = {i for i, n in model.names.items() if n == target}
    if not want:
        sys.exit(f"'{target}' is not a YOLO class. Try: person, cup, bottle, cell phone")
    return model, want


def annotate(frame, model, want, target, quiet=True):
    """Box + name every detected object; steering hint on the nearest target."""
    import cv2
    font = cv2.FONT_HERSHEY_SIMPLEX
    h, w = frame.shape[:2]
    target_boxes = []
    for b in model(frame, verbose=False)[0].boxes:
        x1, y1, x2, y2 = map(int, b.xyxy[0])
        cls = int(b.cls[0])
        name = model.names[cls]
        conf = float(b.conf[0])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{name} {conf:.0%}", (x1, max(y1 - 6, 12)), font, 0.5, (0, 255, 0), 2)
        if cls in want:
            target_boxes.append((x1, y1, x2, y2))

    box = nearest(target_boxes)
    if box is None:
        cv2.putText(frame, f"no {target}", (10, 30), font, 0.8, (0, 0, 255), 2)
        return frame
    dx, dy, hint = steering_hint(box, w, h)
    x1, y1, x2, y2 = box
    cv2.circle(frame, ((x1 + x2) // 2, (y1 + y2) // 2), 4, (0, 0, 255), -1)
    label = f"{target}  {hint}  (dx={dx:+.0f} dy={dy:+.0f})"
    cv2.putText(frame, label, (10, 30), font, 0.7, (0, 255, 0), 2)
    if not quiet:
        print(label)
    return frame


def selfcheck():
    W, H = 640, 480
    _, _, h = steering_hint((300, 220, 340, 260), W, H)
    assert h == "CENTERED", h
    dx, dy, h = steering_hint((10, 10, 60, 60), W, H)
    assert dx < 0 and dy < 0 and "LEFT" in h and "UP" in h, (dx, dy, h)
    dx, dy, h = steering_hint((580, 420, 630, 470), W, H)
    assert dx > 0 and dy > 0 and "RIGHT" in h and "DOWN" in h, (dx, dy, h)
    assert nearest([]) is None
    assert nearest([(0, 0, 10, 10), (0, 0, 100, 100)]) == (0, 0, 100, 100)
    print("selfcheck OK")


def main(target="person"):
    import cv2
    model, want = load(target)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. Grant camera access: System Settings > "
                 "Privacy & Security > Camera > enable your terminal, then rerun.")
    while True:
        ok, frame = cap.read()
        if not ok:
            sys.exit("No frame from camera (black feed usually = camera permission denied).")
        annotate(frame, model, want, target, quiet=False)
        cv2.imshow("AeroMed CV - q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--target", default="person")
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    selfcheck() if a.selfcheck else main(a.target)
