"""Gesture recognition: finger states, static gestures and hand motion."""
import math
from collections import Counter, deque

import config

WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_TIP = 8
MIDDLE_MCP = 9
PINKY_MCP = 17
FINGER_TIPS = (8, 12, 16, 20)   # index, middle, ring, pinky
FINGER_PIPS = (6, 10, 14, 18)

# (index, middle, ring, pinky) -> pose. Fist is split by the thumb in classify().
PATTERNS = {
    (1, 1, 1, 1): "palm",
    (1, 0, 0, 0): "point",
    (1, 1, 0, 0): "two",
    (1, 1, 1, 0): "three",
}

DISPLAY_NAMES = {
    "palm": "Open palm",
    "fist": "Fist",
    "point": "Point",
    "two": "Two fingers",
    "three": "Three fingers",
    "thumb_up": "Thumbs up",
    "thumb_down": "Thumbs down",
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


def classify(hand, fingers):
    key = tuple(fingers[1:])
    if key == (0, 0, 0, 0):
        pts = hand.points
        size = hand_size(hand) or 1e-6
        # Thumbs up/down: thumb out, pointing up or down, and not pinching the index.
        if fingers[0] and _dist(pts[THUMB_TIP], pts[INDEX_TIP]) > 0.5 * size:
            rise = (pts[THUMB_TIP][1] - pts[THUMB_MCP][1]) / size
            if rise < -config.THUMB_VERTICAL:
                return "thumb_up"
            if rise > config.THUMB_VERTICAL:
                return "thumb_down"
        return "fist"
    return PATTERNS.get(key, "other")


class MotionTracker:
    """Wrist position history for swipe and stillness detection."""

    def __init__(self):
        self._history = deque()     # (t, x, y, pose) with x, y in frame fractions
        self._first_seen = None
        self._keep_s = max(config.SWIPE_WINDOW_S, config.STILL_WINDOW_S)

    def reset(self):
        self._history.clear()
        self._first_seen = None

    def clear_history(self):
        """Forget past motion but keep the hand armed (used after a swipe)."""
        self._history.clear()

    def update(self, now, x, y, pose):
        if self._first_seen is None:
            self._first_seen = now
        self._history.append((now, x, y, pose))
        while self._history and now - self._history[0][0] > self._keep_s:
            self._history.popleft()

    def _recent(self, now, window_s):
        return [s for s in self._history if now - s[0] <= window_s]

    def detect_swipe(self, now):
        """Return (direction, pose) for a swipe, else None.

        direction is "swipe_left" / "swipe_right"; pose is the hand shape held
        during most of the swipe (blurry frames mid-swipe are outvoted).
        """
        if self._first_seen is None:
            return None
        armed_at = self._first_seen + config.SWIPE_ARM_S
        samples = [s for s in self._recent(now, config.SWIPE_WINDOW_S) if s[0] >= armed_at]
        if len(samples) < 3:
            return None
        _, x_now, y_now, _ = samples[-1]
        lowest = min(samples, key=lambda s: s[1])
        highest = max(samples, key=lambda s: s[1])

        for direction, start, dx in (("swipe_right", lowest, x_now - lowest[1]),
                                     ("swipe_left", highest, highest[1] - x_now)):
            dy = abs(y_now - start[2])
            if dx > config.SWIPE_THRESHOLD and dy < config.SWIPE_MAX_SLOPE * dx:
                poses = Counter(s[3] for s in samples if s[3] is not None)
                pose = poses.most_common(1)[0][0] if poses else None
                return direction, pose
        return None

    def is_still(self, now):
        samples = self._recent(now, config.STILL_WINDOW_S)
        if len(samples) < 2:
            return False
        xs = [s[1] for s in samples]
        ys = [s[2] for s in samples]
        return max(xs) - min(xs) < config.STILL_THRESHOLD and max(ys) - min(ys) < config.STILL_THRESHOLD
