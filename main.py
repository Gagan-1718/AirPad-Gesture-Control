"""AirPad: control your laptop with hand gestures.

Keys (with the AirPad window focused): q / Esc = quit.
"""
import argparse
import sys

import cv2

import config
from tracker import HAND_CONNECTIONS, HandTracker

GREEN = (80, 220, 100)
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


def draw_hand(img, hand):
    pts = [(int(x), int(y)) for x, y in hand.points]
    for a, b in HAND_CONNECTIONS:
        cv2.line(img, pts[a], pts[b], GREY, 2, cv2.LINE_AA)
    for p in pts:
        cv2.circle(img, p, 4, GREEN, -1, cv2.LINE_AA)


def run(args):
    cap = open_camera(args.camera)
    tracker = HandTracker()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera stopped delivering frames.")
                break
            if config.MIRROR:
                frame = cv2.flip(frame, 1)
            hand = tracker.process(frame)
            if hand is not None:
                draw_hand(frame, hand)
            cv2.imshow(config.WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if cv2.getWindowProperty(config.WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break               # window closed with the X button
    finally:
        cap.release()
        tracker.close()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Control your laptop with hand gestures.")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX, help="camera index")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
