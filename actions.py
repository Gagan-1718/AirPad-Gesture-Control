"""Maps gestures to key presses."""
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

    def update(self, now, gesture):
        """Feed one processed frame. Returns the fired action label, or None."""
        binding = BINDINGS.get(gesture)
        if binding is None or not self._cooldowns.ready(gesture, now):
            return None
        self._send(binding.key)
        self._cooldowns.trigger(gesture, now, binding.cooldown_s)
        return binding.label
