"""All tunable settings for AirPad live here."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Camera -----------------------------------------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_FPS = 30
MIRROR = True               # flip like a mirror so moving right means your right

# --- CPU budget ---------------------------------------------------------------
PROCESS_FPS = 15            # hand-tracking rate while a hand is visible
IDLE_FPS = 3                # rate when no hand has been seen for IDLE_AFTER_S
IDLE_AFTER_S = 2.0

# --- Hand model (MediaPipe Tasks HandLandmarker) -------------------------------
MODEL_PATH = os.path.join(BASE_DIR, "models", "hand_landmarker.task")
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/latest/hand_landmarker.task")
NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6
MIN_HAND_SIZE = 0.05        # frame-height fraction; smaller hands (far away /
                            # people in the background) are ignored

# --- Finger detection ---------------------------------------------------------
# A finger is "up" when tip-to-wrist distance > ratio * PIP-to-wrist distance.
# Rotation-independent, unlike comparing raw y values.
FINGER_EXTENDED_RATIO = 1.15
THUMB_OUT_RATIO = 0.6       # hand sizes from thumb tip to middle-finger base

# --- Stability filter (gesture must win `required` of the last `window` frames)
STABILITY_WINDOW = 5
STABILITY_REQUIRED = 4

# --- Cooldowns ------------------------------------------------------------------
GESTURE_COOLDOWN_S = 0.8

# --- UI -----------------------------------------------------------------------
WINDOW_NAME = "AirPad"
ACTION_FLASH_S = 1.0
