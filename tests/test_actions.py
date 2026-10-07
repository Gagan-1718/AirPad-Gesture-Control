from actions import GestureController
from helpers import FakeOutput


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
    out = FakeOutput()
    feed(GestureController(out), ["palm"] * 10)
    assert out.keys() == ["playpause"]


def test_unmapped_gestures_do_nothing():
    out = FakeOutput()
    feed(GestureController(out), ["fist", "other", None] * 10)
    assert out.keys() == []


def test_holding_palm_fires_only_once():
    out = FakeOutput()
    feed(GestureController(out), ["palm"] * 45)     # 3 seconds
    assert out.keys() == ["playpause"]


def test_palm_fires_again_after_changing_pose():
    out = FakeOutput()
    feed(GestureController(out), ["palm"] * 15 + ["fist"] * 15 + ["palm"] * 15)
    assert out.keys() == ["playpause", "playpause"]


def test_volume_repeats_while_held():
    out = FakeOutput()
    feed(GestureController(out), ["point"] * 15)      # 1 second
    assert out.keys() == ["volumeup"] * 4


def test_moving_palm_does_not_toggle_play_pause():
    out = FakeOutput()
    feed(GestureController(out), [("palm", False, None)] * 30)
    assert out.keys() == []


def test_swipe_right_skips_to_the_next_track():
    out = FakeOutput()
    ctrl = GestureController(out)
    assert ctrl.update(1.0, None, False, "swipe_right") == "Next track"
    assert out.keys() == ["nexttrack"]


def test_swipes_share_a_cooldown():
    out = FakeOutput()
    ctrl = GestureController(out)
    ctrl.update(1.0, None, False, "swipe_right")
    ctrl.update(1.5, None, False, "swipe_right")
    ctrl.update(2.1, None, False, "swipe_right")
    assert out.keys() == ["nexttrack", "nexttrack"]


def test_slides_mode_uses_arrow_keys():
    out = FakeOutput()
    ctrl = GestureController(out)
    ctrl.mode = "slides"
    ctrl.update(1.0, None, False, "swipe_right")
    ctrl.update(2.5, None, False, "swipe_left")
    feed(ctrl, ["palm"] * 15)
    assert out.keys() == ["right", "left"]


def test_return_stroke_after_a_swipe_is_ignored():
    out = FakeOutput()
    ctrl = GestureController(out)
    ctrl.mode = "slides"
    ctrl.update(1.0, None, False, "swipe_right")
    ctrl.update(2.2, None, False, "swipe_left")    # hand coming back
    ctrl.update(3.0, None, False, "swipe_right")   # next real swipe
    assert out.keys() == ["right", "right"]


def test_palm_held_after_a_swipe_does_not_toggle_play_pause():
    out = FakeOutput()
    frames = ["palm"] * 3 + [("palm", False, "swipe_right")] + ["palm"] * 30
    feed(GestureController(out), frames)
    assert out.keys() == ["nexttrack"]


def test_blurred_swipe_still_latches_the_final_pose():
    out = FakeOutput()
    frames = ["palm"] * 3 + [(None, False, "swipe_right")] + ["palm"] * 30
    feed(GestureController(out), frames)
    assert out.keys() == ["nexttrack"]


def test_holding_three_fingers_switches_mode_once():
    ctrl = GestureController(FakeOutput())
    fired = feed(ctrl, ["three"] * 60)                      # 4 seconds
    assert fired == ["Mode: Slides"]
    assert ctrl.mode == "slides"


def test_short_three_finger_hold_does_not_switch():
    ctrl = GestureController(FakeOutput())
    feed(ctrl, ["three"] * 15 + [None] * 5)                # 1 second
    assert ctrl.mode == "media"


def test_game_mode_jumps_on_each_fist():
    out = FakeOutput()
    ctrl = GestureController(out)
    ctrl.mode = "game"
    feed(ctrl, (["fist"] * 4 + ["palm"] * 4) * 3)
    assert out.keys() == ["space"] * 3


def test_pdf_mode_turns_pages_and_scrolls():
    out = FakeOutput()
    ctrl = GestureController(out)
    ctrl.mode = "pdf"
    feed(ctrl, ["point"] * 5)
    ctrl.update(10.0, None, False, "swipe_right")
    assert out.log[0] == ("scroll", -120)
    assert out.log[-1] == ("press", "pagedown")
