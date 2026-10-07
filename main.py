"""AirPad: control your laptop with hand gestures.

Keys (with the AirPad window focused): q / Esc = quit.
Run with --dry-run to see gestures without sending any key presses.
"""
import argparse
import sys
import time

import cv2

import config
from actions import GestureController, press_key
from gestures import DISPLAY_NAMES, MotionTracker, classify, fingers_up, hand_size
from smoothing import StabilityFilter
from tracker import HAND_CONNECTIONS, HandTracker

GREEN = (80, 220, 100)
WHITE = (255, 255, 255)
YELLOW = (0, 220, 255)
GREY = (160, 160, 160)


def open_camera(index):
    # DirectShow opens much faster than the default MSMF backend on Windows.
    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {index}. Is another app using it?")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
    return cap


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
    text(img, f"Mode: {state['mode'].title()}", (10, 28), YELLOW, 0.8, 2)
    text(img, f"{state['fps']:.0f} fps{'  IDLE' if state['idle'] else ''}", (w - 140, 28), GREY)
    if state["fingers"] is not None:
        text(img, f"Gesture: {state['gesture']}", (10, 58))
        text(img, "Fingers: " + "".join(map(str, state["fingers"])), (10, 84), GREY, 0.5)
    if state["action"]:
        text(img, state["action"], (10, h - 50), GREEN, 0.9, 2)
    if state["hold"] > 0:
        cv2.rectangle(img, (10, h - 30), (10 + int((w - 20) * state["hold"]), h - 18), YELLOW, -1)
        cv2.rectangle(img, (10, h - 30), (w - 10, h - 18), WHITE, 1)


def run(args):
    send = (lambda key: print(f"[dry-run] {key}")) if args.dry_run else press_key
    cap = open_camera(args.camera)
    tracker = HandTracker()
    controller = GestureController(send)
    stability = StabilityFilter(config.STABILITY_WINDOW, config.STABILITY_REQUIRED)
    motion = MotionTracker()
    last_process = 0.0
    last_hand_seen = time.monotonic()
    had_hand = False
    fps, fps_count, fps_start = 0.0, 0, time.monotonic()
    action, action_until = "", 0.0
    shown = False
    try:
        while True:
            if not cap.grab():          # grab without decoding; cheap for skipped frames
                print("Camera stopped delivering frames.")
                break
            now = time.monotonic()
            idle = now - last_hand_seen > config.IDLE_AFTER_S
            interval = 1.0 / (config.IDLE_FPS if idle else config.PROCESS_FPS)
            if now - last_process >= interval:
                last_process = now
                ok, frame = cap.retrieve()
                if not ok:
                    continue
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
                    gesture_name = DISPLAY_NAMES.get(swipe or stable, "...")
                    if fired:
                        action, action_until = fired, now + config.ACTION_FLASH_S
                        print(fired)
                elif had_hand:              # disarm: hand left, reset everything
                    had_hand = False
                    stability.reset()
                    motion.reset()
                    controller.hand_lost()

                fps_count += 1
                if now - fps_start >= 1.0:
                    fps, fps_count, fps_start = fps_count / (now - fps_start), 0, now

                state = {
                    "fps": fps, "idle": idle, "fingers": fingers, "gesture": gesture_name,
                    "action": action if now < action_until else "",
                    "mode": controller.mode, "hold": controller.hold_progress,
                }
                if hand is not None:
                    draw_hand(frame, hand)
                draw_overlay(frame, state)
                cv2.imshow(config.WINDOW_NAME, frame)
                shown = True
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if shown and cv2.getWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break               # window closed with the X button
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Control your laptop with hand gestures.")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX, help="camera index")
    parser.add_argument("--dry-run", action="store_true", help="print actions instead of pressing keys")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
