# AirPad

Your hand is the touchpad. Control your laptop with webcam hand gestures.

> Work in progress. See the [project plan](docs/PROJECT_PLAN.md) for the roadmap.

## Gestures

| Gesture | Action |
|---|---|
| ✋ Open palm | Play / Pause |
| ☝️ Index finger up (hold to repeat) | Volume up |
| ✌️ Index + middle up (hold to repeat) | Volume down |

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Run

```bash
python main.py              # normal
python main.py --dry-run    # print actions instead of pressing keys
python main.py --camera 1   # use another webcam
```

The hand model (~7.8 MB) downloads to `models/` on first run.
With the AirPad window focused, **q** or **Esc** quits.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use synthetic hand landmarks, so they need no camera.
