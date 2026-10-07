"""Maps gestures to key presses per mode, plus mode switching.

Firing rules:
- One-shot actions (play/pause, jump, swipes) fire once, then "latch": holding the
  gesture does not repeat it. Change gesture or remove the hand to re-arm.
- Repeat actions (volume, PDF scrolling) keep firing every `repeat_s` while held.
- Static gestures need the hand roughly still (unless `require_still=False`),
  so moving your hand for a swipe does not also fire a static gesture.
Mouse mode's cursor control lives in mouse.py; here it only gets mode switching.
"""
from dataclasses import dataclass

import pyautogui

import config
from smoothing import Cooldowns

pyautogui.PAUSE = 0          # default 0.1 s pause per call would stall the loop
pyautogui.FAILSAFE = True    # slam the mouse into a corner to abort


class Output:
    """Sends real keyboard and mouse input to the OS."""

    def press(self, key):
        pyautogui.press(key)

    def scroll(self, amount):
        pyautogui.scroll(amount)    # Windows: 120 units = one wheel notch

    def move(self, x, y):
        pyautogui.moveTo(x, y)


class DryRunOutput(Output):
    """Prints actions instead of sending them. The cursor is not moved."""

    def press(self, key):
        print(f"[dry-run] press {key}")

    def scroll(self, amount):
        print(f"[dry-run] scroll {amount}")

    def move(self, x, y):
        pass


@dataclass(frozen=True)
class Binding:
    action: tuple                   # ("press", key) or ("scroll", amount)
    label: str
    hold_s: float = 0.0             # gesture must be held (still) this long
    cooldown_s: float = config.GESTURE_COOLDOWN_S
    repeat_s: float | None = None   # repeat while held instead of latching
    require_still: bool = True


def press(key):
    return ("press", key)


def scroll(amount):
    return ("scroll", amount)


# Modes without swipe bindings (mouse) ignore swipes entirely.
SWIPE_BINDINGS = {
    "media": {"swipe_right": Binding(press("nexttrack"), "Next track"),
              "swipe_left": Binding(press("prevtrack"), "Previous track")},
    "slides": {"swipe_right": Binding(press("right"), "Next slide"),
               "swipe_left": Binding(press("left"), "Previous slide")},
    "pdf": {"swipe_right": Binding(press("pagedown"), "Next page"),
            "swipe_left": Binding(press("pageup"), "Previous page")},
    "mouse": {},
    "game": {"swipe_right": Binding(press("right"), "Move right"),
             "swipe_left": Binding(press("left"), "Move left")},
}

STATIC_BINDINGS = {
    "media": {
        "palm": Binding(press("playpause"), "Play / Pause", hold_s=config.PLAYPAUSE_HOLD_S),
        "one": Binding(press("volumeup"), "Volume up", repeat_s=config.VOLUME_REPEAT_S),
        "two": Binding(press("volumedown"), "Volume down", repeat_s=config.VOLUME_REPEAT_S),
    },
    "slides": {},
    "pdf": {
        "one": Binding(scroll(-config.PDF_SCROLL_STEP), "Scroll down", repeat_s=config.PDF_SCROLL_REPEAT_S),
        "two": Binding(scroll(config.PDF_SCROLL_STEP), "Scroll up", repeat_s=config.PDF_SCROLL_REPEAT_S),
    },
    "mouse": {},
    "game": {
        "fist": Binding(press("space"), "Jump", cooldown_s=config.JUMP_COOLDOWN_S, require_still=False),
    },
}


MODE_SWITCH = "three"
_LATCH_NEXT = object()   # latch whichever gesture is seen next


class GestureController:
    def __init__(self, output):
        self._output = output
        self.mode = config.START_MODE
        self._cooldowns = Cooldowns()
        self._latched = None          # gesture already used; ignored until it changes
        self._hold_label = None
        self._hold_start = 0.0
        self._static_block_until = 0.0
        self._last_swipe = None       # (direction, time)
        self.hold_progress = 0.0      # 0..1 for the mode-switch progress bar

    def _perform(self, action):
        kind, arg = action
        getattr(self._output, kind)(arg)

    def hand_lost(self):
        self._latched = None
        self._hold_label = None
        self.hold_progress = 0.0

    def update(self, now, gesture, still, swipe):
        """Feed one processed frame. Returns the fired action label, or None.

        gesture: stable static gesture (or None); still: hand roughly still;
        swipe: "swipe_left" / "swipe_right" / None.
        """
        if swipe and SWIPE_BINDINGS[self.mode]:
            return self._handle_swipe(now, gesture, swipe)

        if gesture is not None and self._latched is _LATCH_NEXT:
            self._latched = gesture
        elif gesture is not None and gesture != self._latched:
            self._latched = None
        self._update_hold(now, gesture, still)
        self.hold_progress = 0.0

        if gesture is None or gesture == self._latched or now < self._static_block_until:
            return None
        held = now - self._hold_start

        if gesture == MODE_SWITCH:
            self.hold_progress = min(held / config.MODE_SWITCH_HOLD_S, 1.0)
            if held < config.MODE_SWITCH_HOLD_S:
                return None
            modes = config.MODES
            self.mode = modes[(modes.index(self.mode) + 1) % len(modes)]
            self._latched = gesture
            self.hold_progress = 0.0
            return f"Mode: {'PDF' if self.mode == 'pdf' else self.mode.title()}"

        binding = STATIC_BINDINGS[self.mode].get(gesture)
        if binding is None or held < binding.hold_s or not self._cooldowns.ready(gesture, now):
            return None
        self._perform(binding.action)
        if binding.repeat_s is not None:
            self._cooldowns.trigger(gesture, now, binding.repeat_s)
        else:
            self._cooldowns.trigger(gesture, now, binding.cooldown_s)
            self._latched = gesture
        return binding.label

    def _update_hold(self, now, gesture, still):
        """Track how long `gesture` has been held (and still, if required)."""
        if gesture != self._hold_label:
            self._hold_label = gesture
            self._hold_start = now
            return
        binding = STATIC_BINDINGS[self.mode].get(gesture)
        needs_still = gesture == MODE_SWITCH or (binding is not None and binding.require_still)
        if needs_still and not still:
            self._hold_start = now

    def _handle_swipe(self, now, gesture, swipe):
        # Whatever shape the hand ends the swipe in must not fire on its own.
        self._latched = gesture if gesture is not None else _LATCH_NEXT
        self._hold_label = None
        self.hold_progress = 0.0
        self._static_block_until = now + config.SWIPE_STATIC_BLOCK_S

        if self._last_swipe is not None:
            last_dir, last_t = self._last_swipe
            if swipe != last_dir and now - last_t < config.SWIPE_REVERSE_BLOCK_S:
                return None   # the hand coming back after a swipe
        binding = SWIPE_BINDINGS[self.mode].get(swipe)
        if binding is None or not self._cooldowns.ready("swipe", now):
            return None
        self._perform(binding.action)
        self._cooldowns.trigger("swipe", now, config.SWIPE_COOLDOWN_S)
        self._last_swipe = (swipe, now)
        return binding.label
