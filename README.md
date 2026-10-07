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

### Media

| Gesture | Action |
|---|---|
| ✋ Open palm, hold still for ½ s | Play / Pause (a bar fills while you hold) |
| 👍 Thumbs up, hold | Volume up (repeats while held) |
| 👎 Thumbs down, hold | Volume down (repeats while held) |

### Tips

- Keep your palm facing the camera, 40 cm to 1.5 m away.
- Swipe right away, without holding the open palm still first. Holding it
  still triggers play/pause.
- One-shot gestures fire once per pose. To fire again, change the pose or
  lower your hand.
- Bringing your hand back after a swipe is ignored, so "next, next, next" works.
- Swipes and keys go to the **focused window**. Pinch-click a window first to
  focus it, just like with a mouse.
- **PDFs:** palm swipes send the arrow keys. For one swipe = one page, set the
  viewer to fit a whole page (Edge/Chrome PDF viewer: `Ctrl + \`). Or scroll
  with two fingers.
- **PowerPoint slideshow:** palm swipes change slides. A pinch-click also
  advances, like a mouse click.

## How it works

1. **Camera thread** (`camera.py`) keeps only the newest webcam frame, so
   nothing waits in a buffer.
2. **Hand tracking** (`tracker.py`) runs MediaPipe HandLandmarker in video
   mode and returns 21 landmarks per frame.
3. **Pose** (`gestures.py`): a finger is "up" when its tip is further from the
   wrist than its middle joint. Distances are measured in hand sizes, so it
   works near or far and with a tilted hand. A pose only counts once it wins
   3 of the last 4 frames.
4. **Motion** (`gestures.py`): a short history of wrist positions detects
   swipes, which hand shape made them, and whether the hand is still.
5. **Cursor** (`mouse.py`): relative movement with acceleration, smoothed by a
   1 Euro filter. Pinches press and release the mouse button.
6. **Actions** (`actions.py`): swipes and held poses become key presses, with
   cooldowns and "fire once per pose" latching so nothing repeats by accident.

## Install

Python 3.10 or newer (tested on 3.14 with MediaPipe 1.1).

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

> Keep the venv out of OneDrive/Dropbox folders. Syncing thousands of
> package files is slow.

## Run

```bash
python main.py              # normal
python main.py --dry-run    # print actions instead of sending input
python main.py --camera 1   # use another webcam
```

The hand model (~7.8 MB) downloads to `models/` on first run.

A small preview window stays on top of other windows. With it focused, **v**
switches to a tiny status bar and back, and **q** or **Esc** quits. Emergency
stop: slam the real mouse into a screen corner.

## Tuning

Every threshold is in `config.py`. Common fixes:

| Problem | Setting |
|---|---|
| Cursor too slow / too fast | `CURSOR_MIN_SPEED` (precise moves), `CURSOR_MAX_SPEED` (flicks) |
| Cursor shaky when still | raise `CURSOR_DEADZONE` or lower `CURSOR_SMOOTH_MIN_CUTOFF` |
| Cursor lags behind | raise `CURSOR_SMOOTH_BETA` (e.g. 0.06) |
| Clicks missed / too many | adjust `PINCH_ON` (lower = harder to click) |
| Scroll too fast / wrong way | `SCROLL_GAIN`, `SCROLL_NATURAL` |
| Swipes not detected | `SWIPE_THRESHOLD = 0.15` |
| Gestures flicker | `STABILITY_WINDOW = 5`, `STABILITY_REQUIRED = 4` |
| Fingers misread as up/down | adjust `FINGER_EXTENDED_RATIO` (watch the digits under the pose name) |
| Play/pause triggers by accident | raise `PLAYPAUSE_HOLD_S` |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use synthetic hand landmarks, so they need no camera.
