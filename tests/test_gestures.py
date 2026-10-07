import pytest

from gestures import MotionTracker, classify, fingers_up, hand_size
from helpers import make_hand


def test_hand_size_is_wrist_to_middle_finger_base():
    assert hand_size(make_hand()) == pytest.approx(100)
    assert hand_size(make_hand(scale=0.5)) == pytest.approx(50)


@pytest.mark.parametrize("fingers", [
    (1, 1, 1, 1), (0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (0, 1, 0, 1),
])
def test_fingers_up_reads_each_finger(fingers):
    assert fingers_up(make_hand(fingers))[1:] == list(fingers)


def test_thumb_spread_and_tucked():
    assert fingers_up(make_hand(thumb="out"))[0] == 1
    assert fingers_up(make_hand(thumb="in"))[0] == 0


@pytest.mark.parametrize("scale", [0.4, 1.0, 2.0])
def test_detection_is_scale_independent(scale):
    assert fingers_up(make_hand((1, 1, 0, 0), thumb="out", scale=scale)) == [1, 1, 1, 0, 0]


@pytest.mark.parametrize("angle", [-60, -30, 30, 90])
def test_detection_works_on_a_tilted_hand(angle):
    assert fingers_up(make_hand((1, 0, 1, 0), angle=angle))[1:] == [1, 0, 1, 0]


@pytest.mark.parametrize("fingers, pose", [
    ((1, 1, 1, 1), "palm"),
    ((0, 0, 0, 0), "fist"),
    ((1, 0, 0, 0), "one"),
    ((1, 1, 0, 0), "two"),
    ((1, 1, 1, 0), "three"),
    ((0, 1, 0, 1), "other"),
])
@pytest.mark.parametrize("thumb", ["in", "out"])
def test_classify_ignores_the_thumb(fingers, pose, thumb):
    assert classify(fingers_up(make_hand(fingers, thumb))) == pose


def track(motion, points, dt=1 / 15):
    """Feed (x, y) wrist positions at 15 fps; return the last swipe seen."""
    swipe = None
    for i, (x, y) in enumerate(points, start=1):
        motion.update(i * dt, x, y)
        swipe = motion.detect_swipe(i * dt) or swipe
    return swipe


def move(x0, x1, frames, y0=0.5, y1=None):
    y1 = y0 if y1 is None else y1
    return [(x0 + (x1 - x0) * k / frames, y0 + (y1 - y0) * k / frames) for k in range(1, frames + 1)]


def test_fast_move_right_is_a_swipe():
    assert track(MotionTracker(), [(0.3, 0.5)] * 6 + move(0.3, 0.7, 4)) == "swipe_right"


def test_fast_move_left_is_a_swipe():
    assert track(MotionTracker(), [(0.7, 0.5)] * 6 + move(0.7, 0.3, 4)) == "swipe_left"


def test_slow_move_is_not_a_swipe():
    assert track(MotionTracker(), [(0.3, 0.5)] * 6 + move(0.3, 0.7, 30)) is None


def test_diagonal_move_is_not_a_swipe():
    assert track(MotionTracker(), [(0.3, 0.3)] * 6 + move(0.3, 0.6, 4, 0.3, 0.8)) is None


def test_hand_entering_from_the_edge_is_not_a_swipe():
    assert track(MotionTracker(), move(0.05, 0.5, 4) + [(0.5, 0.5)] * 10) is None


def test_still_hand_is_still():
    m = MotionTracker()
    track(m, [(0.5, 0.5)] * 6)
    assert m.is_still(6 / 15)


def test_moving_hand_is_not_still():
    m = MotionTracker()
    track(m, move(0.3, 0.6, 6))
    assert not m.is_still(6 / 15)
