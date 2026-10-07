import pytest

from gestures import fingers_up, hand_size
from helpers import make_hand


def test_hand_size_is_wrist_to_middle_finger_base():
    assert hand_size(make_hand()) == pytest.approx(100)
    assert hand_size(make_hand(scale=0.5)) == pytest.approx(50)


@pytest.mark.parametrize("fingers", [
    (1, 1, 1, 1), (0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (0, 1, 0, 1),
])
def test_fingers_up_reads_each_finger(fingers):
    assert fingers_up(make_hand(fingers))[1:] == list(fingers)
