"""AeroMed Phase 1.5 — describe-the-target chat UI (extends gap 1).

Type what the target looks like into a browser chat box ("individual wearing
red shirt and blue trousers", "person next to a white car") and the live feed
only flags people matching the description. Deliberately NO language model:
the drone flies offline, so parsing is keyword-based — colour words, clothing
words, and COCO object names. Colour is judged in HSV on the upper (shirt)
and lower (trousers) parts of each person box: the "coloured blob" idea.

Run:       .venv/bin/python target_chat.py          then open http://localhost:8010
Selfcheck: .venv/bin/python target_chat.py --selfcheck   (no camera/model needed)

Honest limits: dusk/shadow shifts colours (see lighting.py); the shirt/trouser
split needs the person reasonably large — at long range match on one colour.
"""
import argparse
import os
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

import detect

# HSV ranges per colour word (OpenCV hue 0-179; red wraps around 0)
COLORS = {
    "red":    [((0, 80, 60), (10, 255, 255)), ((170, 80, 60), (179, 255, 255))],
    "orange": [((11, 80, 60), (22, 255, 255))],
    "yellow": [((23, 80, 60), (35, 255, 255))],
    "green":  [((36, 60, 50), (85, 255, 255))],
    "blue":   [((90, 60, 50), (130, 255, 255))],
    "purple": [((131, 60, 50), (165, 255, 255))],
    "white":  [((0, 0, 170), (179, 45, 255))],
    "black":  [((0, 0, 0), (179, 255, 65))],
    "grey":   [((0, 0, 66), (179, 45, 169))],
}
UPPER = {"shirt", "tshirt", "t-shirt", "top", "jacket", "hoodie", "jumper", "sweater", "coat", "vest"}
LOWER = {"trousers", "trouser", "pants", "jeans", "shorts", "skirt", "leggings", "bottoms"}
MATCH_FRAC = 0.25   # region "is" a colour when this fraction of its pixels fit
NEAR = 4            # "next to" = object centre within this many person-widths


def parse(text, object_names):
    """'red shirt and blue trousers, next to a white car' ->
    {'upper': ['red'], 'lower': ['blue'], 'objects': [('white', 'car')]}
    Colour words attach to the next clothing/object word they precede.
    ponytail: single-word COCO names only ('car', 'dog'), not 'cell phone'."""
    words = re.findall(r"[a-z-]+", text.lower().replace("gray", "grey"))
    spec = {"upper": [], "lower": [], "objects": []}
    pending = []
    for w in words:
        if w in COLORS:
            pending.append(w)
        elif w in UPPER:
            spec["upper"] += pending
            pending = []
        elif w in LOWER:
            spec["lower"] += pending
            pending = []
        elif w in object_names:
            spec["objects"] += [(c, w) for c in pending] or [(None, w)]
            pending = []
    if pending and not spec["upper"] and not spec["lower"]:
        spec["upper"] = pending          # "wearing red" = red top
    return spec


def describe(spec):
    bits = []
    if spec["upper"]:
        bits.append("/".join(spec["upper"]) + " top")
    if spec["lower"]:
        bits.append("/".join(spec["lower"]) + " bottom")
    bits += [f"near {c or 'any'} {n}" for c, n in spec["objects"]]
    return ", ".join(bits) or "none - everyone matches"


def color_frac(region, color):
    """Fraction of a BGR region's pixels inside the colour's HSV range."""
    if region.size == 0:
        return 0.0
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    hit = sum(int(np.count_nonzero(cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))))
              for lo, hi in COLORS[color])
    return hit / (region.shape[0] * region.shape[1])


def person_matches(frame, box, spec):
    """Shirt = upper box (head skipped), trousers = lower box, central 60% width."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    cx1, cx2 = x1 + int(0.2 * w), x2 - int(0.2 * w)
    regions = {"upper": frame[y1 + int(0.15 * h): y1 + int(0.5 * h), cx1:cx2],
               "lower": frame[y1 + int(0.5 * h): y1 + int(0.95 * h), cx1:cx2]}
    for part in ("upper", "lower"):
        if spec[part] and not any(color_frac(regions[part], c) >= MATCH_FRAC for c in spec[part]):
            return False
    return True


def objects_ok(frame, objs, wanted, person_box):
    """Every requested context object must exist, colour-match, and be near the person."""
    for color, name in wanted:
        for ob in objs.get(name, ()):
            if color and color_frac(frame[ob[1]:ob[3], ob[0]:ob[2]], color) < MATCH_FRAC:
                continue
            pw = person_box[2] - person_box[0]
            pcx, pcy = (person_box[0] + person_box[2]) / 2, (person_box[1] + person_box[3]) / 2
            ocx, ocy = (ob[0] + ob[2]) / 2, (ob[1] + ob[3]) / 2
            if abs(ocx - pcx) <= NEAR * pw and abs(ocy - pcy) <= NEAR * pw:
                break
        else:
            return False
    return True


def annotate(frame, model, spec):
    font = cv2.FONT_HERSHEY_SIMPLEX
    h, w = frame.shape[:2]
    persons, objs = [], {}
    for b in model(frame, verbose=False)[0].boxes:
        box = tuple(map(int, b.xyxy[0]))
        name = model.names[int(b.cls[0])]
        if name == "person":
            persons.append(box)
        else:
            objs.setdefault(name, []).append(box)

    for color, name in spec["objects"]:  # show which context objects qualify
        for ob in objs.get(name, ()):
            if not color or color_frac(frame[ob[1]:ob[3], ob[0]:ob[2]], color) >= MATCH_FRAC:
                cv2.rectangle(frame, ob[:2], ob[2:], (255, 160, 0), 2)
                cv2.putText(frame, f"{color or ''} {name}".strip(),
                            (ob[0], max(ob[1] - 6, 12)), font, 0.5, (255, 160, 0), 2)

    target = None  # largest (= nearest) matching person wins
    for pb in sorted(persons, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True):
        if person_matches(frame, pb, spec) and objects_ok(frame, objs, spec["objects"], pb):
            target = pb
            break
    for pb in persons:
        if pb != target:
            cv2.rectangle(frame, pb[:2], pb[2:], (120, 120, 120), 1)
    if target:
        _, _, hint = detect.steering_hint(target, w, h)
        cv2.rectangle(frame, target[:2], target[2:], (0, 255, 0), 3)
        cv2.putText(frame, f"TARGET {hint}", (target[0], max(target[1] - 8, 20)), font, 0.7, (0, 255, 0), 2)
    miss = "" if target or not any(spec.values()) else "  |  NO MATCH"
    cv2.putText(frame, f"looking for: {describe(spec)}{miss}", (10, 25), font, 0.6, (0, 255, 255), 2)
    return frame


# --- browser chat UI (stdlib http.server, same pattern as stream.py) ---

SPEC = {"upper": [], "lower": [], "objects": []}
LOCK = threading.Lock()
MODEL = VS = None
OBJECT_NAMES = set()

PAGE = b"""<!doctype html><meta charset=utf-8><title>AeroMed target chat</title>
<body style="margin:0;background:#111;color:#eee;font-family:system-ui;text-align:center">
<p style="margin:8px">AeroMed &mdash; describe the target
<span style="color:#888">(colours + shirt/trousers/jacket... + objects: car, truck, dog, backpack...)</span></p>
<img src="/stream" style="max-width:100%">
<form style="margin:10px" onsubmit="send(event)">
<input id=t size=55 placeholder="individual wearing red shirt and blue trousers, next to a white car"
       style="padding:8px;border-radius:6px;border:0">
