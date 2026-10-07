"""Maps gestures to key presses."""
import pyautogui

pyautogui.PAUSE = 0          # default 0.1 s pause per call would stall the loop
pyautogui.FAILSAFE = True    # slam the mouse into a corner to abort


def press_key(key):
    pyautogui.press(key)
