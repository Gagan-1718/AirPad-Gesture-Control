import random

from gestures import fingers_up
from helpers import FakeOutput, make_hand
from mouse import MouseController


def point(cx=320, cy=400):
    """Index up with the thumb spread: drives the cursor."""
    return make_hand((1, 0, 0, 0), thumb="out", cx=cx, cy=cy)


def pinch_hand(cx=320, cy=400):
    """Thumb tip touching a half-bent index fingertip."""
    hand = make_hand((0, 0, 0, 0), cx=cx, cy=cy)
    hand.points[8] = (cx - 25, cy - 125)
    hand.points[4] = hand.points[8]
    return hand


def right_click_hand(cx=320, cy=400):
    """Index up, thumb tip touching a half-bent middle fingertip."""
    hand = make_hand((1, 0, 0, 0), cx=cx, cy=cy)
    hand.points[12] = (cx, cy - 125)
    hand.points[4] = hand.points[12]
    return hand


def run(mouse, hands, pose="point", dt=1 / 30, t0=0.0):
    """Feed hands at 30 fps; return the event labels."""
    events = []
    for i, hand in enumerate(hands, start=1):
        event = mouse.update(t0 + i * dt, hand, pose, fingers_up(hand))
        if event:
            events.append(event)
    return events


def moves(out):
    return [e for e in out.log if e[0] == "move"]


def test_cursor_moves_with_the_hand():
    out = FakeOutput()
    run(MouseController(out), [point(cx=250 + 3 * k) for k in range(30)])
    assert out.position()[0] > 1500


def test_cursor_continues_from_where_it_already_is():
    out = FakeOutput(position=(100, 100))
    run(MouseController(out), [point(cx=320 + 2 * k) for k in range(10)])
    assert 100 < out.position()[0] < 1000


def test_fast_moves_travel_further_than_slow_ones():
    slow, fast = FakeOutput(), FakeOutput()
    run(MouseController(slow), [point()] * 10 + [point(cx=320 + 64 * k / 30) for k in range(1, 31)])
    run(MouseController(fast), [point()] * 10 + [point(cx=320 + 64 * k / 3) for k in range(1, 4)])
    assert fast.position()[0] - 1500 > 1.5 * (slow.position()[0] - 1500)


def test_fist_lifts_the_cursor():
    out = FakeOutput()
    mouse = MouseController(out)
    run(mouse, [point(cx=320 + 2 * k) for k in range(15)])
    x = out.position()[0]
    run(mouse, [make_hand((0, 0, 0, 0), cx=350 - 4 * k) for k in range(15)], pose="fist", t0=0.5)
    assert out.position()[0] == x


def test_palm_does_not_move_the_cursor():
    out = FakeOutput()
    run(MouseController(out), [make_hand((1, 1, 1, 1), cx=250 + 5 * k) for k in range(30)], pose="palm")
    assert moves(out) == []


def test_pinch_clicks():
    out = FakeOutput()
    events = run(MouseController(out), [point()] * 5 + [pinch_hand()] * 4 + [point()] * 5)
    assert events == ["Click"]
    assert out.events() == [("mouse_down",), ("mouse_up",)]


def test_right_click():
    out = FakeOutput()
    events = run(MouseController(out), [point()] * 5 + [right_click_hand()] * 6)
    assert events == ["Right click"]
    assert out.events() == [("right_click",)]


def test_release_lets_go_of_a_dragged_button():
    out = FakeOutput()
    mouse = MouseController(out)
    run(mouse, [pinch_hand()] * 4)
    mouse.release()
    assert out.events() == [("mouse_down",), ("mouse_up",)]


def test_pointing_with_thumb_on_curled_middle_finger_does_not_click():
    out = FakeOutput()
    run(MouseController(out), [make_hand((1, 0, 0, 0), cx=250 + 3 * k) for k in range(30)])
    assert out.events() == []


def test_fist_does_not_click():
    out = FakeOutput()
    fist = make_hand((0, 0, 0, 0))
    fist.points[4] = (300, 305)     # thumb right next to the curled index tip
    run(MouseController(out), [fist] * 10, pose="fist")
    assert out.events() == []


def test_two_fingers_scroll_and_freeze_the_cursor():
    out = FakeOutput()
    hands = [make_hand((1, 1, 0, 0), cy=400 - 4 * k) for k in range(20)]
    run(MouseController(out), hands, pose="two")
    # Natural scrolling: hand moves up, page moves up, i.e. scroll down.
    assert sum(e[1] for e in out.log if e[0] == "scroll") < 0
    assert moves(out) == []


def test_cursor_stays_off_the_screen_corners():
    out = FakeOutput()
    run(MouseController(out), [point(cx=600 - 12 * k) for k in range(45)])
    assert out.position()[0] >= 2


def near_pinch(cx=320, cy=400):
    """Pointing with the thumb closing in on the index tip (not a click yet)."""
    hand = point(cx, cy)
    tip = hand.points[8]
    hand.points[4] = (tip[0] - 40, tip[1])
    return hand


def test_cursor_slows_down_as_the_fingers_close_for_a_pinch():
    normal, careful = FakeOutput(), FakeOutput()
    run(MouseController(normal), [point()] * 10 + [point(cx=320 + 2 * k) for k in range(1, 21)])
    run(MouseController(careful), [near_pinch()] * 10 + [near_pinch(cx=320 + 2 * k) for k in range(1, 21)])
    assert careful.position()[0] - 1500 < 0.5 * (normal.position()[0] - 1500)


def test_click_does_not_drag_the_cursor():
    out = FakeOutput()
    hands = [point()] * 10 + [pinch_hand(cx=320 + 3 * k) for k in range(1, 5)]
    run(MouseController(out), hands)
    down = out.log.index(("mouse_down",))
    assert not [e for e in out.log[down:] if e[0] == "move"]


def test_still_hand_does_not_jitter_the_cursor():
    random.seed(1)
    out = FakeOutput()
    hands = [point(cx=320 + random.gauss(0, 1), cy=400 + random.gauss(0, 1)) for _ in range(90)]
    run(MouseController(out), hands)
    xs = [e[1] for e in moves(out)] or [1500]
    assert max(xs) - min(xs) <= 6


def test_rewind_puts_the_cursor_back():
    out = FakeOutput()
    mouse = MouseController(out)
    run(mouse, [point()] * 10)
    run(mouse, [point(cy=400 - 15 * k) for k in range(1, 8)], t0=10 / 30)
    assert out.position() != (1500, 900)
    mouse.rewind(10 / 30)
    assert out.position() == (1500, 900)
