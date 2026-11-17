import math
import cv2
import numpy as np
import config

SAFE = "SAFE AREA"
APPROACHING = "APPROACHING"
INSIDE = "INSIDE"
LEAVING = "LEAVING"

# BGR colours
STATE_COLORS = {
    SAFE: (0, 255, 0),
    APPROACHING: (0, 255, 255),
    INSIDE: (0, 0, 255),
    LEAVING: (0, 165, 255),
}


def front_point(track, last_vector):
    """Gaadi ke aage ka point (jis taraf woh ja rahi hai).
    Direction na mile to box ka neeche-beech point use hota hai."""
    x1, y1, x2, y2 = track["bbox"]
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    half_w, half_h = (x2 - x1) / 2, (y2 - y1) / 2

    vector = last_vector
    if vector is None:
        return (int(cx), int(y2))       # direction abhi pata nahi

    dx, dy = vector
    length = math.hypot(dx, dy)
    if length == 0:
        return (int(cx), int(y2))

    ux, uy = dx / length, dy / length   # unit direction
    f = getattr(config, "ROI_FRONT_FACTOR", 0.8)
    return (int(cx + ux * half_w * f), int(cy + uy * half_h * f))


class BlindTurnROI:
    def __init__(self):
        poly = config.ROI_POLYGON
        self.enabled = poly is not None and len(poly) >= 3
        self.polygon = (np.array(poly, dtype=np.int32).reshape(-1, 1, 2)
                        if self.enabled else None)
        self.was_inside = {}      # {id: True/False}
        self.dist_history = {}    # {id: [pichli signed distances]}
        self.last_state = {}      # {id: pichla state}
        self.last_vector = {}     # {id: aakhri known direction vector}

    def classify(self, track):
        """Gaadi ka state batata hai. ROI band ho to None."""
        if not self.enabled:
            return None

        vid = track["id"]

        # Direction vector yaad rakho (ruki gaadi ke liye bhi aakhri direction kaam aaye)
        direction = track.get("direction")
        if direction is not None and direction["vector"] != (0, 0):
            self.last_vector[vid] = direction["vector"]
        point = front_point(track, self.last_vector.get(vid))

        # d > 0: ROI ke andar | d < 0: bahar (doori) | d = 0: kinare par
        d = cv2.pointPolygonTest(self.polygon, (float(point[0]), float(point[1])), True)

        # Trend: pichle kuch frames mein ROI ke kareeb gaya ya door
        hist = self.dist_history.setdefault(vid, [])
        hist.append(d)
        del hist[:-config.ROI_TREND_WINDOW]
        trend = d - hist[0]       # positive = ROI ki taraf, negative = ROI se door

        if d >= 0:
            state = INSIDE
            self.was_inside[vid] = True
        else:
            outside = -d
            if outside <= config.ROI_APPROACH_MARGIN:
                if self.was_inside.get(vid):
                    state = LEAVING
                elif trend < -config.ROI_TREND_MIN:
                    state = SAFE          # paas hai, lekin door ja rahi hai
                else:
                    state = APPROACHING
            else:
                state = SAFE
                self.was_inside[vid] = False

        changed = self.last_state.get(vid) != state
        self.last_state[vid] = state
        return {"state": state, "distance": d, "point": point, "changed": changed}

    def draw(self, frame):
        """ROI ko frame par halke laal fill + moti border se dikhata hai."""
        if not self.enabled:
            return
        overlay = frame.copy()
        cv2.fillPoly(overlay, [self.polygon], (0, 0, 255))
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        cv2.polylines(frame, [self.polygon], True, (0, 0, 255), 3)
        x, y = self.polygon[0][0]
        cv2.putText(frame, "BLIND TURN ZONE", (int(x), max(int(y) - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)