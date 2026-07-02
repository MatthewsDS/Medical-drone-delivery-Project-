"""AeroMed Phase 1.5 — describe-the-target chat UI (extends gap 1).

Type what the target looks like into a browser chat box ("individual wearing
red shirt and blue trousers", "person next to a white car") and the live feed
only flags people matching the description. Deliberately NO language model:
the drone flies offline by default, so parsing is keyword-based — colour
words, clothing words, and COCO object names. Colour is judged in HSV inside
the shirt/trouser regions of each person, located by pose keypoints when
visible (correct even sitting at a desk) and by box fractions otherwise.
A garment that isn't visible (trousers below the frame) never vetoes a match.

One background thread runs detection and publishes an annotated JPEG; any
number of browser connections just receive copies — inference never runs
per-client (that's the camera.py lesson applied to a server).

Run:       .venv/bin/python target_chat.py          then open http://localhost:8010
Selfcheck: .venv/bin/python target_chat.py --selfcheck   (no camera/model needed)

Honest limits: dusk/shadow shifts colours (see lighting.py); treat colour as
a filter for choosing between candidates, waving/marker as the confirmation.
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
# COCO pose keypoints: shoulders, hips, knees
L_SH, R_SH, L_HP, R_HP, L_KN, R_KN = 5, 6, 11, 12, 13, 14
KP_CONF = 0.3


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


def person_regions(frame, box, kxy=None, kc=None):
    """Shirt/trouser pixel regions for one person. Pose keypoints when seen
    (shirt = shoulders..hips, trousers = hips..knees — right even when only
    chest-up is in frame); box fractions otherwise. Empty region = garment
    not visible, and the caller skips judging it."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    cx1, cx2 = x1 + int(0.2 * w), x2 - int(0.2 * w)
    upper = frame[y1 + int(0.15 * h): y1 + int(0.5 * h), cx1:cx2]
    lower = frame[y1 + int(0.5 * h): y1 + int(0.95 * h), cx1:cx2]
    if kxy and kc:
        sy = [kxy[i][1] for i in (L_SH, R_SH) if kc[i] > KP_CONF]
        hy = [kxy[i][1] for i in (L_HP, R_HP) if kc[i] > KP_CONF]
        ky = [kxy[i][1] for i in (L_KN, R_KN) if kc[i] > KP_CONF]
        if sy:
            upper = frame[int(min(sy)): int(min(hy)) if hy else y2, cx1:cx2]
            lower = (frame[int(min(hy)): int(max(ky)) if ky else y2, cx1:cx2]
                     if hy else frame[0:0, 0:0])
    return {"upper": upper, "lower": lower}


def person_matches(frame, box, spec, kxy=None, kc=None):
    regions = person_regions(frame, box, kxy, kc)
    for part in ("upper", "lower"):
        want, reg = spec[part], regions[part]
        if want and reg.size and not any(color_frac(reg, c) >= MATCH_FRAC for c in want):
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


def annotate(frame, spec, pose_model, obj_model):
    font = cv2.FONT_HERSHEY_SIMPLEX
    h, w = frame.shape[:2]
    r = pose_model(frame, verbose=False)[0]
    kp = r.keypoints if r.keypoints is not None and r.keypoints.conf is not None else None
    persons = []
    for i, b in enumerate(r.boxes):
        box = tuple(map(int, b.xyxy[0]))
        persons.append((box,
                        kp.xy[i].tolist() if kp is not None else None,
                        kp.conf[i].tolist() if kp is not None else None))

    objs = {}
    if spec["objects"]:  # second model runs only when the request needs it
        for b in obj_model(frame, verbose=False)[0].boxes:
            name = obj_model.names[int(b.cls[0])]
            if name != "person":
                objs.setdefault(name, []).append(tuple(map(int, b.xyxy[0])))
        for color, name in spec["objects"]:  # show which context objects qualify
            for ob in objs.get(name, ()):
                if not color or color_frac(frame[ob[1]:ob[3], ob[0]:ob[2]], color) >= MATCH_FRAC:
                    cv2.rectangle(frame, ob[:2], ob[2:], (255, 160, 0), 2)
                    cv2.putText(frame, f"{color or ''} {name}".strip(),
                                (ob[0], max(ob[1] - 6, 12)), font, 0.5, (255, 160, 0), 2)

    target = None  # largest (= nearest) matching person wins
    for box, kxy, kc in sorted(persons, key=lambda p: (p[0][2] - p[0][0]) * (p[0][3] - p[0][1]),
                               reverse=True):
        if person_matches(frame, box, spec, kxy, kc) and objects_ok(frame, objs, spec["objects"], box):
            target = box
            break
    for box, _, _ in persons:
        if box != target:
            cv2.rectangle(frame, box[:2], box[2:], (120, 120, 120), 1)
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
JPEG = None  # latest annotated frame as bytes; whole-object swap is atomic under the GIL
VS = None
OBJECT_NAMES = set()

