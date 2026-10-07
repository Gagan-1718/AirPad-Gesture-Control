"""Gesture recognition: finger states and static gestures."""
import math

import config

WRIST = 0
MIDDLE_MCP = 9
FINGER_TIPS = (8, 12, 16, 20)   # index, middle, ring, pinky
FINGER_PIPS = (6, 10, 14, 18)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(hand):
    """Wrist -> middle-finger base, in pixels. Used to normalise distances."""
    return _dist(hand.points[WRIST], hand.points[MIDDLE_MCP])


def fingers_up(hand):
    """Return [index, middle, ring, pinky] as 0/1 values."""
    pts = hand.points
    wrist = pts[WRIST]
    return [int(_dist(pts[tip], wrist) > config.FINGER_EXTENDED_RATIO * _dist(pts[pip], wrist))
            for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)]
