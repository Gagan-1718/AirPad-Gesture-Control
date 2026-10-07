"""MediaPipe hand tracking (Tasks HandLandmarker API, MediaPipe >= 0.10).

The legacy `mp.solutions.hands` API was removed from recent MediaPipe
releases, so this uses HandLandmarker in VIDEO mode, which tracks the hand
between frames instead of re-running palm detection every time.
"""
import os
import time
import urllib.request
from dataclasses import dataclass

os.environ.setdefault("GLOG_minloglevel", "2")       # hide MediaPipe's startup log noise
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

import config

HAND_CONNECTIONS = [(c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS]


@dataclass
class Hand:
    points: list        # 21 (x, y) landmark positions in pixels
    frame_w: int
    frame_h: int
    handedness: str     # "Left" / "Right" (correct for a mirrored frame)
    score: float

    def norm(self, index):
        """Landmark position as a fraction of the frame (0..1)."""
        x, y = self.points[index]
        return x / self.frame_w, y / self.frame_h


def ensure_model(path=config.MODEL_PATH, url=config.MODEL_URL):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading hand model to {path} ...")
    tmp = path + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, path)


class HandTracker:
    def __init__(self):
        ensure_model()
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=config.MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.NUM_HANDS,
            min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_PRESENCE_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_ts = -1

    def process(self, frame_bgr):
        """Return the first detected Hand, or None."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        # VIDEO mode requires strictly increasing timestamps.
        ts = max(int(time.monotonic() * 1000), self._last_ts + 1)
        self._last_ts = ts
        result = self._landmarker.detect_for_video(image, ts)
        if not result.hand_landmarks:
            return None
        h, w = frame_bgr.shape[:2]
        points = [(lm.x * w, lm.y * h) for lm in result.hand_landmarks[0]]
        category = result.handedness[0][0]
        return Hand(points, w, h, category.category_name, category.score)

    def close(self):
        self._landmarker.close()
