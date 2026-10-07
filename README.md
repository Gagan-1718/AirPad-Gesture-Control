# AirPad

Your hand is the touchpad. Control your laptop with webcam hand gestures.

> Work in progress. See the [project plan](docs/PROJECT_PLAN.md) for the roadmap.

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
python main.py --camera 1   # use another webcam
```

The hand model (~7.8 MB) downloads to `models/` on first run.
With the AirPad window focused, **q** or **Esc** quits.
