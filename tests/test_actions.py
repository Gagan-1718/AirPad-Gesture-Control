from actions import GestureController


def feed(ctrl, frames, dt=1 / 15):
    """Feed one frame per item at 15 fps; return the fired labels.

    Items are gesture names (hand still, no swipe) or (gesture, still, swipe).
    """
    fired = []
    for i, frame in enumerate(frames, start=1):
        gesture, still, swipe = frame if isinstance(frame, tuple) else (frame, True, None)
        label = ctrl.update(i * dt, gesture, still, swipe)
        if label:
            fired.append(label)
    return fired


def test_palm_toggles_play_pause():
    sent = []
    feed(GestureController(sent.append), ["palm"] * 10)
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


def test_moving_palm_does_not_toggle_play_pause():
    sent = []
    feed(GestureController(sent.append), [("palm", False, None)] * 30)
    assert sent == []


def test_swipe_right_skips_to_the_next_track():
    sent = []
    ctrl = GestureController(sent.append)
    assert ctrl.update(1.0, None, False, "swipe_right") == "Next track"
    assert sent == ["nexttrack"]


def test_swipes_share_a_cooldown():
    sent = []
    ctrl = GestureController(sent.append)
    ctrl.update(1.0, None, False, "swipe_right")
    ctrl.update(1.5, None, False, "swipe_right")
    ctrl.update(2.1, None, False, "swipe_right")
    assert sent == ["nexttrack", "nexttrack"]


def test_slides_mode_uses_arrow_keys():
    sent = []
    ctrl = GestureController(sent.append)
    ctrl.mode = "slides"
    ctrl.update(1.0, None, False, "swipe_right")
    ctrl.update(2.5, None, False, "swipe_left")
    feed(ctrl, ["palm"] * 15)
    assert sent == ["right", "left"]


def test_return_stroke_after_a_swipe_is_ignored():
    sent = []
    ctrl = GestureController(sent.append)
    ctrl.mode = "slides"
    ctrl.update(1.0, None, False, "swipe_right")
    ctrl.update(2.2, None, False, "swipe_left")    # hand coming back
    ctrl.update(3.0, None, False, "swipe_right")   # next real swipe
    assert sent == ["right", "right"]


def test_palm_held_after_a_swipe_does_not_toggle_play_pause():
    sent = []
    frames = ["palm"] * 3 + [("palm", False, "swipe_right")] + ["palm"] * 30
    feed(GestureController(sent.append), frames)
    assert sent == ["nexttrack"]


def test_blurred_swipe_still_latches_the_final_pose():
    sent = []
    frames = ["palm"] * 3 + [(None, False, "swipe_right")] + ["palm"] * 30
    feed(GestureController(sent.append), frames)
    assert sent == ["nexttrack"]
