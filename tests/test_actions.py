from actions import GestureController


def feed(ctrl, gestures, dt=1 / 15):
    """Feed one gesture per frame at 15 fps; return the fired labels."""
    fired = []
    for i, g in enumerate(gestures, start=1):
        label = ctrl.update(i * dt, g)
        if label:
            fired.append(label)
    return fired


def test_palm_toggles_play_pause():
    sent = []
    feed(GestureController(sent.append), ["palm"] * 5)
    assert sent == ["playpause"]


def test_unmapped_gestures_do_nothing():
    sent = []
    feed(GestureController(sent.append), ["fist", "other", None] * 10)
    assert sent == []
