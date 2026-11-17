import math
import config


def estimate_direction(track):
    """Gaadi ki direction batata hai. History kam ho to None."""
    history = track["history"]
    n = config.DIRECTION_WINDOW
    if len(history) < n:
        return None

    _, x_old, y_old = history[-n]
    _, x_new, y_new = history[-1]
    dx = x_new - x_old
    dy = y_new - y_old

    # Bahut kam movement = gaadi ruki hui
    if math.hypot(dx, dy) < config.MIN_MOVEMENT_PIXELS:
        return {"label": "STOPPED", "motion": "STOPPED", "vector": (0, 0)}

    horizontal = "RIGHT" if dx > 0 else "LEFT"
    vertical = "DOWN" if dy > 0 else "UP"

    # Kaun si axis zyada hai?
    if abs(dx) > abs(dy) * config.DIAGONAL_RATIO:
        label = horizontal
    elif abs(dy) > abs(dx) * config.DIAGONAL_RATIO:
        label = vertical
    else:
        label = f"{vertical}-{horizontal}"

    motion = "TOWARD CAMERA" if dy > 0 else "AWAY FROM CAMERA"

    return {"label": label, "motion": motion, "vector": (dx, dy)}