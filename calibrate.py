import json
import math
import cv2
import config

FRAME_TO_USE = 80      # video ka kaun sa frame dikhana hai
SHOW_WIDTH = 1000      # window ki chaudai (sirf dikhane ke liye)
WINDOW = "Calibrate"

cap = cv2.VideoCapture(config.INPUT_VIDEO)
cap.set(cv2.CAP_PROP_POS_FRAMES, FRAME_TO_USE)
ok, original = cap.read()
cap.release()
if not ok:
    raise SystemExit("Frame nahi padha ja saka. Video path check karein.")

h, w = original.shape[:2]
scale = SHOW_WIDTH / w
points = []            # asli (original) video ke coordinates


def redraw():
    img = cv2.resize(original, (SHOW_WIDTH, int(h * scale)))
    pts = [(int(x * scale), int(y * scale)) for x, y in points]
    for p in pts:
        cv2.circle(img, p, 6, (0, 0, 255), -1)
    if len(pts) == 2:
        cv2.line(img, pts[0], pts[1], (0, 255, 0), 2)

    if len(points) < 2:
        msg = f"Click point {len(points) + 1} of 2"
    else:
        msg = "Done! Ab ENTER dabayein, phir terminal dekhein"
    cv2.putText(img, msg, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (0, 255, 255), 2)
    cv2.putText(img, "r = reset, ESC = exit", (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.imshow(WINDOW, img)


def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
        points.append((int(x / scale), int(y / scale)))
        print(f"Point {len(points)} click hua: {points[-1]}")
        redraw()


cv2.namedWindow(WINDOW)
cv2.setMouseCallback(WINDOW, on_click)
redraw()

while True:
    key = cv2.waitKey(50) & 0xFF
    if key == 27:                       # ESC
        raise SystemExit("Band kiya. Kuch save nahi hua.")
    if key == ord("r"):                 # reset
        points.clear()
        redraw()
    if key == 13 and len(points) == 2:  # ENTER
        break

cv2.destroyAllWindows()
cv2.waitKey(1)

pixels = math.dist(points[0], points[1])
print(f"\nPixel distance: {pixels:.1f}")
meters = float(input("In do points ke beech asli doori meter mein likhein (lane = 3.5): "))
mpp = meters / pixels

# ---------- Auto save ----------
data = {
    "meters_per_pixel": mpp,
    "real_distance_m": meters,
    "pixel_distance": pixels,
    "points": points,
    "frame_used": FRAME_TO_USE,
}
with open(config.CALIBRATION_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"\nMETERS_PER_PIXEL = {mpp:.4f}")
print("Saved ->", config.CALIBRATION_FILE)
print("Ab seedha 'python main.py' chalayein. config.py mein kuch badalna nahi hai.")