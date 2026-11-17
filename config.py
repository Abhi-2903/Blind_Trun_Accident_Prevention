import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- Paths ----------
INPUT_VIDEO = "input/road_video.mp4"     # jis video par chalana hai, uska naam
OUTPUT_VIDEO = "output/processed_video.mp4"
CALIBRATION_FILE = os.path.join(BASE_DIR, "calibration.json")
ROI_FILE = os.path.join(BASE_DIR, "roi.json")
HOMOGRAPHY_FILE = os.path.join(BASE_DIR, "homography.json")

# ---------- Display ----------
SHOW_WINDOW = True
WINDOW_NAME = "Blind Turn Safety System"
DISPLAY_WIDTH = 1000
DISPLAY_HEIGHT = 700

# ---------- YOLO ----------
MODEL_PATH = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.4
INFERENCE_SIZE = 640

# COCO class ids: bicycle, car, motorcycle, bus, truck
VEHICLE_CLASSES = [1, 2, 3, 5, 7]

# ---------- Tracking ----------
TRACKER_CONFIG = "bytetrack.yaml"
HISTORY_LENGTH = 30

# ---------- Speed Estimation ----------
METERS_PER_PIXEL = 0.03
SPEED_WINDOW = 6
SPEED_SMOOTHING = 5

# ---------- Direction ----------
ROAD_AXIS = "vertical"        # "vertical" = U-turn video | "horizontal" | "camera" = mod wali video
DIRECTION_WINDOW = 10
MIN_MOVEMENT_PIXELS = 15
DIAGONAL_RATIO = 1.5

# ---------- Blind-Turn ROI ----------
ROI_POLYGON = None            # roi.json se auto-load hoga
ROI_APPROACH_MARGIN = 120
ROI_TREND_WINDOW = 8
ROI_TREND_MIN = 3
ROI_FRONT_FACTOR = 0.8        # gaadi ke aage ka point box ke kinare ke kitna kareeb ho

# ---------- Collision Risk ----------
TTC_DANGER = 2.0              # seconds: isse kam TTC = DANGER
TTC_CAUTION = 5.0             # seconds: isse kam TTC = CAUTION
MIN_CLOSING_SPEED_MPS = 0.5   # isse kam closing speed = "approaching nahi"
MAX_PAIR_DISTANCE_M = 80      # isse door ki jodi ignore
DANGER_CONFIRM_FRAMES = 3     # DANGER itne frame lagatar aaye tabhi dikhao
VEHICLE_SIZE_M = 4.5          # do gaadiyon ki aadhi-aadhi lambai ka jod (centers ki doori se gap nikalne ke liye)

# ---------- Calibration auto-load ----------
if os.path.exists(CALIBRATION_FILE):
    try:
        with open(CALIBRATION_FILE, "r") as f:
            METERS_PER_PIXEL = json.load(f)["meters_per_pixel"]
        print(f"[config] Calibration loaded: METERS_PER_PIXEL = {METERS_PER_PIXEL:.4f}")
    except (ValueError, KeyError):
        print("[config] calibration.json kharab hai, default value use ho rahi hai.")
else:
    print(f"[config] calibration.json nahi mili, default {METERS_PER_PIXEL} use ho raha hai.")

# ---------- ROI auto-load ----------
if os.path.exists(ROI_FILE):
    try:
        with open(ROI_FILE, "r") as f:
            ROI_POLYGON = [tuple(p) for p in json.load(f)["polygon"]]
        print(f"[config] ROI loaded: {len(ROI_POLYGON)} points")
    except (ValueError, KeyError):
        print("[config] roi.json kharab hai, ROI band rahega.")
else:
    print("[config] roi.json nahi mili. Pehle 'python select_roi.py' chalayein.")