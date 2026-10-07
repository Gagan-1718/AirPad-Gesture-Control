# AirControl — Gesture-Controlled Laptop (2-Day Build Plan)

> "AirControl" was the working title during planning. The project ships as **AirPad**.

Control music, slides, and games with hand gestures through your webcam.
Designed to be **lightweight** (no laptop overheating) and **accurate** (no false triggers).

---

## 1. Goal

Build one Python app that:

- Detects your hand through the webcam using MediaPipe (21 landmarks per hand)
- Recognizes a small set of reliable gestures
- Converts gestures into keyboard actions on your laptop
- Has 3 modes: **Media**, **Slides**, **Game**, switchable by gesture

**Final deliverable:** working app + demo video + GitHub repo with README.

---

## 2. Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.10 or 3.11 | Main language (MediaPipe is most stable here) |
| `mediapipe` | Hand landmark detection |
| `opencv-python` | Webcam capture and overlay display |
| `pyautogui` | Sending keystrokes to the OS |
| `numpy` | Distance and angle math |

Install:

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install mediapipe opencv-python pyautogui numpy
```

---

## 3. Folder Structure

```
aircontrol/
├── main.py            # Webcam loop, mode switching
├── tracker.py         # MediaPipe setup + landmark extraction
├── gestures.py        # Gesture recognition logic
├── smoothing.py       # Stability filter + cooldowns
├── actions.py         # Maps gestures to key presses per mode
├── config.py          # All tunable settings in one place
├── README.md
└── demo/              # Demo video and screenshots
```

---

## 4. Lightweight Rules (apply from the start)

| Setting | Value | Why |
|---|---|---|
| Camera resolution | 640×480 (try 320×240 if still hot) | Fewer pixels = less CPU |
| Frames processed | Every 2nd frame | ~15 fps is enough for gestures |
| `model_complexity` | `0` | Lightest hand model |
| `max_num_hands` | `1` | Half the work of two hands |
| Idle mode | Process 3 fps when no hand seen for 2 s | Laptop rests when you're not gesturing |
| Preview window | Toggle off with `v` key | Drawing every frame costs CPU |

**Hardware habits:** stay plugged in, keep vents uncovered, close heavy apps, work in 30–45 min sessions.

**Target:** CPU usage under ~30% while running.

---

## 5. Accuracy Rules (what makes it feel reliable)

1. **Few, distinct gestures.** Only use shapes that look very different from each other.
2. **Stability filter.** A gesture triggers only if it is detected in **at least 4 of the last 5 processed frames**.
3. **Cooldown.** After an action fires, ignore the same gesture for **0.8 s** (swipes: 1.0 s).
4. **Confidence thresholds.** `min_detection_confidence=0.7`, `min_tracking_confidence=0.6`.
5. **Scale-independent math.** Measure distances relative to hand size (wrist to middle-finger base), so it works whether your hand is near or far from the camera.
6. **Arm/disarm.** Actions only fire while a hand is clearly in frame; when the hand leaves, all buffers reset.

---

## 6. Gesture Set

| Gesture | How it's detected | Media mode | Slides mode | Game mode |
|---|---|---|---|---|
| ✋ Open palm (5 fingers) | All 5 fingers up | Play / Pause | — | — |
| ✊ Fist (0 fingers) | No fingers up | — | — | Jump (`space`) |
| ☝️ Index up (1 finger) | Only index up | Volume up | — | — |
| ✌️ Two fingers | Index + middle up | Volume down | — | — |
| 👉 Swipe right | Wrist x moves > 25% of frame width in < 0.4 s | Next track | Next slide | Move right |
| 👈 Swipe left | Same, opposite direction | Previous track | Previous slide | Move left |
| 🤟 Three fingers (hold 1.5 s) | Index + middle + ring up | **Switch mode** | **Switch mode** | **Switch mode** |

### Detection logic (core of accuracy)

- **Finger up (index, middle, ring, pinky):** fingertip `y` is above its PIP joint `y` (landmarks 8/6, 12/10, 16/14, 20/18). In image coordinates, "above" means a smaller `y`.
- **Thumb up:** compare thumb tip (4) and IP joint (3) along the **x-axis**, flipped depending on whether MediaPipe reports a Left or Right hand.
- **Hand size:** distance from wrist (0) to middle-finger base (9). Used to normalize all other distances.
- **Swipe:** keep the wrist x-position history for the last ~0.4 s. If net movement exceeds the threshold **and** the hand shape stays the same during the move, fire the swipe.

---

## 7. Phase Plan

### Phase 0 — Setup (Day 1, ~1 hour)

- [ ] Create the virtual environment and install packages
- [ ] Create the folder structure and `config.py`
- [ ] Test the webcam with a basic OpenCV window

**Done when:** a 640×480 webcam window opens and closes cleanly.

---

### Phase 1 — Hand Tracking (Day 1, ~2 hours)

- [ ] Set up MediaPipe Hands with the lightweight settings from Section 4
- [ ] Draw the 21 landmarks on the preview
- [ ] Add frame skipping and an FPS counter
- [ ] Add idle mode (lower processing rate when no hand is visible)

**Done when:** the hand is tracked smoothly at ~15 fps and the laptop stays only slightly warm after 10 minutes.

---

### Phase 2 — Gesture Recognition (Day 1, ~3 hours)

- [ ] Write `fingers_up()` returning a list like `[0,1,1,0,0]`
- [ ] Classify static gestures: palm, fist, 1 finger, 2 fingers, 3 fingers
- [ ] Add the stability filter (4 of 5 frames)
- [ ] Show the detected gesture name on screen

**Done when:** each gesture is recognized correctly **at least 9 out of 10 times** across different distances and lighting.

---

### Phase 3 — First Real Actions: Media Mode (Day 1 evening, ~2 hours)

- [ ] Map gestures to media keys with `pyautogui.press()`:
      `playpause`, `volumeup`, `volumedown`, `nexttrack`, `prevtrack`
- [ ] Add per-gesture cooldowns
- [ ] Test with Spotify or YouTube

**Done when:** you can pause, play, and change volume with no accidental triggers over a 5-minute session.

> Note: media keys work best on Windows. On macOS, use app shortcuts instead (e.g., `space` for play/pause in a focused browser tab).

---

### Phase 4 — Swipes + Slides Mode (Day 2 morning, ~3 hours)

- [ ] Track wrist position history over the last ~0.4 s
- [ ] Detect left and right swipes using the threshold from Section 6
- [ ] Slides mode: map swipes to `right` / `left` arrow keys
- [ ] Test with PowerPoint or Google Slides in presentation mode

**Done when:** 10 swipes in a row each move exactly one slide.

---

### Phase 5 — Game Mode + Mode Switching (Day 2 afternoon, ~3 hours)

- [ ] Game mode: fist = `space` (jump), swipes = arrow keys
- [ ] Test with the Chrome Dino game (`chrome://dino`) or a simple browser game
- [ ] Mode switch: hold three fingers for 1.5 s to cycle Media → Slides → Game
- [ ] Show the current mode and a progress bar for the hold gesture on screen

