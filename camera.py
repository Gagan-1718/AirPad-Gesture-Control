"""Webcam capture on a background thread, so the app always gets the newest frame.

The thread keeps draining the camera (grab is cheap) and only decodes a frame
when one is requested, so no stale frames pile up in the driver's buffer.
"""
import sys
import threading

import cv2

import config


class Camera:
    def __init__(self, index):
        # DirectShow opens much faster than the default MSMF backend on Windows.
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            raise SystemExit(f"Could not open camera {index}. Is another app using it?")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap = cap
        self._want = threading.Event()
        self._ready = threading.Event()
        self._frame = None
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._running:
            if not self._cap.grab():
                break
            if self._want.is_set():
                ok, frame = self._cap.retrieve()
                if ok:
                    self._frame = frame
                    self._want.clear()
                    self._ready.set()
        self._running = False
        self._ready.set()           # wake a waiting read() so it can report failure

    def read(self, timeout=2.0):
        """Return the next fresh frame, or None if the camera stopped."""
        self._ready.clear()
        self._want.set()
        if not self._ready.wait(timeout) or not self._running:
            return None
        return self._frame

    def close(self):
        self._running = False
        self._thread.join(timeout=1.0)
        self._cap.release()
