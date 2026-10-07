"""Stability filter."""
from collections import Counter, deque


class StabilityFilter:
    """A label only counts once it wins `required` of the last `window` frames."""

    def __init__(self, window, required):
        self.configure(window, required)

    def configure(self, window, required):
        self._buf = deque(maxlen=window)
        self._required = required

    def update(self, label):
        self._buf.append(label)
        best, count = Counter(self._buf).most_common(1)[0]
        return best if count >= self._required else None

    def reset(self):
        self._buf.clear()
