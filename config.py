"""All tunable settings for AirPad live here.

Distances marked "frame fraction" are relative to the camera frame (0..1).
Distances marked "hand sizes" are relative to wrist -> middle-finger-base length,
so they work the same whether your hand is near or far from the camera.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Camera -----------------------------------------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_FPS = 30
MIRROR = True               # flip like a mirror so "swipe right" means your right

# --- CPU budget ---------------------------------------------------------------
# With a hand in view every camera frame is processed (~30 fps) for a lag-free
# cursor. With no hand for IDLE_AFTER_S it drops to IDLE_FPS to keep the laptop cool.
IDLE_FPS = 5
IDLE_AFTER_S = 1.5

# --- Preview window -------------------------------------------------------------
SHOW_PREVIEW = True         # 'v' toggles between preview and a tiny status panel
PREVIEW_SCALE = 0.5         # half-size preview is cheaper and stays out of the way
PREVIEW_ON_TOP = True

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
STABILITY_WINDOW = 4        # a pose counts once it wins 3 of the last 4 frames
STABILITY_REQUIRED = 3      # (~100 ms at 30 fps)
STILL_WINDOW_S = 0.25
STILL_THRESHOLD = 0.04      # frame fraction the wrist may wander and count as still

# --- Cursor (relative, like a touchpad) ------------------------------------------
# Cursor travel = hand travel * speed, where speed grows with hand speed:
# slow movements are precise, fast flicks cross the screen.
CURSOR_MIN_SPEED = 1.2      # screens per frame moved, for slow hand movement
CURSOR_MAX_SPEED = 4.0      # ... for fast hand movement
CURSOR_ACCEL_START = 0.15   # hand speed (frames / s) where acceleration starts
CURSOR_ACCEL_FULL = 1.2     # hand speed where it reaches CURSOR_MAX_SPEED
CURSOR_DEADZONE = 0.02      # hand speed below which the cursor holds still
                            # (movement fades in over 1-2x this speed)
CURSOR_SMOOTH_MIN_CUTOFF = 0.8  # lower = steadier when still, more lag
CURSOR_SMOOTH_BETA = 0.03       # higher = less lag when moving fast
PRECISION_ZONE = 0.5        # hand sizes: as thumb nears index tip, slow the cursor
PRECISION_FACTOR = 0.35     # ...to this fraction, so clicks land where you aim
CLICK_FREEZE_S = 0.15       # cursor holds still right after a click starts

# --- Clicks (pinches) -------------------------------------------------------------
PINCH_ON = 0.25             # hand sizes between fingertips to count as a pinch
PINCH_OFF = 0.40            # must open past this to release (prevents flicker)
PINCH_FRAMES = 2            # consecutive pinch frames before clicking
PINCH_MIN_REACH = 0.75      # pinching finger's tip-to-wrist / PIP-to-wrist; below
                            # this it is curled into a fist, not pinching

# --- Scrolling (two fingers up, move hand up / down) ---------------------------
SCROLL_GAIN = 5000          # wheel units per frame-height of hand movement (120 = 1 notch)
SCROLL_DEADZONE = 0.003     # ignore tiny hand jitter
SCROLL_NATURAL = True       # True: page follows your hand, like a touchpad / phone

# --- Media -------------------------------------------------------------------------
PLAYPAUSE_HOLD_S = 0.5      # open palm held still this long = play / pause
VOLUME_HOLD_S = 0.25        # thumbs up / down must be held this long first
VOLUME_REPEAT_S = 0.2       # then one volume step per this interval
GESTURE_COOLDOWN_S = 0.8

# --- Swipes ---------------------------------------------------------------------
SWIPE_WINDOW_S = 0.4
SWIPE_THRESHOLD = 0.20      # frame-width fraction the hand must travel
SWIPE_MAX_SLOPE = 0.6       # vertical / horizontal movement allowed
SWIPE_ARM_S = 0.2           # ignore movement right after a hand appears
SWIPE_COOLDOWN_S = 0.7      # applies to both directions
SWIPE_REVERSE_BLOCK_S = 1.2 # ignore the "return stroke" after a swipe
SWIPE_STATIC_BLOCK_S = 0.6  # no palm / thumb actions right after a swipe

# --- UI -----------------------------------------------------------------------
WINDOW_NAME = "AirPad"
ACTION_FLASH_S = 1.0
