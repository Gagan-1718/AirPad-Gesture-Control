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


def test_holding_palm_fires_only_once():
    sent = []
    feed(GestureController(sent.append), ["palm"] * 45)     # 3 seconds
    assert sent == ["playpause"]


def test_palm_fires_again_after_changing_pose():
    sent = []
    feed(GestureController(sent.append), ["palm"] * 15 + ["fist"] * 15 + ["palm"] * 15)
    assert sent == ["playpause", "playpause"]


def test_volume_repeats_while_held():
    sent = []
    feed(GestureController(sent.append), ["one"] * 15)      # 1 second
    assert sent == ["volumeup"] * 4


def test_swipe_right_skips_to_the_next_track():
    sent = []
    ctrl = GestureController(sent.append)
    assert ctrl.update(1.0, None, "swipe_right") == "Next track"
    assert sent == ["nexttrack"]


def test_swipes_share_a_cooldown():
    sent = []
    ctrl = GestureController(sent.append)
    ctrl.update(1.0, None, "swipe_right")
    ctrl.update(1.5, None, "swipe_right")
    ctrl.update(2.1, None, "swipe_right")
    assert sent == ["nexttrack", "nexttrack"]


def test_slides_mode_uses_arrow_keys():
    sent = []
    ctrl = GestureController(sent.append)
    ctrl.mode = "slides"
    ctrl.update(1.0, None, "swipe_right")
    ctrl.update(2.5, None, "swipe_left")
    feed(ctrl, ["palm"] * 15)
    assert sent == ["right", "left"]


def test_return_stroke_after_a_swipe_is_ignored():
    sent = []
    ctrl = GestureController(sent.append)
    ctrl.mode = "slides"
    ctrl.update(1.0, None, "swipe_right")
    ctrl.update(2.2, None, "swipe_left")    # hand coming back
    ctrl.update(3.0, None, "swipe_right")   # next real swipe
    assert sent == ["right", "right"]
