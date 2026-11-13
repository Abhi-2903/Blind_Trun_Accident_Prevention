import os
import time
import cv2
import config
from tracker import VehicleTracker
from speed_estimator import SpeedEstimator


def draw_tracks(frame, tracks):
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]
        speed = t.get("speed_kmh")
        speed_text = f"{speed:.0f} km/h" if speed is not None else "-- km/h"

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Class aur ID
        cv2.putText(frame, f'{t["class_name"]} ID:{t["id"]}',
                    (x1, max(y1 - 30, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Speed
        cv2.putText(frame, speed_text,
                    (x1, max(y1 - 8, 35)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Trail (pichli positions)
        points = [(cx, cy) for _, cx, cy in t["history"]]
        for i in range(1, len(points)):
            cv2.line(frame, points[i - 1], points[i], (0, 0, 255), 2)


def main():
    # ---------- Video kholna ----------
    cap = cv2.VideoCapture(config.INPUT_VIDEO)
    if not cap.isOpened():
        print("ERROR: Video nahi khul rahi ->", config.INPUT_VIDEO)
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video: {width}x{height}, {fps:.1f} FPS, {total_frames} frames")

    # ---------- Output writer ----------
    os.makedirs("output", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(config.OUTPUT_VIDEO, fourcc, fps, (width, height))

    # ---------- Modules ----------
    tracker = VehicleTracker()
    speed_estimator = SpeedEstimator(fps)
    print("YOLO + ByteTrack + Speed ready. Processing shuru...")

    frame_number = 0
    start_time = time.time()

    # ---------- Main loop ----------
    while True:
        success, frame = cap.read()
        if not success:
            break
        frame_number += 1

        # 1. Detect + track
        tracks = tracker.update(frame, frame_number)

        # 2. Speed
        for t in tracks:
            t["speed_kmh"] = speed_estimator.estimate(t)

        # 3. Draw
        draw_tracks(frame, tracks)
        cv2.putText(frame, f"Frame {frame_number}/{total_frames}  Vehicles: {len(tracks)}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # 4. Save
        writer.write(frame)

        # 5. Show
        if config.SHOW_WINDOW:
            scale = config.DISPLAY_WIDTH / width
            small = cv2.resize(frame, (config.DISPLAY_WIDTH, int(height * scale)))
            cv2.imshow(config.WINDOW_NAME, small)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("User ne 'q' dabaya.")
                break

        if frame_number % 30 == 0:
            elapsed = time.time() - start_time
            print(f"Frame {frame_number}/{total_frames} | {frame_number / elapsed:.1f} FPS")

    # ---------- Safai ----------
    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    elapsed = time.time() - start_time
    print(f"Done. {frame_number} frames, {elapsed:.1f} sec, "
          f"average {frame_number / max(elapsed, 0.001):.1f} FPS")
    print("Output saved:", config.OUTPUT_VIDEO)


if __name__ == "__main__":
    main()