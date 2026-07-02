"""AeroMed Phase 1.5 — threaded capture (gap 5).

cv2.VideoCapture buffers frames internally. A naive read->infer->repeat loop
on slow hardware (Pi 5: ~200-300 ms per YOLO frame) therefore processes OLD
buffered frames — the drone reacts to where the target WAS, and the lag
compounds. The fix is one background thread that always overwrites a single
slot with the newest frame; the inference loop asks for "now", never a queue.

Bench:     .venv/bin/python camera.py --bench      (webcam + fake Pi-speed inference)
Selfcheck: .venv/bin/python camera.py --selfcheck  (no camera needed)
"""
import argparse
import threading
import time


class VideoStream:
    """Background thread keeps only the newest frame; read() never queues.

    Works with anything shaped like cv2.VideoCapture — read() -> (ok, frame)
    and release() — so the Pi camera wrapper (or a test stub) drops in later.
    """

    def __init__(self, cap):
        self.cap = cap
        self.lock = threading.Lock()
        self.frame = None
        self.ts = 0.0                 # when the current frame was captured
        self.ok = True
        self.stopped = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stopped:
            ok, frame = self.cap.read()
            if not ok:
                self.ok = False
                break
            with self.lock:
                self.frame, self.ts = frame, time.time()

    def read(self):
        """Latest frame (a copy), or None if nothing captured yet / camera died."""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy() if hasattr(self.frame, "copy") else self.frame

    def stop(self):
        self.stopped = True
        self.thread.join(timeout=1)
        self.cap.release()


def bench(infer_s=0.25, n=15):
    import cv2
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Camera won't open. System Settings > Privacy & Security > Camera.")
    cap.read()  # warm up

    # NAIVE: sleep = pretend YOLO ran, then time the next read.
    # An "instant" read (<5 ms) means the camera served a buffered frame that
    # was captured BEFORE inference started — i.e. you just processed the past.
    instant = 0
    for _ in range(n):
        time.sleep(infer_s)
        t0 = time.time()
        cap.read()
        instant += (time.time() - t0) < 0.005
    cap.release()

    # THREADED: how old is the frame at the moment inference would start?
    vs = VideoStream(cv2.VideoCapture(0))
    while vs.read() is None:
        time.sleep(0.01)
    ages = []
    for _ in range(n):
        time.sleep(infer_s)
        vs.read()
        ages.append(time.time() - vs.ts)
    vs.stop()

    print(f"naive:    {instant}/{n} reads served a stale buffered frame after "
          f"{infer_s * 1000:.0f} ms of fake inference")
    print("          (macOS keeps its buffer small — on the Pi's V4L2 stack the backlog is real)")
    print(f"threaded: frame is {1000 * sum(ages) / len(ages):.0f} ms old on average when "
          f"inference starts — always at most one camera interval behind")


def selfcheck():
    class FakeCap:  # frames are just an incrementing counter
        def __init__(self):
            self.i, self.released = 0, False

        def read(self):
            self.i += 1
            time.sleep(0.001)
            return True, self.i

        def release(self):
            self.released = True

    vs = VideoStream(FakeCap())
    time.sleep(0.05)
    seen = []
    for _ in range(5):
        time.sleep(0.03)  # simulate slow inference between reads
        seen.append(vs.read())
    vs.stop()
    assert seen == sorted(seen), seen            # time always moves forward
    assert seen[-1] - seen[0] > len(seen), seen  # frames were SKIPPED: latest-only, no backlog
    assert vs.cap.released
    print("selfcheck OK")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bench", action="store_true")
    p.add_argument("--selfcheck", action="store_true")
    a = p.parse_args()
    bench() if a.bench else selfcheck()
