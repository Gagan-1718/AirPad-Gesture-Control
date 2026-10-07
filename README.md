# AirPad

**Your hand is the touchpad.** Use your laptop with hand gestures through your
webcam: move the cursor, click, drag, scroll, flip slides and PDF pages, go back
in the browser, switch apps and control media. One mode, always on, no switching.

It tracks at the camera's full 30 fps while your hand is in view, using about 5%
of the CPU on a modern laptop, and drops to 5 fps when no hand is visible.

<!-- demo GIF goes here: ![demo](demo/demo.gif) -->

## Gestures

### Cursor (like a touchpad)

| Gesture | Action |
|---|---|
| ☝️ Point (index up) and move | Move the cursor |
| ✊ Fist | "Lift your finger": the cursor stays put while you reposition your hand |
| 🤏 Pinch thumb + index | Left click (pinch twice quickly = double-click) |
| 🤏 Pinch and hold, then move | Drag |
| Pinch thumb + middle tip, index up | Right click |
| ✌️ Two fingers up, move hand up / down | Scroll (the page follows your hand) |

The cursor speeds up with your hand: move slowly for precision, flick to cross
the screen. It slows down as your fingers close in for a pinch, so clicks land
where you aim.

### Swipes (quick sideways movement)

| Hand shape | Swipe right | Swipe left |
|---|---|---|
| ✋ Open palm | Next (→ key): slide, PDF page, photo | Previous (← key) |
| ✌️ Two fingers | Browser forward (Alt+→) | Browser back (Alt+←) |
| 🤟 Three fingers (index + middle + ring) | Switch to last app (Alt+Tab) | Switch to last app |

## Install

Python 3.10 or newer (tested on 3.14 with MediaPipe 1.1).

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Run

```bash
python main.py              # normal
python main.py --dry-run    # print actions instead of sending input
python main.py --camera 1   # use another webcam
```

The hand model (~7.8 MB) downloads to `models/` on first run.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use synthetic hand landmarks, so they need no camera.
