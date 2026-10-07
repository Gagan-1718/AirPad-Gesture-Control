"""Maps gestures to key presses per mode.

- One-shot actions (play/pause, swipes) fire once, then "latch": holding the
  gesture does not repeat it. Change gesture or remove the hand to re-arm.
- Repeat actions (volume) keep firing every `repeat_s` while held.
"""
from dataclasses import dataclass

import pyautogui

import config
from smoothing import Cooldowns

pyautogui.PAUSE = 0          # default 0.1 s pause per call would stall the loop
pyautogui.FAILSAFE = True    # slam the mouse into a corner to abort


@dataclass(frozen=True)
class Binding:
    key: str
    label: str
    cooldown_s: float = config.GESTURE_COOLDOWN_S
    repeat_s: float | None = None   # repeat while held instead of latching


SWIPE_BINDINGS = {
    "media": {"swipe_right": Binding("nexttrack", "Next track"),
              "swipe_left": Binding("prevtrack", "Previous track")},
    "slides": {"swipe_right": Binding("right", "Next slide"),
               "swipe_left": Binding("left", "Previous slide")},
}

STATIC_BINDINGS = {
    "media": {
        "palm": Binding("playpause", "Play / Pause"),
        "one": Binding("volumeup", "Volume up", repeat_s=config.VOLUME_REPEAT_S),
        "two": Binding("volumedown", "Volume down", repeat_s=config.VOLUME_REPEAT_S),
    },
    "slides": {},
}


def press_key(key):
    pyautogui.press(key)


class GestureController:
    def __init__(self, send=press_key):
        self._send = send
        self.mode = config.START_MODE
        self._cooldowns = Cooldowns()
        self._latched = None          # gesture already used; ignored until it changes
        self._last_swipe = None       # (direction, time)

    def hand_lost(self):
        self._latched = None

    def update(self, now, gesture, swipe=None):
        """Feed one processed frame. Returns the fired action label, or None."""
        if swipe:
            return self._handle_swipe(now, swipe)
        if gesture is not None and gesture != self._latched:
            self._latched = None
        binding = STATIC_BINDINGS[self.mode].get(gesture)
        if binding is None or gesture == self._latched or not self._cooldowns.ready(gesture, now):
            return None
        self._send(binding.key)
        if binding.repeat_s is not None:
            self._cooldowns.trigger(gesture, now, binding.repeat_s)
        else:
            self._cooldowns.trigger(gesture, now, binding.cooldown_s)
            self._latched = gesture
        return binding.label

    def _handle_swipe(self, now, swipe):
        if self._last_swipe is not None:
            last_dir, last_t = self._last_swipe
            if swipe != last_dir and now - last_t < config.SWIPE_REVERSE_BLOCK_S:
                return None   # the hand coming back after a swipe
        binding = SWIPE_BINDINGS[self.mode].get(swipe)
        if binding is None or not self._cooldowns.ready("swipe", now):
            return None
        self._send(binding.key)
        self._cooldowns.trigger("swipe", now, config.SWIPE_COOLDOWN_S)
        self._last_swipe = (swipe, now)
        return binding.label
