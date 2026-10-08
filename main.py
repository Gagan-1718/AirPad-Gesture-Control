"""AirPad: use your laptop with hand gestures, like an air touchpad.

Keys (with the AirPad window focused): p = pause / resume, v = toggle preview,
q / Esc = quit.
Run with --dry-run to see gestures without sending any input.
"""
import argparse
import ctypes
import sys
import time

import cv2
import numpy as np

import config
from actions import DryRunOutput, GestureController, Output, PauseToggle
from camera import Camera
from gestures import DISPLAY_NAMES, MotionTracker, classify, fingers_up, hand_size
from mouse import MouseController
from smoothing import StabilityFilter
from tracker import HAND_CONNECTIONS, HandTracker

GREEN = (80, 220, 100)
WHITE = (255, 255, 255)
YELLOW = (0, 220, 255)
GREY = (160, 160, 160)
RED = (60, 60, 230)


def text(img, msg, org, color=WHITE, scale=0.45, thickness=1):
    cv2.putText(img, msg, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, msg, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def draw_hand(img, hand, scale):
    pts = [(int(x * scale), int(y * scale)) for x, y in hand.points]
    for a, b in HAND_CONNECTIONS:
        cv2.line(img, pts[a], pts[b], GREY, 1, cv2.LINE_AA)
    for p in pts:
        cv2.circle(img, p, 2, GREEN, -1, cv2.LINE_AA)


def draw_overlay(img, state):
    h, w = img.shape[:2]
    text(img, f"{state['fps']:.0f} fps{'  idle' if state['idle'] else ''}", (w - 85, 16), GREY, 0.4)
    if state["fingers"] is not None:
        text(img, state["gesture"], (8, 18), YELLOW, 0.5)
        text(img, "".join(map(str, state["fingers"])), (8, 36), GREY, 0.4)
    if state["action"]:
        text(img, state["action"], (8, h - 26), GREEN, 0.6, 2)
    if state["hold"] > 0:
        cv2.rectangle(img, (8, h - 16), (8 + int((w - 16) * state["hold"]), h - 10), YELLOW, -1)
        cv2.rectangle(img, (8, h - 16), (w - 8, h - 10), WHITE, 1)
    if state["paused"]:
        cv2.rectangle(img, (0, 0), (w - 1, h - 1), RED, 4)
        text(img, "PAUSED", (w // 2 - 55, h // 2), RED, 1.0, 2)
        text(img, "hold 3 fingers still to resume", (w // 2 - 120, h // 2 + 26), WHITE, 0.5)


def status_panel(state):
    """Tiny window shown when the preview is off (keeps key handling alive)."""
    img = np.zeros((44, 240, 3), np.uint8)
    msg = state["action"] or ("idle" if state["idle"] else state["gesture"] or "no hand")
    if state["paused"]:
        text(img, "AirPad: PAUSED", (8, 27), RED, 0.5)
    else:
        text(img, f"AirPad: {msg}", (8, 27), GREEN, 0.5)
    return img


def run(args):
    if sys.platform == "win32":
        ctypes.windll.winmm.timeBeginPeriod(1)   # 1 ms timers: waitKey(1) really waits ~1 ms
    output = DryRunOutput() if args.dry_run else Output()
    camera = Camera(args.camera)
    tracker = HandTracker()
    controller = GestureController(output)
    mouse = MouseController(output)
    pause = PauseToggle(config.START_PAUSED)
    stability = StabilityFilter(config.STABILITY_WINDOW, config.STABILITY_REQUIRED)
    motion = MotionTracker()

    show_preview = config.SHOW_PREVIEW
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    last_process = 0.0
    last_hand_seen = time.monotonic()
    had_hand = False
    fps, fps_count, fps_start = 0.0, 0, time.monotonic()
    action, action_until = "", 0.0
    shown = False
    print("AirPad running. Focus the AirPad window and press q to quit.")

    try:
        while True:
            now = time.monotonic()
            idle = now - last_hand_seen > config.IDLE_AFTER_S
            if idle and now - last_process < 1.0 / config.IDLE_FPS:
                key = cv2.waitKey(20) & 0xFF      # rest between idle checks
            else:
                frame = camera.read()             # waits for the next fresh frame
                if frame is None:
                    print("Camera stopped delivering frames.")
                    break
                now = last_process = time.monotonic()
                if config.MIRROR:
                    frame = cv2.flip(frame, 1)

                hand = tracker.process(frame)
                if hand is not None and hand_size(hand) < config.MIN_HAND_SIZE * hand.frame_h:
                    hand = None         # too far away to trust

                fingers, gesture_name = None, ""
                if hand is not None:
                    last_hand_seen = now
                    had_hand = True
                    fingers = fingers_up(hand)
                    raw = classify(hand, fingers)
                    pose = stability.update(raw)
                    motion.update(now, *hand.norm(0), raw)
                    still = motion.is_still(now)
                    fired = pause.update(now, pose, still)
                    if fired:                       # just paused or resumed: start clean
                        motion.clear_history()
                        controller.hand_lost()
                        mouse.release()
                    elif not pause.paused:
                        swipe = motion.detect_swipe(now)
                        if swipe:
                            motion.clear_history()
                        fired = controller.update(now, pose, still, swipe)
                        fired = mouse.update(now, hand, pose, fingers) or fired
                        if swipe and swipe[1] == "point" and swipe[0] in ("swipe_up", "swipe_down"):
                            mouse.rewind(now - config.SWIPE_WINDOW_S)   # a page flick, not a cursor move
                    gesture_name = DISPLAY_NAMES.get(pose, "...")
                    if fired:
                        action, action_until = fired, now + config.ACTION_FLASH_S
                        if fired != "Scroll":   # scrolling fires every frame
                            print(fired)
                elif had_hand:              # hand left: let go of everything
                    had_hand = False
                    stability.reset()
                    motion.reset()
                    controller.hand_lost()
                    mouse.release()
                    pause.hand_lost()

                fps_count += 1
                if now - fps_start >= 1.0:
                    fps, fps_count, fps_start = fps_count / (now - fps_start), 0, now

                state = {
                    "fps": fps, "idle": idle, "fingers": fingers, "gesture": gesture_name,
                    "action": action if now < action_until else "",
                    "hold": pause.progress or controller.hold_progress,
                    "paused": pause.paused,
                }
                if show_preview:
                    s = config.PREVIEW_SCALE
                    view = cv2.resize(frame, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
                    if hand is not None:
                        draw_hand(view, hand, s)
                    draw_overlay(view, state)
                    cv2.imshow(config.WINDOW_NAME, view)
                else:
                    cv2.imshow(config.WINDOW_NAME, status_panel(state))
                if not shown and config.PREVIEW_ON_TOP:
                    cv2.setWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_TOPMOST, 1)
                shown = True
                key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break
            if key == ord("v"):
                show_preview = not show_preview
            if key == ord("p"):
                action, action_until = pause.flip(), time.monotonic() + config.ACTION_FLASH_S
                print(action)
                controller.hand_lost()
                mouse.release()
            if shown and cv2.getWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break               # window closed with the X button
    finally:
        mouse.release()             # never leave the mouse button held down
        camera.close()
        tracker.close()
        cv2.destroyAllWindows()
        if sys.platform == "win32":
            ctypes.windll.winmm.timeEndPeriod(1)


def main():
    parser = argparse.ArgumentParser(description="Use your laptop with hand gestures.")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX, help="camera index")
    parser.add_argument("--dry-run", action="store_true", help="print actions instead of sending input")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
