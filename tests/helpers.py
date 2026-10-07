"""Synthetic hands for tests: an upright hand, palm facing the camera."""
import math
from dataclasses import dataclass


@dataclass
class FakeHand:
    points: list
    frame_w: int = 640
    frame_h: int = 480

    def norm(self, index):
        x, y = self.points[index]
        return x / self.frame_w, y / self.frame_h


THUMBS = {
    "in": [(-45, -50), (-30, -70), (-5, -75)],      # tucked across the palm
    "out": [(-60, -45), (-85, -60), (-110, -70)],   # spread sideways
    "up": [(-45, -60), (-50, -110), (-50, -160)],   # thumbs up
    "down": [(-45, -20), (-50, 25), (-50, 75)],     # thumbs down
}


def make_hand(fingers=(1, 1, 1, 1), thumb="in", cx=320, cy=400, scale=1.0, angle=0.0):
    """Build 21 landmarks. fingers: (index, middle, ring, pinky), 1 = extended.

    The wrist sits at (cx, cy) and the hand is 100 * scale px from wrist to
    middle-finger base. angle (degrees) tilts the hand around the wrist.
    """
    cos, sin = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def at(dx, dy):
        dx, dy = dx * scale, dy * scale
        return (cx + dx * cos - dy * sin, cy + dx * sin + dy * cos)

    pts = [at(0, 0), at(-35, -25)] + [at(*p) for p in THUMBS[thumb]]
    for dx, up in zip((-25, 0, 25, 45), fingers):
        tip = [at(dx, -165), at(dx, -190)] if up else [at(dx, -115), at(dx, -85)]
        pts += [at(dx, -100), at(dx, -140)] + tip
    return FakeHand(pts)


class FakeOutput:
    """Records keyboard and mouse output instead of sending it to the OS."""

    def __init__(self, position=(1500, 900)):
        self.log = []
        self._pos = position

    def press(self, key):
        self.log.append(("press", key))

    def hotkey(self, keys):
        self.log.append(("hotkey", tuple(keys)))

    def scroll(self, amount):
        self.log.append(("scroll", amount))

    def position(self):
        return self._pos

    def move(self, x, y):
        self._pos = (x, y)
        self.log.append(("move", x, y))

    def mouse_down(self):
        self.log.append(("mouse_down",))

    def mouse_up(self):
        self.log.append(("mouse_up",))

    def right_click(self):
        self.log.append(("right_click",))

    def keys(self):
        return [entry[1] for entry in self.log if entry[0] == "press"]

    def events(self):
        """Everything except cursor moves."""
        return [entry for entry in self.log if entry[0] != "move"]
