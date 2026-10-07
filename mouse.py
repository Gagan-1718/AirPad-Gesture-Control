"""Mouse mode: move the cursor with your hand.

The cursor follows the index-finger knuckle (landmark 5), not the fingertip,
so it stays steady while the fingers move.
"""
import pyautogui

import config
from smoothing import OneEuroFilter

INDEX_MCP = 5


class MouseController:
    def __init__(self, output):
        self._out = output
        self._screen_w, self._screen_h = pyautogui.size()
        self._fx = OneEuroFilter(config.MOUSE_SMOOTH_MIN_CUTOFF, config.MOUSE_SMOOTH_BETA)
        self._fy = OneEuroFilter(config.MOUSE_SMOOTH_MIN_CUTOFF, config.MOUSE_SMOOTH_BETA)
        self._last_pos = None

    def release(self):
        """Forget the hand (hand lost, mode change, quit)."""
        self._fx.reset()
        self._fy.reset()
        self._last_pos = None

    def update(self, now, hand, gesture, fingers):
        """Feed one frame. gesture: stable gesture or None. Returns an event label or None."""
        if gesture == "three":
            return None         # hold still so the mode switch can complete
        self._move(now, hand)
        return None

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
