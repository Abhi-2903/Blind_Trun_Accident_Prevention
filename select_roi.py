import json
import cv2
import numpy as np
import config

FRAME_TO_USE = 80
SHOW_WIDTH = 1000
WINDOW = "Select Blind-Turn ROI"

cap = cv2.VideoCapture(config.INPUT_VIDEO)
cap.set(cv2.CAP_PROP_POS_FRAMES, FRAME_TO_USE)
ok, original = cap.read()
cap.release()
if not ok:
    raise SystemExit("Frame nahi padha ja saka. Video path check karein.")

h, w = original.shape[:2]
scale = SHOW_WIDTH / w
points = []            # asli video ke coordinates


def redraw():
    img = cv2.resize(original, (SHOW_WIDTH, int(h * scale)))
    pts = [(int(x * scale), int(y * scale)) for x, y in points]

    if len(pts) >= 3:       # halka laal fill
        overlay = img.copy()
        cv2.fillPoly(overlay, [np.array(pts, np.int32)], (0, 0, 255))
        cv2.addWeighted(overlay, 0.25, img, 0.75, 0, img)
    if len(pts) >= 2:
        cv2.polylines(img, [np.array(pts, np.int32)], len(pts) >= 3, (0, 0, 255), 2)
    for i, p in enumerate(pts):
        cv2.circle(img, p, 6, (0, 255, 255), -1)
        cv2.putText(img, str(i + 1), (p[0] + 8, p[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    if len(points) < 3:
        msg = f"Points: {len(points)} (kam se kam 3 chahiye)"
    else:
        msg = f"Points: {len(points)}  -> ENTER dabakar save karein"
    cv2.putText(img, msg, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cv2.putText(img, "Click = point add | u = undo | r = reset | ESC = exit",
                (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.imshow(WINDOW, img)


def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((int(x / scale), int(y / scale)))
        print(f"Point {len(points)}: {points[-1]}")
        redraw()


cv2.namedWindow(WINDOW)
cv2.setMouseCallback(WINDOW, on_click)
redraw()

while True:
    key = cv2.waitKey(50) & 0xFF
    if key == 27:                        # ESC
        raise SystemExit("Band kiya. Kuch save nahi hua.")
    if key == ord("r"):
        points.clear()
        redraw()
    if key == ord("u") and points:       # last point hatao
        points.pop()
        redraw()
    if key == 13 and len(points) >= 3:   # ENTER
        break

cv2.destroyAllWindows()
cv2.waitKey(1)

data = {"polygon": points, "frame_used": FRAME_TO_USE}
with open(config.ROI_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"\nROI saved ({len(points)} points) -> {config.ROI_FILE}")
print("Ab seedha 'python main.py' chalayein.")