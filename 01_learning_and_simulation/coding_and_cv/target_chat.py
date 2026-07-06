"""AeroMed Phase 1.5 — describe-the-target UI (v2: sidebar + postures).

Full-screen live camera with a collapsible details sidebar. Type what the
target looks like — every detail is optional and only what you type is
checked ("red top" ignores bottoms entirely):

    colours   red orange yellow green blue purple white black grey
    garments  top/shirt/jacket...  bottom/trousers/jeans...
    posture   waving   (reuses waving.py's WaveDetector — behaviour over time)
              lying/laying   (box wider than tall)
    objects   next to a red car / yellow vehicle / dog / backpack ...

Deliberately NO language model in keyword mode: the drone flies offline.
The "AI search" button sends the same text to YOLO-World (any phrase, ~4 fps
on the Mac — ground-station/demo mode until the AI HAT+ arrives).

One background thread runs detection and publishes JPEGs; the page polls
/frame (freeze-proof in every browser). Errors print as "producer error:".

Run:       .venv/bin/python target_chat.py          then open http://localhost:8010
Selfcheck: .venv/bin/python target_chat.py --selfcheck   (no camera/model needed)

Honest limits: dusk/shadow shifts colours (see lighting.py) — colour picks
between candidates, waving/marker confirms. Wave progress follows the current
best candidate; two similar candidates alternating can reset it (foundation).
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
import waving as wv

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
UPPER = {"shirt", "tshirt", "t-shirt", "top", "upper", "jacket", "hoodie", "jumper", "sweater", "coat", "vest"}
LOWER = {"trousers", "trouser", "pants", "jeans", "shorts", "skirt", "leggings", "bottoms", "bottom", "lower"}
POSTURES = {"waving": "waving", "wave": "waving", "waves": "waving", "lying": "lying", "laying": "lying"}
ALIASES = {"vehicle": ("car", "truck", "bus"), "bike": ("bicycle", "motorcycle")}  # any-of class groups
MATCH_FRAC = 0.25   # region "is" a colour when this fraction of its pixels fit
NEAR = 4            # "next to" = object centre within this many person-widths
LYING_ASPECT = 1.15  # box wider than tall by this factor = lying down
# COCO pose keypoints: shoulders, hips, knees
L_SH, R_SH, L_HP, R_HP, L_KN, R_KN = 5, 6, 11, 12, 13, 14
KP_CONF = 0.3


def parse(text, object_names):
    """'red top, waving, next to a white car' ->
    {'upper': ['red'], 'lower': [], 'posture': ['waving'], 'objects': [('white', 'car')]}
    Colour words attach to the next clothing/object word they precede.
    Every part is optional — only what is typed gets checked.
    ponytail: single-word COCO names only ('car', 'dog'), not 'cell phone'."""
    words = re.findall(r"[a-z-]+", text.lower().replace("gray", "grey"))
    spec = {"upper": [], "lower": [], "objects": [], "posture": []}
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
        elif w in POSTURES:
            if POSTURES[w] not in spec["posture"]:
                spec["posture"].append(POSTURES[w])
        elif w in object_names or w in ALIASES:
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
    bits += spec["posture"]
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
    """Stateless checks: clothing colours + lying posture. (Waving is
    temporal and handled by the caller on the best candidate.)"""
    x1, y1, x2, y2 = box
    if "lying" in spec.get("posture", ()) and (x2 - x1) <= LYING_ASPECT * (y2 - y1):
        return False  # ponytail: aspect heuristic; keypoint-axis check if this misfires
    regions = person_regions(frame, box, kxy, kc)
    for part in ("upper", "lower"):
        want, reg = spec[part], regions[part]
        if want and reg.size and not any(color_frac(reg, c) >= MATCH_FRAC for c in want):
            return False
    return True


def objects_ok(frame, objs, wanted, person_box):
    """Every requested context object must exist, colour-match, and be near the person."""
    for color, name in wanted:
        for ob in [o for cls in ALIASES.get(name, (name,)) for o in objs.get(cls, ())]:
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
            for ob in [o for cls in ALIASES.get(name, (name,)) for o in objs.get(cls, ())]:
                if not color or color_frac(frame[ob[1]:ob[3], ob[0]:ob[2]], color) >= MATCH_FRAC:
                    cv2.rectangle(frame, ob[:2], ob[2:], (255, 160, 0), 2)
                    cv2.putText(frame, f"{color or ''} {name}".strip(),
                                (ob[0], max(ob[1] - 6, 12)), font, 0.5, (255, 160, 0), 2)

    cands = [(box, kxy, kc) for box, kxy, kc in persons
             if person_matches(frame, box, spec, kxy, kc)
             and objects_ok(frame, objs, spec["objects"], box)]

    target = pending = None
    need_wave = "waving" in spec["posture"]
    if cands:  # largest (= nearest) matching person is the candidate
        box, kxy, kc = max(cands, key=lambda p: (p[0][2] - p[0][0]) * (p[0][3] - p[0][1]))
        if need_wave:
            if kxy and wv.person_wave(kxy, kc, WAVERS, time.time()):
                target = box
            else:
                pending = box  # matches the description; wave not confirmed yet
        else:
            target = box
    elif need_wave:  # nobody matches: let wave history decay
        for d in WAVERS.values():
            d.update(0, False, 0, time.time())

    for box, _, _ in persons:
        if box != target and box != pending:
            cv2.rectangle(frame, box[:2], box[2:], (120, 120, 120), 1)
    if pending:
        arm_up = any(d.track for d in WAVERS.values())
        cv2.rectangle(frame, pending[:2], pending[2:], (0, 200, 255), 2)
        cv2.putText(frame, "keep waving" if arm_up else "waiting for wave",
                    (pending[0], max(pending[1] - 8, 20)), font, 0.7, (0, 200, 255), 2)
    if target:
        _, _, hint = detect.steering_hint(target, w, h)
        cv2.rectangle(frame, target[:2], target[2:], (0, 255, 0), 3)
        cv2.putText(frame, f"TARGET {hint}", (target[0], max(target[1] - 8, 20)), font, 0.7, (0, 255, 0), 2)
    miss = "" if target or pending or not any(spec.values()) else "  |  NO MATCH"
    cv2.putText(frame, f"looking for: {describe(spec)}{miss}", (10, 25), font, 0.6, (0, 255, 255), 2)
    return frame


# --- browser UI (stdlib http.server; page polls /frame — freeze-proof) ---

SPEC = {"upper": [], "lower": [], "objects": [], "posture": []}
WAVERS = {"L": wv.WaveDetector(), "R": wv.WaveDetector()}
LOCK = threading.Lock()
JPEG = None  # latest annotated frame as bytes; whole-object swap is atomic under the GIL
VS = None
OBJECT_NAMES = set()
MODE = "kw"            # "kw" (keyword+colour, flight-ready) or "world" (AI search)
WORLD = None           # lazy-loaded YOLOWorld model
WORLD_LABEL = ""
WLOCK = threading.Lock()


def _phrases(text):
    """'white shirt, next to a yellow vehicle' -> ['white shirt', 'a yellow vehicle']"""
    return [p.strip() for p in re.split(r",|\band\b|\bnext to\b", text.lower()) if p.strip()]


def annotate_world(frame, result, label):
    font = cv2.FONT_HERSHEY_SIMPLEX
    h, w = frame.shape[:2]
    boxes = []
    for b in result.boxes:
        box = tuple(map(int, b.xyxy[0]))
        boxes.append(box)
        cv2.rectangle(frame, box[:2], box[2:], (0, 255, 0), 1)
        cv2.putText(frame, f"{result.names[int(b.cls[0])]} {float(b.conf[0]):.0%}",
                    (box[0], max(box[1] - 6, 12)), font, 0.5, (0, 255, 0), 2)
    target = detect.nearest(boxes)
    if target:
        _, _, hint = detect.steering_hint(target, w, h)
        cv2.rectangle(frame, target[:2], target[2:], (0, 255, 0), 3)
        cv2.putText(frame, f"TARGET {hint}", (target[0], max(target[1] - 8, 20)), font, 0.7, (0, 255, 0), 2)
    miss = "" if target else "  |  NO MATCH"
    cv2.putText(frame, f"AI search: {label}{miss}", (10, 25), font, 0.6, (0, 255, 255), 2)


PAGE = b"""<!doctype html><html lang=en><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>AeroMed Vision</title>
<style>
:root{--bg:#020617;--s1:#0f172a;--s2:#1e293b;--bd:#334155;--fg:#f8fafc;
      --mut:#94a3b8;--acc:#22c55e;--accd:#052e16;--warn:#f59e0b;--red:#ef4444}
*{box-sizing:border-box}
body{margin:0;height:100dvh;display:flex;overflow:hidden;background:var(--bg);
     color:var(--fg);font-family:system-ui,-apple-system,sans-serif;font-size:16px}
button{cursor:pointer;font:inherit;transition:background .2s,border-color .2s,opacity .2s}
button:focus-visible,input:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
#burger{position:fixed;top:12px;left:12px;z-index:50;width:44px;height:44px;
        border:1px solid var(--bd);border-radius:10px;background:var(--s1);color:var(--fg);
        display:flex;align-items:center;justify-content:center}
