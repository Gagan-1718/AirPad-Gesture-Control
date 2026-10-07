"""All tunable settings for AirPad live here."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Camera -----------------------------------------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_FPS = 30
MIRROR = True               # flip like a mirror so "swipe right" means your right

# --- CPU budget ---------------------------------------------------------------
PROCESS_FPS = 30            # hand-tracking rate while a hand is visible
IDLE_FPS = 3                # rate when no hand has been seen for IDLE_AFTER_S
IDLE_AFTER_S = 2.0

# --- Preview window -------------------------------------------------------------
SHOW_PREVIEW = True         # 'v' toggles between preview and a tiny status panel

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

# --- Pose detection -----------------------------------------------------------
# A finger is "up" when tip-to-wrist distance > ratio * PIP-to-wrist distance.
FINGER_EXTENDED_RATIO = 1.15
THUMB_OUT_RATIO = 0.6       # hand sizes from thumb tip to middle-finger base
THUMB_VERTICAL = 0.45       # hand sizes the thumb tip must be above / below its
                            # base for thumbs-up / thumbs-down
STABILITY_WINDOW = 5        # a pose counts once it wins 4 of the last 5 frames
STABILITY_REQUIRED = 4
STILL_WINDOW_S = 0.25
STILL_THRESHOLD = 0.04      # frame fraction the wrist may wander and count as still

# --- Cursor (relative, like a touchpad) ------------------------------------------
# Cursor travel = hand travel * speed, where speed grows with hand speed:
# slow movements are precise, fast flicks cross the screen.
CURSOR_MIN_SPEED = 1.2      # screens per frame moved, for slow hand movement
CURSOR_MAX_SPEED = 4.0      # ... for fast hand movement
CURSOR_ACCEL_START = 0.15   # hand speed (frames / s) where acceleration starts
CURSOR_ACCEL_FULL = 1.2     # hand speed where it reaches CURSOR_MAX_SPEED
CURSOR_DEADZONE = 0.015     # hand speed below which the cursor holds still
CURSOR_SMOOTH_MIN_CUTOFF = 1.2  # lower = steadier when still, more lag
CURSOR_SMOOTH_BETA = 0.03       # higher = less lag when moving fast

# --- Clicks (pinches) -------------------------------------------------------------
PINCH_ON = 0.25             # hand sizes between fingertips to count as a pinch
PINCH_OFF = 0.40            # must open past this to release (prevents flicker)
PINCH_FRAMES = 2            # consecutive pinch frames before clicking
PINCH_MIN_REACH = 0.75      # pinching finger's tip-to-wrist / PIP-to-wrist; below
                            # this it is curled into a fist, not pinching

# --- Scrolling (two fingers up, move hand up / down) ---------------------------
MOUSE_SCROLL_GAIN = 4000    # wheel units per frame-height of hand movement
MOUSE_SCROLL_DEADZONE = 0.004  # ignore tiny hand jitter while scrolling

# --- Media -------------------------------------------------------------------------
PLAYPAUSE_HOLD_S = 0.3      # open palm held still this long = play / pause
VOLUME_REPEAT_S = 0.25      # thumbs up / down: one volume step per this interval
GESTURE_COOLDOWN_S = 0.8

# --- Swipes ---------------------------------------------------------------------
SWIPE_WINDOW_S = 0.4
SWIPE_THRESHOLD = 0.25      # frame-width fraction the hand must travel
SWIPE_MAX_SLOPE = 0.6       # vertical / horizontal movement allowed
SWIPE_ARM_S = 0.2           # ignore movement right after a hand appears
SWIPE_COOLDOWN_S = 1.0      # applies to both directions
SWIPE_REVERSE_BLOCK_S = 1.5 # ignore the "return stroke" after a swipe
SWIPE_STATIC_BLOCK_S = 0.6  # no palm / thumb actions right after a swipe

# --- UI -----------------------------------------------------------------------
WINDOW_NAME = "AirPad"
ACTION_FLASH_S = 1.0
