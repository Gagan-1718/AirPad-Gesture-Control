"""Gesture -> keyboard actions (one always-on mode, laptop style).

Cursor, clicks and scrolling live in mouse.py. This file handles:
- Swipes, whose meaning depends on the hand shape:
    open palm   -> Right / Left arrow   (next / previous slide, page, photo)
    two fingers -> Alt+Right / Alt+Left (browser forward / back)
    three       -> Alt+Tab              (switch to the last app)
- Open palm held still -> play / pause.
- Thumbs up / down held -> volume up / down (repeats while held).

One-shot actions fire once, then "latch": holding the pose does not repeat
it. Change pose or remove the hand to re-arm.
"""
from dataclasses import dataclass

import pyautogui

import config
from smoothing import Cooldowns

pyautogui.PAUSE = 0          # default 0.1 s pause per call would stall the loop
pyautogui.FAILSAFE = True    # slam the real mouse into a corner to abort


class Output:
    """Sends real keyboard and mouse input to the OS."""

    def press(self, key):
        pyautogui.press(key)

    def hotkey(self, keys):
        pyautogui.hotkey(*keys)

    def scroll(self, amount):
        pyautogui.scroll(amount)    # Windows: 120 units = one wheel notch

    def position(self):
        return tuple(pyautogui.position())

    def move(self, x, y):
        pyautogui.moveTo(x, y)

    def mouse_down(self):
        pyautogui.mouseDown()

    def mouse_up(self):
        pyautogui.mouseUp()

    def right_click(self):
        pyautogui.click(button="right")


class DryRunOutput(Output):
    """Prints actions instead of sending them. The real cursor is not moved."""

    def __init__(self):
        w, h = pyautogui.size()
        self._pos = (w // 2, h // 2)

    def press(self, key):
        print(f"[dry-run] press {key}")

    def hotkey(self, keys):
        print(f"[dry-run] hotkey {'+'.join(keys)}")

    def scroll(self, amount):
        print(f"[dry-run] scroll {amount}")

    def position(self):
        return self._pos

    def move(self, x, y):
        self._pos = (x, y)

    def mouse_down(self):
        print("[dry-run] mouse down")

    def mouse_up(self):
        print("[dry-run] mouse up")

    def right_click(self):
        print("[dry-run] right click")


@dataclass(frozen=True)
class Binding:
    action: tuple                   # ("press", key) or ("hotkey", (key, ...))
    label: str
    hold_s: float = 0.0             # pose must be held this long (still, if required)
    cooldown_s: float = config.GESTURE_COOLDOWN_S
    repeat_s: float | None = None   # repeat while held instead of latching
    require_still: bool = True


def press(key):
    return ("press", key)


def hotkey(*keys):
    return ("hotkey", keys)


SWIPE_BINDINGS = {
    ("palm", "swipe_right"): Binding(press("right"), "Next"),
    ("palm", "swipe_left"): Binding(press("left"), "Previous"),
    ("two", "swipe_right"): Binding(hotkey("alt", "right"), "Forward"),
    ("two", "swipe_left"): Binding(hotkey("alt", "left"), "Back"),
    ("three", "swipe_right"): Binding(hotkey("alt", "tab"), "Switch app"),
    ("three", "swipe_left"): Binding(hotkey("alt", "tab"), "Switch app"),
}

STATIC_BINDINGS = {
    "palm": Binding(press("playpause"), "Play / Pause", hold_s=config.PLAYPAUSE_HOLD_S),
    "thumb_up": Binding(press("volumeup"), "Volume up", hold_s=config.VOLUME_HOLD_S,
                        repeat_s=config.VOLUME_REPEAT_S, require_still=False),
    "thumb_down": Binding(press("volumedown"), "Volume down", hold_s=config.VOLUME_HOLD_S,
                          repeat_s=config.VOLUME_REPEAT_S, require_still=False),
}

_LATCH_NEXT = object()   # latch whichever pose is seen next


class GestureController:
    def __init__(self, output):
        self._output = output
        self._cooldowns = Cooldowns()
        self._latched = None          # pose already used; ignored until it changes
        self._hold_label = None
        self._hold_start = 0.0
        self._static_block_until = 0.0
        self._last_swipe = None       # (direction, time)
        self.hold_progress = 0.0      # 0..1 for the play/pause progress bar

    def _perform(self, action):
        kind, arg = action
        getattr(self._output, kind)(arg)

    def hand_lost(self):
        self._latched = None
        self._hold_label = None
        self.hold_progress = 0.0

    def update(self, now, pose, still, swipe):
        """Feed one frame. Returns the fired action label, or None.

        pose: stable pose (or None); still: hand roughly still;
        swipe: (direction, pose) from MotionTracker.detect_swipe, or None.
        """
        if swipe and (swipe[1], swipe[0]) in SWIPE_BINDINGS:
            return self._handle_swipe(now, pose, swipe)

        if pose is not None and self._latched is _LATCH_NEXT:
            self._latched = pose
        elif pose is not None and pose != self._latched:
            self._latched = None
        self._update_hold(now, pose, still)
        self.hold_progress = 0.0

        binding = STATIC_BINDINGS.get(pose)
        if binding is None or pose == self._latched or now < self._static_block_until:
            return None
        held = now - self._hold_start
        if binding.hold_s > 0:
            self.hold_progress = min(held / binding.hold_s, 1.0)
        if held < binding.hold_s or not self._cooldowns.ready(pose, now):
            return None
        self._perform(binding.action)
        self.hold_progress = 0.0
        if binding.repeat_s is not None:
            self._cooldowns.trigger(pose, now, binding.repeat_s)
        else:
            self._cooldowns.trigger(pose, now, binding.cooldown_s)
            self._latched = pose
        return binding.label

    def _update_hold(self, now, pose, still):
        """Track how long `pose` has been held (and still, if required)."""
        if pose != self._hold_label:
            self._hold_label = pose
            self._hold_start = now
            return
        binding = STATIC_BINDINGS.get(pose)
        if binding is not None and binding.require_still and not still:
            self._hold_start = now

    def _handle_swipe(self, now, pose, swipe):
        direction, swipe_pose = swipe
        # Whatever shape the hand ends the swipe in must not fire on its own.
        self._latched = pose if pose is not None else _LATCH_NEXT
        self._hold_label = None
        self.hold_progress = 0.0
        self._static_block_until = now + config.SWIPE_STATIC_BLOCK_S

        if self._last_swipe is not None:
            last_dir, last_t = self._last_swipe
            if direction != last_dir and now - last_t < config.SWIPE_REVERSE_BLOCK_S:
                return None   # the hand coming back after a swipe
        if not self._cooldowns.ready("swipe", now):
            return None
        binding = SWIPE_BINDINGS[(swipe_pose, direction)]
        self._perform(binding.action)
        self._cooldowns.trigger("swipe", now, config.SWIPE_COOLDOWN_S)
        self._last_swipe = (direction, now)
        return binding.label