#burger:hover{background:var(--s2)}
#sb{width:320px;min-width:320px;background:var(--s1);border-right:1px solid var(--bd);
    padding:68px 20px 20px;display:flex;flex-direction:column;gap:14px;
    overflow-y:auto;transition:margin .25s ease}
body.closed #sb{margin-left:-320px}
#sb h1{margin:0;font-size:15px;letter-spacing:.18em;font-family:ui-monospace,monospace}
#sb h1 span{color:var(--acc)}
#sb .sub{margin:-8px 0 0;color:var(--mut);font-size:13px}
#t{width:100%;padding:12px;border-radius:10px;border:1px solid var(--bd);
   background:var(--bg);color:var(--fg);font-size:15px}
#t::placeholder{color:#475569}
.row{display:flex;gap:8px}
.btn{flex:1;padding:11px 0;border-radius:10px;border:1px solid transparent;font-weight:600}
#go{background:var(--acc);color:var(--accd)}
#go:hover{background:#4ade80}
#aib{background:none;border-color:var(--bd);color:var(--fg)}
#aib:hover{border-color:var(--acc);color:var(--acc)}
#clr{background:none;border:none;color:var(--red);font-weight:500;padding:8px;align-self:center}
#clr:hover{opacity:.75}
#chips{display:flex;flex-wrap:wrap;gap:6px;min-height:30px}
.chip{background:var(--s2);border:1px solid var(--bd);border-radius:999px;
      padding:5px 12px;font-size:13px;color:var(--fg)}
