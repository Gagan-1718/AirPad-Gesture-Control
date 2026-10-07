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
PROCESS_FPS = 15            # hand-tracking rate; ~15 fps is enough for gestures

# --- Hand model (MediaPipe Tasks HandLandmarker) -------------------------------
MODEL_PATH = os.path.join(BASE_DIR, "models", "hand_landmarker.task")
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/latest/hand_landmarker.task")
NUM_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6

# --- UI -----------------------------------------------------------------------
WINDOW_NAME = "AirPad"
