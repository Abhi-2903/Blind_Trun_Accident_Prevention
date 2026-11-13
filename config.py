import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- Paths ----------
INPUT_VIDEO = "input/road_video.mp4"
OUTPUT_VIDEO = "output/processed_video.mp4"
CALIBRATION_FILE = os.path.join(BASE_DIR, "calibration.json")

# ---------- Display ----------
SHOW_WINDOW = True            # False karne par window nahi khulegi (fast processing)
WINDOW_NAME = "Blind Turn Safety System"
DISPLAY_WIDTH = 1000          # window ki chaudai (sirf dikhane ke liye)

# ---------- YOLO ----------
MODEL_PATH = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.4    # isse kam confidence wali detections ignore
INFERENCE_SIZE = 640          # chhota = fast, bada = zyada accurate

# COCO class ids: bicycle, car, motorcycle, bus, truck
VEHICLE_CLASSES = [1, 2, 3, 5, 7]

# ---------- Tracking ----------
TRACKER_CONFIG = "bytetrack.yaml"
HISTORY_LENGTH = 30           # har vehicle ki pichli kitni positions yaad rakhni hain

# ---------- Speed Estimation ----------
METERS_PER_PIXEL = 0.03       # default; calibration.json mile to woh use hoga
SPEED_WINDOW = 6              # kitne pichle frames ki movement se speed nikalni hai
SPEED_SMOOTHING = 5           # kitni pichli speeds ka average lena hai

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