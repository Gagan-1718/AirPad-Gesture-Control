"""Stability filter, cooldown timers and cursor smoothing."""
import math
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


class OneEuroFilter:
    """Smooths a noisy signal: steady when still, low lag when moving fast.

    See Casiez et al., "1 Euro Filter" (CHI 2012).
    """

    def __init__(self, min_cutoff, beta, d_cutoff=1.0):
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self.reset()

    def reset(self):
        self._t = None
        self._x = 0.0
        self._dx = 0.0

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, t, x):
        if self._t is None:
            self._t, self._x = t, x
            return x
        dt = max(t - self._t, 1e-6)
        a_d = self._alpha(self._d_cutoff, dt)
        self._dx = a_d * (x - self._x) / dt + (1 - a_d) * self._dx
        a = self._alpha(self._min_cutoff + self._beta * abs(self._dx), dt)
        self._x = a * x + (1 - a) * self._x
        self._t = t
        return self._x
