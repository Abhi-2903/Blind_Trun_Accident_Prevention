from ultralytics import YOLO
import config


class VehicleTracker:
    def __init__(self):
        self.model = YOLO(config.MODEL_PATH)
        self.class_names = self.model.names
        self.history = {}   # {vehicle_id: [(frame_number, cx, cy), ...]}

    def update(self, frame, frame_number):
        """Frame par detect + track karta hai, ID wali vehicles ki list deta hai."""
        results = self.model.track(
            frame,
            persist=True,                      # frames ke beech yaad rakho
            tracker=config.TRACKER_CONFIG,     # ByteTrack
            classes=config.VEHICLE_CLASSES,
            conf=config.CONFIDENCE_THRESHOLD,
            imgsz=config.INFERENCE_SIZE,
            verbose=False,
        )

        tracks = []
        boxes = results[0].boxes
        if boxes.id is None:        # kabhi kabhi kisi frame mein koi track nahi hota
            return tracks

        for box in boxes:
            if box.id is None:
                continue

            vehicle_id = int(box.id[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            class_id = int(box.cls[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # History update
            if vehicle_id not in self.history:
                self.history[vehicle_id] = []
            self.history[vehicle_id].append((frame_number, cx, cy))
            self.history[vehicle_id] = self.history[vehicle_id][-config.HISTORY_LENGTH:]

            tracks.append({
                "id": vehicle_id,
                "bbox": (x1, y1, x2, y2),
                "class_id": class_id,
                "class_name": self.class_names[class_id],
                "confidence": float(box.conf[0]),
                "center": (cx, cy),
                "history": self.history[vehicle_id],
            })
        return tracks