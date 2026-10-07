"""Gesture recognition: finger states, static gestures and hand motion."""
import math
from collections import deque

import config

WRIST = 0
THUMB_IP, THUMB_TIP = 3, 4
MIDDLE_MCP = 9
PINKY_MCP = 17
FINGER_TIPS = (8, 12, 16, 20)   # index, middle, ring, pinky
FINGER_PIPS = (6, 10, 14, 18)

# (index, middle, ring, pinky) -> gesture. The thumb is deliberately ignored:
# it is the least reliable landmark and none of these shapes need it.
PATTERNS = {
    (1, 1, 1, 1): "palm",
    (0, 0, 0, 0): "fist",
    (1, 0, 0, 0): "one",
    (1, 1, 0, 0): "two",
    (1, 1, 1, 0): "three",
}

DISPLAY_NAMES = {
    "palm": "Open palm",
    "fist": "Fist",
    "one": "Index up",
    "two": "Two fingers",
    "three": "Three fingers",
    "other": "Unknown",
    "swipe_left": "Swipe left",
    "swipe_right": "Swipe right",
}


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(hand):
    """Wrist -> middle-finger base, in pixels. Used to normalise distances."""
    return _dist(hand.points[WRIST], hand.points[MIDDLE_MCP])


def fingers_up(hand):
    """Return [thumb, index, middle, ring, pinky] as 0/1 values."""
    pts = hand.points
    size = hand_size(hand) or 1e-6
    wrist = pts[WRIST]

    # Thumb: tip further from the pinky base than its IP joint, and clearly
    # away from the palm. Works for both hands without a Left/Right flip.
    thumb = (_dist(pts[THUMB_TIP], pts[PINKY_MCP]) > _dist(pts[THUMB_IP], pts[PINKY_MCP])
             and _dist(pts[THUMB_TIP], pts[MIDDLE_MCP]) > config.THUMB_OUT_RATIO * size)

    others = [_dist(pts[tip], wrist) > config.FINGER_EXTENDED_RATIO * _dist(pts[pip], wrist)
              for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)]
    return [int(thumb)] + [int(f) for f in others]


def classify(fingers):
    return PATTERNS.get(tuple(fingers[1:]), "other")


class MotionTracker:
    """Wrist position history over the last SWIPE_WINDOW_S seconds."""

    def __init__(self):
        self._history = deque()     # (t, x, y) in frame fractions
        self._first_seen = None

    def reset(self):
        self._history.clear()
        self._first_seen = None

    def clear_history(self):
        """Forget past motion but keep the hand armed (used after a swipe)."""
        self._history.clear()

    def update(self, now, x, y):
        if self._first_seen is None:
            self._first_seen = now
        self._history.append((now, x, y))
        while self._history and now - self._history[0][0] > config.SWIPE_WINDOW_S:
            self._history.popleft()

    def _recent(self, now, window_s):
        return [s for s in self._history if now - s[0] <= window_s]

    def detect_swipe(self, now):
        """Return "swipe_left", "swipe_right" or None."""
        if self._first_seen is None:
            return None
        armed_at = self._first_seen + config.SWIPE_ARM_S
        samples = [s for s in self._recent(now, config.SWIPE_WINDOW_S) if s[0] >= armed_at]
        if len(samples) < 3:
            return None
        _, x_now, y_now = samples[-1]
        lowest = min(samples, key=lambda s: s[1])
        highest = max(samples, key=lambda s: s[1])

        for direction, start, dx in (("swipe_right", lowest, x_now - lowest[1]),
                                     ("swipe_left", highest, highest[1] - x_now)):
            dy = abs(y_now - start[2])
            if dx > config.SWIPE_THRESHOLD and dy < config.SWIPE_MAX_SLOPE * dx:
                return direction
        return None
