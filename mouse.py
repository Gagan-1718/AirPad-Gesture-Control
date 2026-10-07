"""Mouse control: move the cursor with your hand, pinch to click, two fingers to scroll.

- Point (index up) and move: the cursor follows your hand.
- Fist (or hand out of view): the cursor stays put.
- Thumb + index pinch = left button down; open = button up (so hold = drag).
- Thumb + middle pinch with index up = right click.
- Two fingers up (index + middle): cursor freezes, move hand up/down to scroll.
The cursor follows the index-finger knuckle (landmark 5), not the fingertip,
so the cursor does not jump when you pinch.
"""
import math

import pyautogui

import config
from gestures import hand_size
from smoothing import OneEuroFilter

WRIST, THUMB_TIP, INDEX_MCP = 0, 4, 5
INDEX_PIP, INDEX_TIP, MIDDLE_PIP, MIDDLE_TIP = 6, 8, 10, 12
EDGE = 2   # keep off the exact screen corners (pyautogui fail-safe zone)

MOVE_POSES = {"point", "other"}
FREEZE_POSES = {"fist", "palm", "two", "three", "thumb_up", "thumb_down"}
NO_CLICK_POSES = {"palm", "two", "three", "thumb_up", "thumb_down"}


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
        self._moving = False          # current pose drives the cursor
        self._button_down = False
        self._pinch_frames = 0
        self._right_pinched = False
        self._scroll_y = None
        self._scroll_rest = 0.0
        self._last_pos = None

    def release(self):
        """Let go of everything (hand lost, quit). Never leaves a stuck button."""
        if self._button_down:
            self._out.mouse_up()
            self._button_down = False
        self._moving = False
        self._pinch_frames = 0
        self._right_pinched = False
        self._scroll_y = None
        self._scroll_rest = 0.0
        self._lift()

    def _lift(self):
        """Stop following the hand until the pointing pose comes back."""
        self._fx.reset()
        self._fy.reset()
        self._last_pos = None

    def update(self, now, hand, pose, fingers):
        """Feed one frame. pose: stable pose or None. Returns an event label or None."""
        pts = hand.points
        size = hand_size(hand) or 1e-6
        pinch = _dist(pts[THUMB_TIP], pts[INDEX_TIP]) / size
        right = _dist(pts[THUMB_TIP], pts[MIDDLE_TIP]) / size
        if not _reaching(pts, INDEX_TIP, INDEX_PIP):
            pinch = max(pinch, config.PINCH_OFF + 1e-3)   # curled: not a pinch
        if not _reaching(pts, MIDDLE_TIP, MIDDLE_PIP):
            right = max(right, config.PINCH_OFF + 1e-3)

        if pose in MOVE_POSES:
            self._moving = True
        elif pose in FREEZE_POSES:
            self._moving = False

        event = None
        if pose == "two" and not self._button_down:
            event = self._scroll(hand.norm(INDEX_MCP)[1])
        else:
            self._scroll_y = None

        if self._button_down or self._moving:
            self._move(now, hand)
        else:
            self._lift()

        if pose not in NO_CLICK_POSES or self._button_down:
            event = self._buttons(pinch, right, fingers) or event
        return event

    def _move(self, now, hand):
        nx, ny = hand.norm(INDEX_MCP)
        x0, y0, x1, y1 = config.MOUSE_BOX
        sx = min(max((nx - x0) / (x1 - x0), 0.0), 1.0) * (self._screen_w - 1)
        sy = min(max((ny - y0) / (y1 - y0), 0.0), 1.0) * (self._screen_h - 1)
        x = int(min(max(self._fx(now, sx), EDGE), self._screen_w - 1 - EDGE))
        y = int(min(max(self._fy(now, sy), EDGE), self._screen_h - 1 - EDGE))
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

    def _scroll(self, y):
        if self._scroll_y is None:
            self._scroll_y = y
            return None
        dy = self._scroll_y - y         # hand moving up -> positive -> scroll up
        self._scroll_y = y
        if abs(dy) < config.MOUSE_SCROLL_DEADZONE:
            return None
        self._scroll_rest += dy * config.MOUSE_SCROLL_GAIN
        amount = int(self._scroll_rest)
        if amount == 0:
            return None
        self._scroll_rest -= amount
        self._out.scroll(amount)
        return "Scroll"
