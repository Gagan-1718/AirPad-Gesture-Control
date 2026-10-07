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
SHOW_PREVIEW = True         # start with the camera preview on ('v' toggles)

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
GAME_STABILITY_WINDOW = 3   # game mode trades a little accuracy for speed
GAME_STABILITY_REQUIRED = 2

# --- Stillness (static gestures only fire while the hand is roughly still) ----
STILL_WINDOW_S = 0.25
STILL_THRESHOLD = 0.04      # frame fraction the wrist may wander in that window

# --- Cooldowns & holds ----------------------------------------------------------
GESTURE_COOLDOWN_S = 0.8
PLAYPAUSE_HOLD_S = 0.3      # palm must be held still briefly (avoids firing
                            # when you raise an open hand to swipe)
VOLUME_REPEAT_S = 0.25      # hold one/two fingers to keep changing volume
JUMP_COOLDOWN_S = 0.3       # game needs fast repeat jumps
MODE_SWITCH_HOLD_S = 1.5

# --- Swipes ---------------------------------------------------------------------
SWIPE_WINDOW_S = 0.4
SWIPE_THRESHOLD = 0.25      # frame-width fraction the wrist must travel
SWIPE_MAX_SLOPE = 0.6       # vertical / horizontal movement allowed
SWIPE_ARM_S = 0.2           # ignore movement right after a hand appears
SWIPE_COOLDOWN_S = 1.0      # applies to both directions
SWIPE_REVERSE_BLOCK_S = 1.5 # ignore the "return stroke" after a swipe
SWIPE_STATIC_BLOCK_S = 0.6  # no static gestures right after a swipe

# --- Modes --------------------------------------------------------------------
MODES = ["media", "slides", "game"]
START_MODE = "media"

# --- UI -----------------------------------------------------------------------
WINDOW_NAME = "AirPad"
ACTION_FLASH_S = 1.0
