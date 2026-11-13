import math
import config


class SpeedEstimator:
    def __init__(self, fps):
        self.fps = fps
        self.recent = {}    # {vehicle_id: [pichli speeds]}

    def estimate(self, track):
        """Gaadi ki speed km/h mein deta hai. Data kam ho to None."""
        history = track["history"]
        n = config.SPEED_WINDOW
        if len(history) < n:
            return None

        f_old, x_old, y_old = history[-n]
        f_new, x_new, y_new = history[-1]

        pixels = math.hypot(x_new - x_old, y_new - y_old)
        meters = pixels * config.METERS_PER_PIXEL
        seconds = (f_new - f_old) / self.fps
        if seconds <= 0:
            return None

        kmh = meters / seconds * 3.6

        # Smoothing: pichli kuch speeds ka average, taaki number kampe nahi
        speeds = self.recent.setdefault(track["id"], [])
        speeds.append(kmh)
        del speeds[:-config.SPEED_SMOOTHING]
        return sum(speeds) / len(speeds)