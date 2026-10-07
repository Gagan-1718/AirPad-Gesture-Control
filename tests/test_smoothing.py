from smoothing import StabilityFilter


def test_label_needs_enough_votes():
    f = StabilityFilter(window=5, required=4)
    assert [f.update("palm") for _ in range(4)] == [None, None, None, "palm"]


def test_single_frame_flicker_is_ignored():
    f = StabilityFilter(window=5, required=4)
    for _ in range(5):
        f.update("palm")
    assert f.update("fist") == "palm"


def test_reset_clears_history():
    f = StabilityFilter(window=5, required=4)
    for _ in range(5):
        f.update("palm")
    f.reset()
    assert f.update("palm") is None