# The page polls /frame for independent JPEGs instead of one long MJPEG
# stream — Safari stalls mid-frame on multipart streams; polling can't freeze.
PAGE = b"""<!doctype html><meta charset=utf-8><title>AeroMed target chat</title>
<body style="margin:0;background:#111;color:#eee;font-family:system-ui;text-align:center">
<p style="margin:8px">AeroMed &mdash; describe the target
<span style="color:#888">(colours + shirt/trousers/jacket... + objects: car, truck, dog, backpack...)</span></p>
<img id=v style="max-width:100%;min-height:200px">
<form style="margin:10px" onsubmit="send(event)">
<input id=t size=55 placeholder="individual wearing red shirt and blue trousers, next to a white car"
       style="padding:8px;border-radius:6px;border:0">
<button style="padding:8px 14px">set target</button>
<button type=button onclick="reset()" style="padding:8px 14px">clear</button>
</form>
<p id=f style="color:#6f6">looking for: ...</p>
<script>
async function post(v){const r=await fetch('/prompt',{method:'POST',body:v});
document.getElementById('f').textContent='looking for: '+await r.text();}
function send(e){e.preventDefault();post(document.getElementById('t').value);}
function reset(){document.getElementById('t').value='';post('');}
const img=document.getElementById('v');
async function tick(){
 try{const r=await fetch('/frame');const b=await r.blob();
  const u=URL.createObjectURL(b);img.onload=()=>URL.revokeObjectURL(u);img.src=u;
 }catch(e){}
 setTimeout(tick,66);
}
window.onload=async()=>{tick();const r=await fetch('/filter');
document.getElementById('f').textContent='looking for: '+await r.text();};
</script>
"""


def _producer(pose_model, obj_model):
    """The ONLY thread that runs inference; browsers get copies of its output."""
    global JPEG
    while True:
        frame = VS.read()
        if frame is None:
            time.sleep(0.05)
            continue
        with LOCK:
            spec = SPEC
        try:
            annotate(frame, spec, pose_model, obj_model)
            ok, buf = cv2.imencode(".jpg", frame)
            if ok:
                JPEG = buf.tobytes()
        except Exception as e:  # one bad frame must never kill the whole feed
            print("producer error:", e)
            time.sleep(0.1)


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
        if self.path == "/filter":
            with LOCK:
                msg = describe(SPEC)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(msg.encode())
            return
        if self.path == "/frame":
            j = JPEG
            while j is None:  # camera still warming up
                time.sleep(0.05)
                j = JPEG
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(j)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(j)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(PAGE)


def main(port):
    global VS, OBJECT_NAMES
    from ultralytics import YOLO
    from camera import VideoStream
    pose_model = YOLO("yolov8n-pose.pt")
    obj_model = YOLO("yolov8n.pt")
    OBJECT_NAMES = {n for n in obj_model.names.values() if n != "person" and " " not in n}
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Camera won't open. System Settings > Privacy & Security > Camera.")
    VS = VideoStream(cap)
    while VS.read() is None:
        time.sleep(0.05)
    threading.Thread(target=_producer, args=(pose_model, obj_model), daemon=True).start()
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

    # full body in frame, no keypoints: box-fraction regions
    person = np.zeros((200, 100, 3), np.uint8)
    person[:100] = (0, 0, 255)   # red shirt
    person[100:] = (255, 0, 0)   # blue trousers
    box = (0, 0, 100, 200)
    assert person_matches(person, box, {"upper": ["red"], "lower": ["blue"], "objects": []})
    assert not person_matches(person, box, {"upper": ["green"], "lower": [], "objects": []})

    # desk view: only chest-up visible — keypoints place the shirt correctly
    desk = np.zeros((200, 100, 3), np.uint8)
    desk[:100] = (0, 255, 0)      # head-height clutter the box heuristic would judge
    desk[100:] = (255, 255, 255)  # the actual white shirt
    kxy, kc = [[50, 0]] * 17, [0.0] * 17
    kxy[L_SH], kxy[R_SH] = [20, 100], [80, 100]
    kc[L_SH] = kc[R_SH] = 0.9     # shoulders seen; hips/knees below the frame
    spec = {"upper": ["white"], "lower": ["blue"], "objects": []}
    assert person_matches(desk, box, spec, kxy, kc)  # shirt matches; unseen trousers don't veto
    assert not person_matches(desk, box, spec)       # box heuristic alone judges the clutter

    frame = np.zeros((300, 400, 3), np.uint8)
    frame[0:60, 150:250] = (0, 0, 255)             # a red car-sized blob
    objs = {"car": [(150, 0, 250, 60)]}
    assert objects_ok(frame, objs, [("red", "car")], (100, 100, 140, 200))       # near
    assert not objects_ok(frame, objs, [("blue", "car")], (100, 100, 140, 200))  # wrong colour
    assert not objects_ok(frame, objs, [("red", "car")], (0, 250, 20, 290))      # too far
    assert not objects_ok(frame, {}, [("red", "car")], (100, 100, 140, 200))     # no car at all
    print("selfcheck OK")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse local model files
    p = argparse.ArgumentParser()
    p.add_argument("port", nargs="?", type=int, default=8010)
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    selfcheck() if a.selfcheck else main(a.port)
