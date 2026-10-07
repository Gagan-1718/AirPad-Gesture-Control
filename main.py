"""AirPad: control your laptop with hand gestures.

Keys (with the AirPad window focused): q / Esc = quit.
"""
import sys

import cv2

import config


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


def run():
    cap = open_camera(config.CAMERA_INDEX)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Camera stopped delivering frames.")
                break
            if config.MIRROR:
                frame = cv2.flip(frame, 1)
            cv2.imshow(config.WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


def main():
    run()


if __name__ == "__main__":
    main()
