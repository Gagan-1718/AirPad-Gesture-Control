"""Gesture recognition: finger states and static gestures."""
import math

WRIST = 0
MIDDLE_MCP = 9


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def hand_size(hand):
    """Wrist -> middle-finger base, in pixels. Used to normalise distances."""
    return _dist(hand.points[WRIST], hand.points[MIDDLE_MCP])
