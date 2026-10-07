import pytest

from gestures import hand_size
from helpers import make_hand


def test_hand_size_is_wrist_to_middle_finger_base():
    assert hand_size(make_hand()) == pytest.approx(100)
    assert hand_size(make_hand(scale=0.5)) == pytest.approx(50)
