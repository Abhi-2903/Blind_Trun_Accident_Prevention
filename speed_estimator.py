import math
import config


class SpeedEstimator:
    def __init__(self, fps, mapper=None):
        self.fps = fps
        self.mapper = mapper
        self.recent = {}     # {vehicle_id: [pichli speeds]}
        self.world = {}      # {vehicle_id: [(frame, X, Y)]}  (meter mein)

    def estimate(self, track):
        """Speed km/h mein deta hai. Saath mein track mein world_pos aur
        world_velocity bhi bharta hai (agar homography on ho)."""
        history = track["history"]
        frame_now = history[-1][0]
        n = config.SPEED_WINDOW

        if self.mapper is not None and self.mapper.enabled:
            # Gaadi ke pahiyon wala point (zameen par), box ke neeche-beech
            x1, y1, x2, y2 = track["bbox"]
            X, Y = self.mapper.to_world((x1 + x2) / 2, y2)

            pts = self.world.setdefault(track["id"], [])
            pts.append((frame_now, X, Y))
            del pts[:-config.HISTORY_LENGTH]
            track["world_pos"] = (X, Y)

            if len(pts) < n:
                return None
            f_old, X_old, Y_old = pts[-n]
            seconds = (frame_now - f_old) / self.fps
            if seconds <= 0:
                return None
            dX, dY = X - X_old, Y - Y_old
            meters = math.hypot(dX, dY)
            track["world_velocity"] = (dX / seconds, dY / seconds)
        else:
            # Purana tarika: pixel x METERS_PER_PIXEL
            if len(history) < n:
                return None
            f_old, x_old, y_old = history[-n]
            _, x_new, y_new = history[-1]
            meters = math.hypot(x_new - x_old, y_new - y_old) * config.METERS_PER_PIXEL
            seconds = (frame_now - f_old) / self.fps
            if seconds <= 0:
                return None

        kmh = meters / seconds * 3.6

        speeds = self.recent.setdefault(track["id"], [])
        speeds.append(kmh)
        del speeds[:-config.SPEED_SMOOTHING]
        return sum(speeds) / len(speeds)