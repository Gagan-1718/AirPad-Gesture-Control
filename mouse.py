"""Cursor, clicks and scrolling, used like a touchpad.

- Point (index up) and move: the cursor moves *relative* to your hand, with
  acceleration: slow = precise, fast = far. It continues from wherever the
  cursor already is, so you can mix it with the real touchpad.
- Fist (or hand out of view) = "lift the finger": the cursor stays put, so you
  can reposition your hand.
- Pinch thumb + index: left button down; open = up. Hold the pinch and move to
  drag. Pinch twice quickly to double-click.
- Pinch thumb + middle with the index up: right click.
- Two fingers up, move hand up / down: scroll.
The cursor follows the index-finger knuckle (landmark 5), not the fingertip,
and slows down as your fingers approach a pinch, so clicks land where you aim.
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
        self._fx = OneEuroFilter(config.CURSOR_SMOOTH_MIN_CUTOFF, config.CURSOR_SMOOTH_BETA)
        self._fy = OneEuroFilter(config.CURSOR_SMOOTH_MIN_CUTOFF, config.CURSOR_SMOOTH_BETA)
        self._moving = False          # current pose drives the cursor
        self._ref = None              # last filtered hand position (x, y, t)
        self._pos = (0.0, 0.0)        # cursor position with sub-pixel precision
        self._button_down = False
        self._down_at = 0.0
        self._pinch_frames = 0
        self._right_pinched = False
        self._scroll_y = None
        self._scroll_rest = 0.0

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
        """Stop tracking hand motion; the next movement starts fresh (no jump)."""
        self._ref = None
        self._fx.reset()
        self._fy.reset()

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
            self._move(now, hand, slow=not self._button_down and pinch < config.PRECISION_ZONE)
        else:
            self._lift()

        if pose not in NO_CLICK_POSES or self._button_down:
            event = self._buttons(now, pinch, right, fingers) or event
        return event

    def _move(self, now, hand, slow):
        nx, ny = hand.norm(INDEX_MCP)
        # Smooth in camera pixels so the filter's speed terms behave the same at any resolution.
        fx = self._fx(now, nx * hand.frame_w) / hand.frame_w
        fy = self._fy(now, ny * hand.frame_h) / hand.frame_h
        if self._ref is None:
            self._ref = (fx, fy, now)
            self._pos = self._out.position()
            return
        rx, ry, rt = self._ref
        self._ref = (fx, fy, now)
        if self._button_down and now - self._down_at < config.CLICK_FREEZE_S:
            return                      # hold still so a click doesn't become a drag
        dx, dy = fx - rx, fy - ry
        speed = math.hypot(dx, dy) / max(now - rt, 1e-3)
        if speed < config.CURSOR_DEADZONE:
            return
        t = (speed - config.CURSOR_ACCEL_START) / (config.CURSOR_ACCEL_FULL - config.CURSOR_ACCEL_START)
        t = min(max(t, 0.0), 1.0)
        gain = config.CURSOR_MIN_SPEED + (config.CURSOR_MAX_SPEED - config.CURSOR_MIN_SPEED) * t
        if slow:
            gain *= config.PRECISION_FACTOR
        x = min(max(self._pos[0] + dx * gain * self._screen_w, EDGE), self._screen_w - 1 - EDGE)
        y = min(max(self._pos[1] + dy * gain * self._screen_h, EDGE), self._screen_h - 1 - EDGE)
        if (int(x), int(y)) != (int(self._pos[0]), int(self._pos[1])):
            self._out.move(int(x), int(y))
        self._pos = (x, y)

    def _buttons(self, now, pinch, right, fingers):
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
                self._down_at = now
                self._out.mouse_down()
                return "Click"
        else:
            self._pinch_frames = 0
        return None

    def _scroll(self, y):
        if self._scroll_y is None:
            self._scroll_y = y
            return None
        dy = y - self._scroll_y         # hand moving down -> positive
        self._scroll_y = y
        if abs(dy) < config.SCROLL_DEADZONE:
            return None
        # Natural: page follows the hand (hand up -> content up -> scroll down).
        direction = 1 if config.SCROLL_NATURAL else -1
        self._scroll_rest += direction * dy * config.SCROLL_GAIN
        amount = int(self._scroll_rest)
        if amount == 0:
            return None
        self._scroll_rest -= amount
        self._out.scroll(amount)
        return "Scroll"
