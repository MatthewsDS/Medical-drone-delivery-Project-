"""AeroMed demo hub — click a button to run any demo. No terminal typing.

Start it once (either way):
  - double-click  start_aeromed.command   (opens the page for you), or
  - .venv/bin/python hub.py
Then use:  http://localhost:8080

One demo runs at a time (they share the single webcam). Camera demos open
their own window — press q in that window to close it. Text demos print into
the page. Any error (e.g. camera permission) shows in the output box too.

Selfcheck: .venv/bin/python hub.py --selfcheck   (no camera needed)
"""
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, ".venv", "bin", "python")
LOG = os.path.join(HERE, ".hub_last_output.txt")

# key -> (label, argv, what-to-expect note, weblink or None)
DEMOS = {
    "target_chat": ("Target chat — describe who to find", ["target_chat.py"],
                    "starts a web page — click the link that appears", "http://localhost:8010"),
    "waving": ("Wave detection", ["waving.py"],
               "a camera window opens — press q to close it", None),
    "altitude": ("Altitude simulator (w = climb, s = descend)", ["altitude.py"],
                 "camera window — press q to close", None),
    "aruco": ("ArUco landing marker", ["aruco_landing.py"],
              "camera window — show marker_0.png, press q to close", None),
    "mission": ("Full mission demo", ["mission.py", "--live"],
                "camera window — wave or show the marker; r resets, q closes", None),
    "detect": ("Basic detection", ["detect.py"],
               "camera window — press q to close", None),
    "altitude_sweep": ("Altitude range table (text)", ["altitude.py", "--sweep"],
                       "stand back — a table prints in the output box below", None),
    "camera_bench": ("Threading benchmark (text)", ["camera.py", "--bench"],
                     "numbers print in the output box below", None),
}

_proc = None
_lock = threading.Lock()


def _stop():
    global _proc
    with _lock:
        if _proc and _proc.poll() is None:
            _proc.terminate()
            try:
                _proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _proc.kill()
        _proc = None


def _run(argv):
    global _proc
    _stop()  # the webcam can't be shared — always one demo at a time
    with _lock:
        _proc = subprocess.Popen([PY] + argv, cwd=HERE,
                                 stdout=open(LOG, "w"), stderr=subprocess.STDOUT)


def _page():
    rows = "".join(
        f'<button onclick="run(\'{k}\')" '
        f'style="display:block;width:100%;text-align:left;margin:6px 0;padding:12px 14px;'
        f'font-size:15px;border:0;border-radius:8px;background:#1e293b;color:#e2e8f0;cursor:pointer">'
        f'<b>{lbl}</b><br><span style="color:#94a3b8;font-size:13px">{note}</span></button>'
        for k, (lbl, _a, note, _w) in DEMOS.items())
    return f"""<!doctype html><meta charset=utf-8><title>AeroMed demos</title>
<body style="margin:0;background:#0f172a;color:#e2e8f0;font-family:system-ui;max-width:640px;margin:auto;padding:20px">
<h2>AeroMed — CV demos</h2>
<p style="color:#94a3b8">Click one. It replaces whatever was running (they share the webcam).</p>
{rows}
<button onclick="stop()" style="width:100%;margin:12px 0;padding:12px;border:0;border-radius:8px;background:#7f1d1d;color:#fff;cursor:pointer">stop current demo</button>
<p id=s style="color:#38bdf8;min-height:24px"></p>
<pre id=o style="background:#020617;padding:12px;border-radius:8px;white-space:pre-wrap;max-height:260px;overflow:auto"></pre>
<script>
const NOTE={{ {", ".join(f'{k}:{{n:{note!r},w:{w!r}}}' for k,(_l,_a,note,w) in DEMOS.items())} }};
async function run(k){{await fetch('/run?d='+k,{{method:'POST'}});
 const d=NOTE[k];let m=d.n;if(d.w)m+=' → <a href="'+d.w+'" target="_blank" style="color:#38bdf8">open '+d.w+'</a>';
 document.getElementById('s').innerHTML='started: '+m;}}
async function stop(){{await fetch('/stop',{{method:'POST'}});document.getElementById('s').textContent='stopped';}}
async function poll(){{try{{const r=await fetch('/log');document.getElementById('o').textContent=await r.text();}}catch(e){{}}setTimeout(poll,1000);}}
poll();
</script>""".encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="text/plain"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else body.encode())

    def do_POST(self):
        p = urlparse(self.path)
        if p.path == "/run":
            key = parse_qs(p.query).get("d", [""])[0]
            if key in DEMOS:
                _run(DEMOS[key][1])
                self._send("ok")
            else:
                self.send_error(404)
        elif p.path == "/stop":
            _stop()
            self._send("ok")
        else:
            self.send_error(404)

    def do_GET(self):
        if urlparse(self.path).path == "/log":
            try:
                with open(LOG) as f:
                    self._send(f.read()[-4000:])
            except FileNotFoundError:
                self._send("")
        else:
            self._send(_page(), "text/html")


def main(port=8080):
    if not os.path.exists(PY):
        sys.exit(f"venv not found at {PY} — run: python3 -m venv .venv && "
                 ".venv/bin/python -m pip install -r requirements.txt")
    print(f"AeroMed demo hub: http://localhost:{port}")
    try:
        ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
    finally:
        _stop()


def selfcheck():
    import time
    for k, (lbl, argv, note, w) in DEMOS.items():
        assert os.path.exists(os.path.join(HERE, argv[0])), f"{k}: missing {argv[0]}"
        assert lbl and note, k
    assert b"AeroMed" in _page() and b"stop current demo" in _page()
    # end-to-end: launch a real no-camera child via the same machinery, capture its stdout
    _run(["detect.py", "--selfcheck"])
    for _ in range(50):
        time.sleep(0.1)
        if os.path.exists(LOG) and "selfcheck OK" in open(LOG).read():
            break
    else:
        raise AssertionError("child did not produce expected output via hub")
    _stop()
    print("selfcheck OK")


if __name__ == "__main__":
    selfcheck() if "--selfcheck" in sys.argv else main()
