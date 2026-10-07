import pytest

from gestures import classify, fingers_up, hand_size
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
