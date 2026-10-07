import pyautogui
import pytest

SCREEN = pyautogui.Size(3000, 1800)   # FakeOutput starts the cursor at its centre


@pytest.fixture(autouse=True)
def fixed_screen_size(monkeypatch):
    """Make cursor tests independent of the machine's real screen size."""
    monkeypatch.setattr(pyautogui, "size", lambda: SCREEN)
