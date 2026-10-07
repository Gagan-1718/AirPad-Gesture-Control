"""Stability filter and cooldown timers."""
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


class Cooldowns:
    """Per-key "not before" timestamps."""

    def __init__(self):
        self._until = {}

    def ready(self, key, now):
        return now >= self._until.get(key, 0.0)

    def trigger(self, key, now, seconds):
        self._until[key] = now + seconds

    def reset(self):
        self._until.clear()
