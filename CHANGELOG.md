# Changelog

## 1.0.0

Laptop-style redesign: one always-on mode that works like a touchpad.

### Added
- Touchpad-style relative cursor with acceleration, smoothed by a 1 Euro filter.
- Fist "lifts" the cursor so you can reposition your hand.
- Cursor slows down as the fingers close for a pinch; holds still as a click starts.
- Swipes depend on hand shape: palm = next/previous, two fingers = browser
  back/forward, three fingers = switch app.
- Thumbs up / down for volume.
- Natural scrolling with two fingers.
- Background camera thread, 1 ms timers on Windows, tracking on every frame
  while a hand is visible.
- Half-size, always-on-top preview window.
- Lint and test CI on GitHub Actions.

### Removed
- Mode switching and the separate media, slides, PDF, mouse and game modes.

## 0.2.0

- Five modes (media, slides, PDF, mouse, game), switched by holding three
  fingers or pressing 1-5.
- Mouse mode with pinch click, drag, right click and two-finger scroll.
- PDF mode (page turns and scrolling) and game mode (fist = jump).
- Preview toggle with `v`.

## 0.1.0

- Hand tracking with MediaPipe HandLandmarker, idle mode, FPS counter.
- Finger detection, pose classification and a stability filter.
- Media controls: play/pause, volume, next/previous track.
- Swipe detection with return-stroke and edge-entry filtering.
