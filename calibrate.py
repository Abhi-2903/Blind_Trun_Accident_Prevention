import json
import math
import cv2
import numpy as np
import config

FRAME_TO_USE = 80          # video ka kaun sa frame dikhana hai
SHOW_W, SHOW_H = 1000, 700 # window ka maximum size (sirf dikhane ke liye)
WINDOW = "Calibrate"


# ---------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------
def load_frame():
    cap = cv2.VideoCapture(config.INPUT_VIDEO)
    cap.set(cv2.CAP_PROP_POS_FRAMES, FRAME_TO_USE)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit("Frame nahi padha ja saka. Video path check karein: " + str(config.INPUT_VIDEO))
    return frame


def collect_points(original, labels):
    """Window dikhata hai aur len(labels) points click karwata hai.
    Points asli video ke coordinates mein lautata hai. ESC = exit."""
    h, w = original.shape[:2]
    scale = min(SHOW_W / w, SHOW_H / h)
    n = len(labels)
    points = []

    def redraw():
        img = cv2.resize(original, (int(w * scale), int(h * scale)))
        pts = [(int(x * scale), int(y * scale)) for x, y in points]
        if len(pts) >= 2:
            closed = (n == 4 and len(pts) == 4)
            cv2.polylines(img, [np.array(pts, np.int32)], closed, (0, 255, 0), 2)
        for i, p in enumerate(pts):
            cv2.circle(img, p, 6, (0, 0, 255), -1)
            cv2.putText(img, labels[i], (p[0] + 8, p[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if len(points) < n:
            msg = f"Click: {labels[len(points)]}"
        else:
            msg = "Done! Ab ENTER dabayein"
        cv2.putText(img, msg, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(img, "u = undo | r = reset | ESC = exit", (20, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.imshow(WINDOW, img)

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < n:
            points.append((int(x / scale), int(y / scale)))
            print(f"Point {len(points)} click hua: {points[-1]}")
            redraw()

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_click)
    redraw()

    while True:
        key = cv2.waitKey(50) & 0xFF
        if key == 27:                                   # ESC
            cv2.destroyAllWindows()
            raise SystemExit("Band kiya. Kuch save nahi hua.")
        if key == ord("r"):
            points.clear()
            redraw()
        if key == ord("u") and points:
            points.pop()
            redraw()
        if key == 13 and len(points) == n:              # ENTER
            break

    cv2.destroyAllWindows()
    cv2.waitKey(1)
    return points


# ---------------------------------------------------------------
# Mode 1: Simple calibration (2 points -> METERS_PER_PIXEL)
# ---------------------------------------------------------------
def simple_calibration(original):
    print("\n=== Simple calibration (2 points) ===")
    print("Road par jis cheez ki asli lambai pata ho, uske do kinaron par click karein.")
    print("Jaise: ek lane ki chaudai (peeli line se safed line tak) = 3.5 m")

    points = collect_points(original, ["Point 1", "Point 2"])
    pixels = math.dist(points[0], points[1])
    print(f"\nPixel distance: {pixels:.1f}")
    meters = float(input("In do points ke beech asli doori meter mein likhein (lane = 3.5): "))
    mpp = meters / pixels

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


# ---------------------------------------------------------------
# Mode 2: Homography calibration (4 points -> perspective-corrected meters)
# ---------------------------------------------------------------
def homography_calibration(original):
    print("\n=== Homography calibration (4 points) ===")
    print("Road par ek seedha rectangle socho (jaise 3.5 m chaudi x 10 m lambi).")
    print("Uske 4 corners is order mein click karein:")
    print("  1 = paas-left, 2 = paas-right, 3 = door-right, 4 = door-left")

    labels = ["1: paas-left", "2: paas-right", "3: door-right", "4: door-left"]
    points = collect_points(original, labels)

    print("\nRectangle ki asli naap (meter mein):")
    W = float(input("Chaudai W (point 1 se 2 tak, jaise 3.5): "))
    L = float(input("Lambai L (point 1 se 4 tak, jaise 10): "))

    src = np.array(points, dtype=np.float32)
    dst = np.array([[0, 0], [W, 0], [W, L], [0, L]], dtype=np.float32)
    H, _ = cv2.findHomography(src, dst)
    if H is None:
        raise SystemExit("Homography nahi ban saki. Points dobara click karein.")

    with open(config.HOMOGRAPHY_FILE, "w") as f:
        json.dump({"image_points": points,
                   "world_points": dst.tolist(),
                   "width_m": W, "length_m": L,
                   "frame_used": FRAME_TO_USE}, f, indent=2)
    print("Saved ->", config.HOMOGRAPHY_FILE)

    # ----- Check image: road par 1 meter ki grid -----
    Hinv = np.linalg.inv(H)

    def to_img(X, Y):
        p = cv2.perspectiveTransform(np.array([[[X, Y]]], np.float32), Hinv)[0][0]
        return int(np.clip(p[0], -5000, 5000)), int(np.clip(p[1], -5000, 5000))

    check = original.copy()
    for X in np.arange(-W, 2 * W + 0.01, 1.0):
        cv2.line(check, to_img(X, -L), to_img(X, 2 * L), (0, 255, 255), 1)
    for Y in np.arange(-L, 2 * L + 0.01, 1.0):
        cv2.line(check, to_img(-W, Y), to_img(2 * W, Y), (0, 255, 255), 1)
    cv2.polylines(check, [src.astype(np.int32)], True, (0, 0, 255), 3)

    cv2.imwrite("homography_check.jpg", check)
    print("Check image ban gayi: homography_check.jpg")
    print("Peeli grid ka har dabba road par 1 meter ke barabar dikhna chahiye.")


# ---------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------
def main():
    print("Kaunsa calibration karna hai?")
    print("  1 = Simple     (2 points, ek hi METERS_PER_PIXEL, top-down video ke liye)")
    print("  2 = Homography (4 points, perspective wali video ke liye, behtar)")
    print("  3 = Dono")
    choice = input("Number likhein (1/2/3): ").strip()

    if choice not in ("1", "2", "3"):
        raise SystemExit("Galat choice. 1, 2 ya 3 likhein.")

    original = load_frame()

    if choice in ("1", "3"):
        simple_calibration(original)
    if choice in ("2", "3"):
        homography_calibration(original)

    print("\nCalibration poora. Ab 'python main.py' chalayein. config.py mein kuch badalna nahi hai.")


if __name__ == "__main__":
    main()