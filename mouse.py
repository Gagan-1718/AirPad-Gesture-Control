"""Mouse mode: move the cursor with your hand, pinch to click.

- Cursor follows the index-finger knuckle (landmark 5), not the fingertip,
  so the cursor does not jump when you pinch.
- Thumb + index pinch = left button down; open = button up (so hold = drag).
- Thumb + middle pinch with index up = right click.
- Three fingers: cursor freezes so you can hold still to switch mode.
"""
import math

import pyautogui

import config
from gestures import hand_size
from smoothing import OneEuroFilter

WRIST, THUMB_TIP, INDEX_MCP = 0, 4, 5
INDEX_PIP, INDEX_TIP, MIDDLE_PIP, MIDDLE_TIP = 6, 8, 10, 12


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _reaching(pts, tip, pip):
    """True if the finger is out towards the thumb, not curled into the palm.

    Stops a fist (or a pointing hand with the thumb resting on the curled
    middle finger) from counting as a pinch.
    """
    return _dist(pts[tip], pts[WRIST]) > config.PINCH_MIN_REACH * _dist(pts[pip], pts[WRIST])


class MouseController:
    def __init__(self, output):
        self._out = output
        self._screen_w, self._screen_h = pyautogui.size()
        self._fx = OneEuroFilter(config.MOUSE_SMOOTH_MIN_CUTOFF, config.MOUSE_SMOOTH_BETA)
        self._fy = OneEuroFilter(config.MOUSE_SMOOTH_MIN_CUTOFF, config.MOUSE_SMOOTH_BETA)
        self._button_down = False
        self._pinch_frames = 0
        self._right_pinched = False
        self._last_pos = None

    def release(self):
        """Let go of everything (hand lost, mode change, quit). Never leaves a stuck button."""
        if self._button_down:
            self._out.mouse_up()
            self._button_down = False
        self._pinch_frames = 0
        self._right_pinched = False
        self._fx.reset()
        self._fy.reset()
        self._last_pos = None

    def update(self, now, hand, gesture, fingers):
        """Feed one frame. gesture: stable gesture or None. Returns an event label or None."""
        pts = hand.points
        size = hand_size(hand) or 1e-6
        pinch = _dist(pts[THUMB_TIP], pts[INDEX_TIP]) / size
        right = _dist(pts[THUMB_TIP], pts[MIDDLE_TIP]) / size
        if not _reaching(pts, INDEX_TIP, INDEX_PIP):
            pinch = max(pinch, config.PINCH_OFF + 1e-3)   # curled: not a pinch
        if not _reaching(pts, MIDDLE_TIP, MIDDLE_PIP):
            right = max(right, config.PINCH_OFF + 1e-3)

        if not self._button_down and gesture == "three":
            self._pinch_frames = 0
            return None         # hold still so the mode switch can complete

        self._move(now, hand)
        return self._buttons(pinch, right, fingers)

    def _move(self, now, hand):
        nx, ny = hand.norm(INDEX_MCP)
        x0, y0, x1, y1 = config.MOUSE_BOX
        sx = min(max((nx - x0) / (x1 - x0), 0.0), 1.0) * (self._screen_w - 1)
        sy = min(max((ny - y0) / (y1 - y0), 0.0), 1.0) * (self._screen_h - 1)
        x = int(self._fx(now, sx))
        y = int(self._fy(now, sy))
        if (x, y) != self._last_pos:
            self._out.move(x, y)
            self._last_pos = (x, y)

    def _buttons(self, pinch, right, fingers):
        if self._button_down:
            if pinch > config.PINCH_OFF:
                self._out.mouse_up()
                self._button_down = False
            return None

        # Right click: thumb on middle fingertip while the index stays up.
        if fingers[1] and right < config.PINCH_ON and pinch > config.PINCH_ON:
            if not self._right_pinched:
                self._right_pinched = True
                self._out.right_click()
                return "Right click"
            return None
        if right > config.PINCH_OFF:
            self._right_pinched = False

        # Left button: thumb closer to the index tip than to the middle tip.
        if pinch < config.PINCH_ON and pinch < right:
            self._pinch_frames += 1
            if self._pinch_frames >= config.PINCH_FRAMES:
                self._pinch_frames = 0
                self._button_down = True
                self._out.mouse_down()
                return "Click"
        else:
            self._pinch_frames = 0
        return None
