"""Browser preview of the AeroMed CV pipeline — MJPEG over stdlib http.server.

Run:  .venv/bin/python stream.py            (target: person, port 8000)
      .venv/bin/python stream.py cup 8001
Open: http://localhost:8000

Same detection/targeting as detect.py (imported), just streamed to a tab
instead of a native window. No extra dependencies beyond opencv + ultralytics.
"""
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

import detect

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # reuse the local yolov8n.pt

TARGET = sys.argv[1] if len(sys.argv) > 1 else "person"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000

model, want = detect.load(TARGET)

cap = cv2.VideoCapture(0)
ok = cap.isOpened() and cap.read()[0]
if ok:
    MODE = "live"
else:
    cap.release()
    cap = None
    MODE = "demo"
    from ultralytics.utils import ASSETS
    _img = cv2.imread(str(ASSETS / "zidane.jpg"))
    detect.annotate(_img, model, want, TARGET)
    cv2.putText(_img, "DEMO (no camera - grant access & restart for live)",
                (10, _img.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    DEMO_JPG = cv2.imencode(".jpg", _img)[1].tobytes()

PAGE = f"""<!doctype html><meta charset=utf-8><title>AeroMed CV</title>
<body style="margin:0;background:#111;color:#eee;font-family:system-ui;text-align:center">
<p>AeroMed CV — target: <b>{TARGET}</b></p>
<img src="/stream" style="max-width:100%;height:auto">
""".encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

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
                if MODE == "demo":
                    jpg = DEMO_JPG
                    time.sleep(0.5)
                else:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    detect.annotate(frame, model, want, TARGET)
                    ok, buf = cv2.imencode(".jpg", frame)
                    if not ok:
                        continue
                    jpg = buf.tobytes()
                self.wfile.write(b"--f\r\nContent-Type: image/jpeg\r\n\r\n")
                self.wfile.write(jpg)
                self.wfile.write(b"\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass


print(f"AeroMed CV preview: http://localhost:{PORT}  (target: {TARGET})")
ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