<button style="padding:8px 14px">set target</button>
<button type=button onclick="reset()" style="padding:8px 14px">clear</button>
</form>
<p id=f style="color:#6f6">looking for: none - everyone matches</p>
<script>
async function post(v){const r=await fetch('/prompt',{method:'POST',body:v});
document.getElementById('f').textContent='looking for: '+await r.text();}
function send(e){e.preventDefault();post(document.getElementById('t').value);}
function reset(){document.getElementById('t').value='';post('');}
</script>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        global SPEC
        text = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
        with LOCK:
            SPEC = parse(text, OBJECT_NAMES)
            msg = describe(SPEC)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(msg.encode())

    def do_GET(self):
        if self.path != "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE)
            return
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=f")
        self.end_headers()
        try:
            while True:
                frame = VS.read()
                if frame is None:
                    break
                with LOCK:
                    spec = SPEC
                annotate(frame, MODEL, spec)
                ok, buf = cv2.imencode(".jpg", frame)
                if ok:
                    self.wfile.write(b"--f\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass


def main(port):
    global MODEL, VS, OBJECT_NAMES
    from ultralytics import YOLO
    from camera import VideoStream
    MODEL = YOLO("yolov8n.pt")
    OBJECT_NAMES = {n for n in MODEL.names.values() if n != "person" and " " not in n}
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. System Settings > Privacy & Security > Camera.")
    VS = VideoStream(cap)
    while VS.read() is None:
        time.sleep(0.05)
    print(f"AeroMed target chat: http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def selfcheck():
    s = parse("individual is wearing a red shirt and blue trousers", {"car"})
    assert s["upper"] == ["red"] and s["lower"] == ["blue"] and not s["objects"], s
    s = parse("person next to a red car", {"car"})
    assert s["objects"] == [("red", "car")] and not s["upper"], s
    assert parse("wearing red", {"car"})["upper"] == ["red"]
    assert parse("next to a car", {"car"})["objects"] == [(None, "car")]
    assert parse("", {"car"}) == {"upper": [], "lower": [], "objects": []}

    red = np.full((20, 20, 3), (0, 0, 255), np.uint8)
    blue = np.full((20, 20, 3), (255, 0, 0), np.uint8)
    assert color_frac(red, "red") > 0.9 and color_frac(red, "blue") == 0
    assert color_frac(blue, "blue") > 0.9
    assert color_frac(np.full((20, 20, 3), 255, np.uint8), "white") > 0.9

    person = np.zeros((200, 100, 3), np.uint8)
    person[:100] = (0, 0, 255)   # red shirt
    person[100:] = (255, 0, 0)   # blue trousers
    box = (0, 0, 100, 200)
    assert person_matches(person, box, {"upper": ["red"], "lower": ["blue"], "objects": []})
    assert not person_matches(person, box, {"upper": ["green"], "lower": [], "objects": []})

    frame = np.zeros((300, 400, 3), np.uint8)
    frame[0:60, 150:250] = (0, 0, 255)             # a red car-sized blob
    objs = {"car": [(150, 0, 250, 60)]}
    assert objects_ok(frame, objs, [("red", "car")], (100, 100, 140, 200))       # near
    assert not objects_ok(frame, objs, [("blue", "car")], (100, 100, 140, 200))  # wrong colour
    assert not objects_ok(frame, objs, [("red", "car")], (0, 250, 20, 290))      # too far
    assert not objects_ok(frame, {}, [("red", "car")], (100, 100, 140, 200))     # no car at all
    print("selfcheck OK")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse local yolov8n.pt
    p = argparse.ArgumentParser()
    p.add_argument("port", nargs="?", type=int, default=8010)
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    selfcheck() if a.selfcheck else main(a.port)
