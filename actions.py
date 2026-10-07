"""Maps gestures to key presses.

One-shot actions fire once, then "latch": holding the gesture does not
repeat it. Change gesture or remove the hand to re-arm.
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


BINDINGS = {
    "palm": Binding("playpause", "Play / Pause"),
    "one": Binding("volumeup", "Volume up"),
    "two": Binding("volumedown", "Volume down"),
}


def press_key(key):
    pyautogui.press(key)


class GestureController:
    def __init__(self, send=press_key):
        self._send = send
        self._cooldowns = Cooldowns()
        self._latched = None          # gesture already used; ignored until it changes

    def hand_lost(self):
        self._latched = None

    def update(self, now, gesture):
        """Feed one processed frame. Returns the fired action label, or None."""
        if gesture is not None and gesture != self._latched:
            self._latched = None
        binding = BINDINGS.get(gesture)
        if binding is None or gesture == self._latched or not self._cooldowns.ready(gesture, now):
            return None
        self._send(binding.key)
        self._cooldowns.trigger(gesture, now, binding.cooldown_s)
        self._latched = gesture
        return binding.label
