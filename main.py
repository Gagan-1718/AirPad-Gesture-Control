"""AirPad: control your laptop with hand gestures.

Keys (with the AirPad window focused): 1-5 = pick mode, v = toggle preview,
q / Esc = quit.
Run with --dry-run to see gestures without sending any key presses.
"""
import argparse
import time

import cv2
import numpy as np

import config
from actions import DryRunOutput, GestureController, Output
from camera import Camera
from gestures import DISPLAY_NAMES, MotionTracker, classify, fingers_up, hand_size
from mouse import MouseController
from smoothing import StabilityFilter
from tracker import HAND_CONNECTIONS, HandTracker

GREEN = (80, 220, 100)
WHITE = (255, 255, 255)
YELLOW = (0, 220, 255)
GREY = (160, 160, 160)



def mode_title(mode):
    return f"{config.MODES.index(mode) + 1} {'PDF' if mode == 'pdf' else mode.title()}"


def stability_for(mode):
    if mode == "game":
        return config.GAME_STABILITY_WINDOW, config.GAME_STABILITY_REQUIRED
    return config.STABILITY_WINDOW, config.STABILITY_REQUIRED


def text(img, msg, org, color=WHITE, scale=0.6, thickness=1):
    cv2.putText(img, msg, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, msg, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def draw_hand(img, hand):
    pts = [(int(x), int(y)) for x, y in hand.points]
    for a, b in HAND_CONNECTIONS:
        cv2.line(img, pts[a], pts[b], GREY, 2, cv2.LINE_AA)
    for p in pts:
        cv2.circle(img, p, 4, GREEN, -1, cv2.LINE_AA)


def draw_overlay(img, state):
    h, w = img.shape[:2]
    if state["mode"] == "mouse":
        x0, y0, x1, y1 = config.MOUSE_BOX
        cv2.rectangle(img, (int(x0 * w), int(y0 * h)), (int(x1 * w), int(y1 * h)), YELLOW, 1)
    text(img, f"Mode: {mode_title(state['mode'])}", (10, 28), YELLOW, 0.8, 2)
    text(img, f"{state['fps']:.0f} fps{'  IDLE' if state['idle'] else ''}", (w - 140, 28), GREY)
    if state["fingers"] is not None:
        text(img, f"Gesture: {state['gesture']}", (10, 58))
        text(img, "Fingers: " + "".join(map(str, state["fingers"])), (10, 84), GREY, 0.5)
    if state["action"]:
        text(img, state["action"], (10, h - 50), GREEN, 0.9, 2)
    if state["hold"] > 0:
        cv2.rectangle(img, (10, h - 30), (10 + int((w - 20) * state["hold"]), h - 18), YELLOW, -1)
        cv2.rectangle(img, (10, h - 30), (w - 10, h - 18), WHITE, 1)
    text(img, "1-5: mode  v: preview  q: quit", (w - 255, h - 8), GREY, 0.45)


def status_panel(state):
    """Tiny window shown when the preview is off (keeps key handling alive)."""
    img = np.zeros((70, 320, 3), np.uint8)
    text(img, f"Mode: {mode_title(state['mode'])}", (10, 28), YELLOW, 0.7, 2)
    text(img, state["action"] or ("idle" if state["idle"] else state["gesture"]), (10, 56), GREEN, 0.55)
    return img


def run(args):
    output = DryRunOutput() if args.dry_run else Output()
    camera = Camera(args.camera)
    tracker = HandTracker()
    controller = GestureController(output)
    mouse = MouseController(output)
    stability = StabilityFilter(*stability_for(controller.mode))
    motion = MotionTracker()
    mode = controller.mode

    show_preview = config.SHOW_PREVIEW
    cv2.namedWindow(config.WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    last_process = 0.0
    last_hand_seen = time.monotonic()
    had_hand = False
    fps, fps_count, fps_start = 0.0, 0, time.monotonic()
    action, action_until = "", 0.0
    shown = False
    try:
        while True:
            now = time.monotonic()
            idle = now - last_hand_seen > config.IDLE_AFTER_S
            if idle:
                interval = 1.0 / config.IDLE_FPS
            elif controller.mode == "mouse":
                interval = 1.0 / config.MOUSE_PROCESS_FPS
            else:
                interval = 1.0 / config.PROCESS_FPS
            if now - last_process < interval:
                key = cv2.waitKey(5) & 0xFF       # rest until the next frame is due
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
                    stable = stability.update(classify(fingers))
                    motion.update(now, *hand.norm(0))
                    swipe = motion.detect_swipe(now)
                    if swipe:
                        motion.clear_history()
                    fired = controller.update(now, stable, motion.is_still(now), swipe)
                    if controller.mode == "mouse":
                        swipe = None
                        fired = fired or mouse.update(now, hand, stable, fingers)
                    gesture_name = DISPLAY_NAMES.get(swipe or stable, "...")
                    if fired:
                        action, action_until = fired, now + config.ACTION_FLASH_S
                        if fired != "Scroll":   # scrolling fires every frame
                            print(fired)
                elif had_hand:              # disarm: hand left, reset everything
                    had_hand = False
                    stability.reset()
                    motion.reset()
                    controller.hand_lost()
                    mouse.release()

                if controller.mode != mode:
                    mode = controller.mode
                    stability.configure(*stability_for(mode))
                    mouse.release()

                fps_count += 1
                if now - fps_start >= 1.0:
                    fps, fps_count, fps_start = fps_count / (now - fps_start), 0, now

                state = {
                    "fps": fps, "idle": idle, "fingers": fingers, "gesture": gesture_name,
                    "action": action if now < action_until else "",
                    "mode": controller.mode, "hold": controller.hold_progress,
                }
                if show_preview:
                    if hand is not None:
                        draw_hand(frame, hand)
                    draw_overlay(frame, state)
                    cv2.imshow(config.WINDOW_NAME, frame)
                else:
                    cv2.imshow(config.WINDOW_NAME, status_panel(state))
                shown = True
                key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break
            if key == ord("v"):
                show_preview = not show_preview
            if ord("1") <= key < ord("1") + len(config.MODES):
                controller.set_mode(config.MODES[key - ord("1")])
                action, action_until = f"Mode: {mode_title(controller.mode)}", time.monotonic() + config.ACTION_FLASH_S
            if shown and cv2.getWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break               # window closed with the X button
    finally:
        mouse.release()             # never leave the mouse button held down
        camera.close()
        tracker.close()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Control your laptop with hand gestures.")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX, help="camera index")
    parser.add_argument("--dry-run", action="store_true", help="print actions instead of pressing keys")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
