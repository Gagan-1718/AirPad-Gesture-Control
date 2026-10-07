from smoothing import Cooldowns, OneEuroFilter, StabilityFilter


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


def test_cooldown_blocks_until_it_expires():
    c = Cooldowns()
    assert c.ready("palm", now=0.0)
    c.trigger("palm", now=0.0, seconds=0.8)
    assert not c.ready("palm", now=0.5)
    assert c.ready("palm", now=0.8)


def test_cooldowns_are_independent_per_key():
    c = Cooldowns()
    c.trigger("palm", now=0.0, seconds=1.0)
    assert c.ready("fist", now=0.1)


def test_one_euro_filter_removes_jitter():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0)
    out = [f(i / 30, 100 + (1 if i % 2 else -1)) for i in range(60)]
    assert max(out[30:]) - min(out[30:]) < 0.5


def test_one_euro_filter_follows_fast_moves():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.05)
    for i in range(30):
        f(i / 30, 0.0)
    for i in range(30, 33):
        value = f(i / 30, 500.0)
    assert value > 450
