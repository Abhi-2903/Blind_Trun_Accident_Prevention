import os
import time
import math
import cv2
import config

from tracker import VehicleTracker
from speed_estimator import SpeedEstimator
from direction import estimate_direction
from roi import BlindTurnROI, STATE_COLORS, INSIDE
from collision_detector import CollisionDetector, draw_collision
from homography import GroundMapper


def draw_tracks(frame, tracks):
    for t in tracks:
        x1, y1, x2, y2 = t["bbox"]

        speed = t.get("speed_kmh")
        speed_text = f"{speed:.0f} km/h" if speed is not None else "-- km/h"

        direction = t.get("direction")
        roi_info = t.get("roi")

        color = (
            STATE_COLORS.get(roi_info["state"], (0, 255, 0))
            if roi_info
            else (0, 255, 0)
        )

        # Vehicle bounding box
        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        # Vehicle name + ID
        cv2.putText(
            frame,
            f'{t["class_name"]} ID:{t["id"]}',
            (x1, max(y1 - 30, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

        # Speed
        cv2.putText(
            frame,
            speed_text,
            (x1, max(y1 - 8, 35)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        # Direction
        if direction is not None:

            cv2.putText(
                frame,
                f'Dir: {direction["label"]}',
                (x1, y2 + 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 200, 0),
                2
            )

            cv2.putText(
                frame,
                direction["motion"],
                (x1, y2 + 44),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 200, 0),
                1
            )

            dx, dy = direction["vector"]

            length = math.hypot(dx, dy)

            if length > 0:
                cx, cy = t["center"]

                end = (
                    int(cx + dx / length * 60),
                    int(cy + dy / length * 60)
                )

                cv2.arrowedLine(
                    frame,
                    (cx, cy),
                    end,
                    (255, 0, 0),
                    3,
                    tipLength=0.35
                )

        else:
            cv2.putText(
                frame,
                "Dir: ...",
                (x1, y2 + 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 200, 0),
                2
            )

        # ROI information
        if roi_info:

            cv2.putText(
                frame,
                roi_info["state"],
                (x1, y2 + 66),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

            cv2.circle(
                frame,
                roi_info["point"],
                6,
                color,
                -1
            )

        # Draw vehicle movement history
        points = [
            (cx, cy)
            for _, cx, cy in t["history"]
        ]

        for i in range(1, len(points)):
            cv2.line(
                frame,
                points[i - 1],
                points[i],
                (0, 0, 255),
                2
            )


def main():

    # ---------- Video kholna ----------

    cap = cv2.VideoCapture(config.INPUT_VIDEO)

    if not cap.isOpened():
        print(
            "ERROR: Video nahi khul rahi ->",
            config.INPUT_VIDEO
        )
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    ok, first_frame = cap.read()

    if not ok:
        print("ERROR: Pehla frame nahi padha ja saka.")
        return

    height, width = first_frame.shape[:2]

    # Wapas video ke first frame par
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    print(
        f"Video: {width}x{height}, "
        f"{fps:.1f} FPS, "
        f"{total_frames} frames"
    )

    # ---------- Output writer ----------

    os.makedirs("output", exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = cv2.VideoWriter(
        config.OUTPUT_VIDEO,
        fourcc,
        fps,
        (width, height)
    )

    # ---------- Modules ----------

    tracker = VehicleTracker()

    mapper = GroundMapper()

    speed_estimator = SpeedEstimator(
        fps,
        mapper
    )

    roi = BlindTurnROI()

    collision = CollisionDetector()

    if not roi.enabled:
        print(
            "WARNING: ROI set nahi hai. "
            "'python select_roi.py' chalayein."
        )

    print(
        "YOLO + Track + Speed + Direction + "
        "ROI + Collision ready. Processing shuru..."
    )

    frame_number = 0

    start_time = time.time()

    # ---------- Main loop ----------

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame_number += 1

        # 1. Detect + Track

        tracks = tracker.update(
            frame,
            frame_number
        )

        # 2. Speed + Direction + ROI state

        for t in tracks:

            t["speed_kmh"] = speed_estimator.estimate(t)

            t["direction"] = estimate_direction(t)

            t["roi"] = roi.classify(t)

            if t["roi"] and t["roi"]["changed"]:

                print(
                    f'Frame {frame_number}: '
                    f'ID {t["id"]} '
                    f'{t["class_name"]} '
                    f'-> {t["roi"]["state"]}'
                )

        # 3. Collision risk

        risk = collision.analyze(tracks)

        if risk["changed"]:

            w = risk["worst"]

            extra = ""

            if w is not None and w["ttc"] is not None:

                extra = (
                    f'  (ID {w["ids"][0]} '
                    f'vs ID {w["ids"][1]}: '
                    f'gap {w["gap_m"]:.1f} m, '
                    f'closing {w["closing_mps"]:.1f} m/s, '
                    f'TTC {w["ttc"]:.1f} s)'
                )

            print(
                f'Frame {frame_number}: '
                f'STATUS -> {risk["level"]}'
                f'{extra}'
            )

        # 4. Draw

        roi.draw(frame)

        draw_tracks(
            frame,
            tracks
        )

        draw_collision(
            frame,
            risk
        )

        inside_count = sum(
            1
            for t in tracks
            if t["roi"]
            and t["roi"]["state"] == INSIDE
        )

        cv2.putText(
            frame,
            f"Frame {frame_number}/{total_frames}  "
            f"Vehicles: {len(tracks)}  "
            f"In turn: {inside_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 255),
            2
        )

        # 5. Save

        writer.write(frame)

        # 6. Show

        if config.SHOW_WINDOW:

            scale = min(
                config.DISPLAY_WIDTH / width,
                config.DISPLAY_HEIGHT / height
            )

            small = cv2.resize(
                frame,
                (
                    int(width * scale),
                    int(height * scale)
                )
            )

            cv2.imshow(
                config.WINDOW_NAME,
                small
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):

                print("User ne 'q' dabaya.")

                break

        # Progress

        if frame_number % 30 == 0:

            elapsed = time.time() - start_time

            print(
                f"Frame {frame_number}/{total_frames} | "
                f"{frame_number / elapsed:.1f} FPS"
            )

    # ---------- Safai ----------

    cap.release()

    writer.release()

    cv2.destroyAllWindows()

    elapsed = time.time() - start_time

    print(
        f"Done. {frame_number} frames, "
        f"{elapsed:.1f} sec, "
        f"average "
        f"{frame_number / max(elapsed, 0.001):.1f} FPS"
    )

    print(
        "Output saved:",
        config.OUTPUT_VIDEO
    )


if __name__ == "__main__":
    main()