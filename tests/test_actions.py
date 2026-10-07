from actions import GestureController
from helpers import FakeOutput


def feed(ctrl, frames, dt=1 / 30):
    """Feed one frame per item at 30 fps; return the fired labels.

    Items are pose names (hand still, no swipe) or (pose, still, swipe) tuples.
    """
    fired = []
    for i, frame in enumerate(frames, start=1):
        pose, still, swipe = frame if isinstance(frame, tuple) else (frame, True, None)
        label = ctrl.update(i * dt, pose, still, swipe)
        if label:
            fired.append(label)
    return fired


def test_palm_held_still_toggles_play_pause_once():
    out = FakeOutput()
    feed(GestureController(out), ["palm"] * 60)
    assert out.keys() == ["playpause"]


def test_moving_palm_does_not_toggle_play_pause():
    out = FakeOutput()
    feed(GestureController(out), [("palm", False, None)] * 60)
    assert out.keys() == []


def test_palm_fires_again_after_changing_pose():
    out = FakeOutput()
    feed(GestureController(out), ["palm"] * 30 + ["fist"] * 30 + ["palm"] * 30)
    assert out.keys() == ["playpause", "playpause"]


def test_hold_progress_fills_while_holding_the_palm():
    ctrl = GestureController(FakeOutput())
    feed(ctrl, ["palm"] * 6)
    assert 0 < ctrl.hold_progress < 1


def test_thumbs_up_repeats_volume_up():
    out = FakeOutput()
    feed(GestureController(out), ["thumb_up"] * 30)          # 1 second
    assert len(out.keys()) >= 3
    assert set(out.keys()) == {"volumeup"}


def test_thumbs_down_lowers_the_volume():
    out = FakeOutput()
    feed(GestureController(out), ["thumb_down"] * 30)
    assert set(out.keys()) == {"volumedown"}


def test_palm_swipe_presses_the_arrow_keys():
    out = FakeOutput()
    ctrl = GestureController(out)
    assert ctrl.update(1.0, None, False, ("swipe_right", "palm")) == "Next"
    assert ctrl.update(3.0, None, False, ("swipe_left", "palm")) == "Previous"
    assert out.keys() == ["right", "left"]


def test_swipe_with_a_pointing_hand_is_ignored():
    out = FakeOutput()
    ctrl = GestureController(out)
    assert ctrl.update(1.0, "point", False, ("swipe_right", "point")) is None
    assert out.log == []


def test_swipes_share_a_cooldown():
    out = FakeOutput()
    ctrl = GestureController(out)
    for t in (1.0, 1.5, 2.1):
        ctrl.update(t, None, False, ("swipe_right", "palm"))
    assert out.keys() == ["right", "right"]


def test_return_stroke_after_a_swipe_is_ignored():
    out = FakeOutput()
    ctrl = GestureController(out)
    ctrl.update(1.0, None, False, ("swipe_right", "palm"))
    ctrl.update(2.0, None, False, ("swipe_left", "palm"))    # hand coming back
    ctrl.update(3.0, None, False, ("swipe_right", "palm"))   # next real swipe
    assert out.keys() == ["right", "right"]


def test_palm_held_after_a_swipe_does_not_toggle_play_pause():
    out = FakeOutput()
    frames = ["palm"] * 3 + [("palm", False, ("swipe_right", "palm"))] + ["palm"] * 60
    feed(GestureController(out), frames)
    assert out.keys() == ["right"]


def test_blurred_swipe_still_latches_the_final_pose():
    out = FakeOutput()
    frames = ["palm"] * 3 + [(None, False, ("swipe_right", "palm"))] + ["palm"] * 60
    feed(GestureController(out), frames)
    assert out.keys() == ["right"]


def test_two_finger_swipes_go_back_and_forward():
    out = FakeOutput()
    ctrl = GestureController(out)
    assert ctrl.update(1.0, None, False, ("swipe_left", "two")) == "Back"
    assert ctrl.update(3.0, None, False, ("swipe_right", "two")) == "Forward"
    assert out.log == [("hotkey", ("alt", "left")), ("hotkey", ("alt", "right"))]


def test_three_finger_swipe_switches_apps():
    out = FakeOutput()
    ctrl = GestureController(out)
    assert ctrl.update(1.0, None, False, ("swipe_right", "three")) == "Switch app"
    assert out.log == [("hotkey", ("alt", "tab"))]