#f{margin:0;color:var(--acc);font-size:13px;font-family:ui-monospace,monospace;min-height:18px}
details{border:1px solid var(--bd);border-radius:10px;padding:10px 12px;font-size:13px;color:var(--mut)}
summary{cursor:pointer;color:var(--fg);font-weight:600;font-size:13px}
details p{margin:8px 0 0;line-height:1.6}
details b{color:var(--fg);font-weight:600}
main{flex:1;display:flex;align-items:center;justify-content:center;background:#000;min-width:0}
#v{max-width:100%;max-height:100dvh;min-height:200px}
@media (max-width:700px){#sb{position:fixed;inset:0 auto 0 0;z-index:40;box-shadow:8px 0 24px #000c}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
<body>
<button id=burger aria-label="Toggle details sidebar" onclick="document.body.classList.toggle('closed')">
<svg width=20 height=20 viewBox="0 0 24 24" fill=none stroke=currentColor stroke-width=2 stroke-linecap=round>
<path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
<aside id=sb>
<h1>AEROMED <span>VISION</span></h1>
<p class=sub>Describe the target. Any detail alone works.</p>
<form onsubmit="send(event)">
<input id=t placeholder="red top, black bottom, waving, next to a red car" autocomplete=off>
<div class=row style="margin-top:10px">
<button class=btn id=go>Set target</button>
<button class=btn id=aib type=button onclick="ai()">AI search &beta;</button>
</div>
<button id=clr type=button onclick="reset()">clear filter</button>
</form>
<div id=chips></div>
<p id=f>looking for: ...</p>
<details><summary>Vocabulary</summary>
<p><b>colours</b> red orange yellow green blue purple white black grey<br>
<b>top</b> top / shirt / jacket / hoodie...<br>
<b>bottom</b> bottom / trousers / jeans / shorts...<br>
<b>posture</b> waving &middot; lying<br>
<b>objects</b> next to a car / vehicle / bike / dog / backpack...<br><br>
<b>Set target</b> = instant, flies on the Pi.<br>
<b>AI search</b> = any phrase, slower (demo mode).</p>
</details>
</aside>
<main><img id=v alt="live camera feed with detections"></main>
<script>
function setF(t){document.getElementById('f').textContent='looking for: '+t;
 const c=document.getElementById('chips');c.innerHTML='';
 if(t && !t.startsWith('none'))t.split(', ').forEach(x=>{
  const s=document.createElement('span');s.className='chip';s.textContent=x;c.appendChild(s);});}
async function post(v,path){const r=await fetch(path||'/prompt',{method:'POST',body:v});setF(await r.text());}
function send(e){e.preventDefault();post(document.getElementById('t').value);}
function ai(){document.getElementById('f').textContent='loading AI model (first time ~20s)...';
 post(document.getElementById('t').value,'/world');}
function reset(){document.getElementById('t').value='';post('');}
const img=document.getElementById('v');
async function tick(){
 try{const r=await fetch('/frame');const b=await r.blob();
  const u=URL.createObjectURL(b);img.onload=()=>URL.revokeObjectURL(u);img.src=u;
 }catch(e){}
 setTimeout(tick,66);}
window.onload=async()=>{tick();const r=await fetch('/filter');setF(await r.text());};
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
            if MODE == "world" and WORLD is not None:
                with WLOCK:
                    r = WORLD(frame, conf=0.2, verbose=False)[0]
                annotate_world(frame, r, WORLD_LABEL)
            else:
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
        global SPEC, MODE, WORLD, WORLD_LABEL, WAVERS
        text = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
        if self.path == "/world" and _phrases(text):
            phrases = _phrases(text)
            with WLOCK:
                if WORLD is None:
                    from ultralytics import YOLOWorld  # first call: loads/downloads model
                    WORLD = YOLOWorld("yolov8s-worldv2.pt")
                WORLD.set_classes(phrases)
            WORLD_LABEL = ", ".join(phrases)
            MODE = "world"
            msg = f"AI search: {WORLD_LABEL}"
        else:
            with LOCK:
                SPEC = parse(text, OBJECT_NAMES)
                WAVERS = {"L": wv.WaveDetector(), "R": wv.WaveDetector()}  # fresh wave history
                msg = describe(SPEC)
            MODE = "kw"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(msg.encode())

    def do_GET(self):
        if self.path == "/filter":
            with LOCK:
                msg = f"AI search: {WORLD_LABEL}" if MODE == "world" else describe(SPEC)
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
    print(f"AeroMed Vision: http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def selfcheck():
    empty = {"upper": [], "lower": [], "objects": [], "posture": []}
    s = parse("individual is wearing a red shirt and blue trousers", {"car"})
    assert s["upper"] == ["red"] and s["lower"] == ["blue"] and not s["objects"], s
    s = parse("person next to a red car", {"car"})
    assert s["objects"] == [("red", "car")] and not s["upper"], s
    assert parse("wearing red", {"car"})["upper"] == ["red"]
    assert parse("next to a car", {"car"})["objects"] == [(None, "car")]
    assert parse("", {"car"}) == empty
    # every part is optional, and the words the UI suggests all parse
    assert parse("white top", {"car"}) == dict(empty, upper=["white"])
    assert parse("blue bottom", {"car"}) == dict(empty, lower=["blue"])
    assert parse("black bottoms", {"car"})["lower"] == ["black"]
    assert parse("next to a yellow vehicle", {"car"})["objects"] == [("yellow", "vehicle")]
    # postures parse alone or alongside anything else
    assert parse("waving", {"car"}) == dict(empty, posture=["waving"])
    assert parse("laying down", {"car"}) == dict(empty, posture=["lying"])
    s = parse("red top, waving", {"car"})
    assert s["upper"] == ["red"] and s["posture"] == ["waving"], s
    assert "waving" in describe(s) and "red top" in describe(s)

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
    assert person_matches(person, box, dict(empty, upper=["red"], lower=["blue"]))
    assert not person_matches(person, box, dict(empty, upper=["green"]))
    # partial specs judge only the part given
    assert person_matches(person, box, dict(empty, upper=["red"]))
    assert person_matches(person, box, dict(empty, lower=["blue"]))
    assert not person_matches(person, box, dict(empty, lower=["green"]))
    # lying: wide box passes, upright box fails
    wide = np.zeros((100, 200, 3), np.uint8)
    assert person_matches(wide, (0, 0, 200, 100), dict(empty, posture=["lying"]))
    assert not person_matches(person, box, dict(empty, posture=["lying"]))

    # desk view: only chest-up visible — keypoints place the shirt correctly
    desk = np.zeros((200, 100, 3), np.uint8)
    desk[:100] = (0, 255, 0)      # head-height clutter the box heuristic would judge
    desk[100:] = (255, 255, 255)  # the actual white shirt
    kxy, kc = [[50, 0]] * 17, [0.0] * 17
    kxy[L_SH], kxy[R_SH] = [20, 100], [80, 100]
    kc[L_SH] = kc[R_SH] = 0.9     # shoulders seen; hips/knees below the frame
    spec = dict(empty, upper=["white"], lower=["blue"])
    assert person_matches(desk, box, spec, kxy, kc)  # shirt matches; unseen trousers don't veto
    assert not person_matches(desk, box, spec)       # box heuristic alone judges the clutter

    frame = np.zeros((300, 400, 3), np.uint8)
    frame[0:60, 150:250] = (0, 0, 255)             # a red car-sized blob
    objs = {"car": [(150, 0, 250, 60)]}
    assert objects_ok(frame, objs, [("red", "car")], (100, 100, 140, 200))       # near
    assert not objects_ok(frame, objs, [("blue", "car")], (100, 100, 140, 200))  # wrong colour
    assert not objects_ok(frame, objs, [("red", "car")], (0, 250, 20, 290))      # too far
    assert not objects_ok(frame, {}, [("red", "car")], (100, 100, 140, 200))     # no car at all
    assert objects_ok(frame, {"truck": objs["car"]}, [("red", "vehicle")], (100, 100, 140, 200))

    assert _phrases("white shirt, next to a yellow vehicle") == ["white shirt", "a yellow vehicle"]
    assert _phrases("red jacket and a dog") == ["red jacket", "a dog"]
    assert _phrases("") == []
    print("selfcheck OK")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse local model files
    p = argparse.ArgumentParser()
    p.add_argument("port", nargs="?", type=int, default=8010)
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    selfcheck() if a.selfcheck else main(a.port)