**Done when:** you can switch between all 3 modes and use each one without touching the keyboard.

---

### Phase 6 — Polish & Ship (Day 2 evening, ~2 hours)

- [ ] Move every threshold into `config.py`
- [ ] Add keyboard shortcuts: `v` toggles the preview, `q` quits
- [ ] Clean up the code and add comments
- [ ] Record a 60–90 second demo video showing all 3 modes
- [ ] Write the README: what it does, gestures table, install steps, demo GIF
- [ ] Push to GitHub

**Done when:** a friend can clone the repo, follow the README, and run it.

---

## 8. Testing Checklist

| Test | Pass criteria |
|---|---|
| Accuracy per gesture | ≥ 9/10 correct |
| False triggers | 0 accidental actions in 2 min of normal hand movement |
| Distance | Works from ~40 cm to ~1.5 m |
| Lighting | Works in normal room light and with a desk lamp |
| Heat | CPU < ~30%, laptop only warm after 15 min |
| Hand leaves frame | No stuck actions; buffers reset |

---

## 9. Common Problems & Fixes

| Problem | Fix |
|---|---|
| Gestures flicker | Increase the stability window to 6 frames |
| Same action fires repeatedly | Increase the cooldown |
| Swipes not detected | Lower the swipe threshold to 20% of frame width |
| Thumb detection wrong | Check the Left/Right handedness flip (webcam images are mirrored) |
| Laptop still hot | Drop to 320×240 and process every 3rd frame |
| Low light hurts tracking | Face a light source; avoid a bright window behind you |

---

## 10. Stretch Goals (only if time remains)

- **Air drawing mode:** index finger draws on a canvas, pinch lifts the pen
- **Mouse mode:** index finger moves the cursor, pinch clicks
- **Custom gesture config:** users remap gestures in a JSON file
- **System tray icon** so it runs in the background

---

## 11. Status

All phases (0-6) are complete. Changes made during the build:

- **MediaPipe API:** recent MediaPipe releases removed `mp.solutions.hands`, so
  tracking uses the Tasks `HandLandmarker` API (with a downloaded model file).
  `model_complexity` no longer exists.
- **Python:** MediaPipe now ships wheels for current Python versions, so
  3.10+ works (developed on 3.14).
- **Finger detection:** tip-to-wrist vs PIP-to-wrist distances instead of
  comparing `y` values, so tilted hands work. The thumb is ignored for
  finger-count poses.
- **Accuracy:** gestures fire once per pose (latching), static gestures need a
  still hand, and the return stroke after a swipe is ignored.
- **Redesign:** after testing the five-mode version (media, slides, PDF, mouse,
  game), mode switching proved to be the main friction. Version 1.0 replaces
  the modes with one always-on, touchpad-like mode. See the
  [changelog](../CHANGELOG.md).
