from gestures import fingers_up
from helpers import FakeOutput, make_hand
from mouse import MouseController


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


def run(mouse, hands, gesture="one", dt=1 / 30):
    """Feed hands at 30 fps; return the event labels."""
    events = []
    for i, hand in enumerate(hands, start=1):
        event = mouse.update(i * dt, hand, gesture, fingers_up(hand))
        if event:
            events.append(event)
    return events


def test_cursor_follows_the_hand():
    out = FakeOutput()
    run(MouseController(out), [make_hand((1, 0, 0, 0), cx=250 + 5 * k) for k in range(30)])
    moves = [e for e in out.log if e[0] == "move"]
    assert moves[-1][1] > moves[0][1]


def test_pinch_clicks():
    out = FakeOutput()
    point = make_hand((1, 0, 0, 0), thumb="out")
    events = run(MouseController(out), [point] * 5 + [pinch_hand()] * 4 + [point] * 5)
    assert events == ["Click"]
    assert out.events() == [("mouse_down",), ("mouse_up",)]


def test_right_click():
    out = FakeOutput()
    events = run(MouseController(out), [make_hand((1, 0, 0, 0), thumb="out")] * 5 + [right_click_hand()] * 6)
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
    run(MouseController(out), [fist] * 10, gesture="fist")
    assert out.events() == []


def test_two_fingers_scroll_and_freeze_the_cursor():
    out = FakeOutput()
    hands = [make_hand((1, 1, 0, 0), cy=400 - 4 * k) for k in range(20)]
    run(MouseController(out), hands, gesture="two")
    assert sum(e[1] for e in out.log if e[0] == "scroll") > 0
    assert not [e for e in out.log if e[0] == "move"]


def test_cursor_stays_off_the_screen_corners():
    out = FakeOutput()
    run(MouseController(out), [make_hand((1, 0, 0, 0), cx=40, cy=200)] * 60)
    x, y = [e for e in out.log if e[0] == "move"][-1][1:]
    assert x >= 2 and y >= 2
