"""Gesture recognition: finger states and static gestures."""
import math

import config

WRIST = 0
THUMB_IP, THUMB_TIP = 3, 4
MIDDLE_MCP = 9
PINKY_MCP = 17
FINGER_TIPS = (8, 12, 16, 20)   # index, middle, ring, pinky
FINGER_PIPS = (6, 10, 14, 18)


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
