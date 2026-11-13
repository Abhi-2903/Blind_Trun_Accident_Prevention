import os
import sys

# ---------- Part 1: Python version ----------
print("Python version:", sys.version.split()[0])

# ---------- Part 2: Libraries import check ----------
try:
    import cv2
    import numpy as np
    import ultralytics
except ImportError as e:
    print("ERROR: Library missing ->", e)
    print("Run: pip install ultralytics opencv-python numpy")
    sys.exit(1)

print("OpenCV version:", cv2.__version__)
print("NumPy version:", np.__version__)
print("Ultralytics version:", ultralytics.__version__)

# ---------- Part 3: YOLO load + test ----------
from ultralytics import YOLO

model = YOLO("yolo11n.pt")  # 'n' = nano, sabse chhota aur fast model
print("YOLO model loaded successfully.")

# Model kin cheezon ko pehchanta hai, usme se hamare vehicle classes
vehicle_names = ["bicycle", "car", "motorcycle", "bus", "truck"]
print("\nVehicle classes in this model:")
for class_id, name in model.names.items():
    if name in vehicle_names:
        print(f"  class id {class_id} -> {name}")

# Ek khali (kaali) image par model chalakar dekhte hain ki error to nahi aata
blank_image = np.zeros((640, 640, 3), dtype=np.uint8)
results = model(blank_image, verbose=False)
print("\nTest inference OK. Detections on blank image:", len(results[0].boxes))

# ---------- Part 4: Video check (optional) ----------
video_path = os.path.join("input", "road_video.mp4")

if os.path.exists(video_path):
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"\nVideo OK: {width}x{height}, {fps:.1f} FPS, {total_frames} frames")
        print(f"Duration: about {total_frames / fps:.1f} seconds")
    else:
        print("\nVideo file mili, lekin OpenCV isko khol nahi pa raha.")
    cap.release()
else:
    print("\nVideo not found at input/road_video.mp4 (abhi skip kar sakte hain).")

print("\nSetup check complete.")