import math
import cv2
import config
from roi import APPROACHING, INSIDE, SAFE as ROI_SAFE

SAFE = "SAFE"
CAUTION = "CAUTION"
DANGER = "DANGER"

RANK = {SAFE: 0, CAUTION: 1, DANGER: 2}
LEVEL_COLORS = {SAFE: (0, 200, 0), CAUTION: (0, 255, 255), DANGER: (0, 0, 255)}


def box_gap_pixels(a, b):
    """Do boxes ke beech ka sabse chhota gap (pixel). Chhoo rahe ho to 0."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    gap_x = max(0, max(ax1, bx1) - min(ax2, bx2))
    gap_y = max(0, max(ay1, by1) - min(ay2, by2))
    return math.hypot(gap_x, gap_y)


def velocity_mps(track, use_world):
    """Gaadi ka velocity vector (m/s). use_world=True ho to road ke meter wale axes mein."""
    speed = track.get("speed_kmh")
    direction = track.get("direction")
    if speed is None:
        return None
    if direction is not None and direction["label"] == "STOPPED":
        return (0.0, 0.0)

    if use_world:
        dx, dy = track["world_velocity"]
    elif direction is not None:
        dx, dy = direction["vector"]
    else:
        return None

    length = math.hypot(dx, dy)
    if length == 0:
        return (0.0, 0.0)
    v = speed / 3.6                 # km/h -> m/s
    return (dx / length * v, dy / length * v)


def roi_state(track):
    roi = track.get("roi")
    return roi["state"] if roi else None


class CollisionDetector:
    def __init__(self):
        self.danger_streak = 0
        self.last_level = SAFE

    # ---------- Ek jodi ka analysis ----------
    def _check_pair(self, a, b):
        # Dono ke paas world data ho tabhi meter wale axes use karo
        use_world = all(t.get("world_pos") and t.get("world_velocity") for t in (a, b))

        va, vb = velocity_mps(a, use_world), velocity_mps(b, use_world)
        if va is None or vb is None:
            return None

        if use_world:
            pa, pb = a["world_pos"], b["world_pos"]
            rx, ry = pb[0] - pa[0], pb[1] - pa[1]
            dist = math.hypot(rx, ry)
            gap_m = max(0.0, dist - config.VEHICLE_SIZE_M)
        else:
            pa, pb = a["center"], b["center"]
            rx, ry = pb[0] - pa[0], pb[1] - pa[1]
            dist = math.hypot(rx, ry)
            gap_m = box_gap_pixels(a["bbox"], b["bbox"]) * config.METERS_PER_PIXEL

        if dist == 0:
            return None
        rux, ruy = rx / dist, ry / dist                 # A se B ki taraf unit direction

        # Closing speed: dono ek-doosre ke kitne kareeb aa rahe hain (m/s)
        rel_vx, rel_vy = vb[0] - va[0], vb[1] - va[1]
        closing = -(rux * rel_vx + ruy * rel_vy)

        approaching = closing > config.MIN_CLOSING_SPEED_MPS
        ttc = gap_m / closing if approaching else None

        if config.ROI_POLYGON is None:
            near_turn = True
        else:
            near_turn = any(s not in (None, ROI_SAFE) for s in (roi_state(a), roi_state(b)))

        level = SAFE
        if approaching and near_turn and gap_m <= config.MAX_PAIR_DISTANCE_M:
            if ttc < config.TTC_DANGER:
                level = DANGER
            elif ttc < config.TTC_CAUTION:
                level = CAUTION

        return {
            "ids": (a["id"], b["id"]),
            "center_a": a["center"], "center_b": b["center"],
            "gap_m": gap_m, "closing_mps": closing,
            "approaching": approaching, "ttc": ttc, "level": level,
        }

    # ---------- Poore frame ka analysis ----------
    def analyze(self, tracks):
        pairs = []
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                p = self._check_pair(tracks[i], tracks[j])
                if p:
                    pairs.append(p)

        raw = SAFE
        worst = None
        for p in pairs:
            if p["level"] == SAFE:
                continue
            if worst is None or RANK[p["level"]] > RANK[worst["level"]] or \
               (p["level"] == worst["level"] and p["ttc"] < worst["ttc"]):
                worst = p
                raw = p["level"]

        if raw == SAFE and any(roi_state(t) in (APPROACHING, INSIDE) for t in tracks):
            raw = CAUTION

        self.danger_streak = self.danger_streak + 1 if raw == DANGER else 0
        level = raw
        if raw == DANGER and self.danger_streak < config.DANGER_CONFIRM_FRAMES:
            level = CAUTION

        changed = level != self.last_level
        self.last_level = level
        return {"level": level, "pairs": pairs, "worst": worst, "changed": changed}


def draw_collision(frame, result):
    """Video ke andar SAFE / CAUTION / DANGER status dikhata hai."""

    level = result["level"]

    # Status ke according color
    color = LEVEL_COLORS[level]


    cv2.putText(
    frame,
    f"STATUS: {level}",
    (40, 62),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.0,
    color,
    3
)

    # ---------- RISKY PAIRS ----------
    for p in result["pairs"]:

        if p["level"] == SAFE:
            continue

        color = LEVEL_COLORS[p["level"]]

        # Vehicles ke beech line
        cv2.line(
            frame,
            p["center_a"],
            p["center_b"],
            color,
            3
        )

        # Line ke center mein TTC
        mid = (
            (
                p["center_a"][0] +
                p["center_b"][0]
            ) // 2,
            (
                p["center_a"][1] +
                p["center_b"][1]
            ) // 2
        )

        cv2.putText(
            frame,
            f'TTC {p["ttc"]:.1f}s',
            mid,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )