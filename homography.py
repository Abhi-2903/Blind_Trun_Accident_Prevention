import json
import os
import cv2
import numpy as np
import config


class GroundMapper:
    """Image ke pixel point ko road ki asli position (meter) mein badalta hai."""

    def __init__(self):
        self.enabled = False
        self.H = None
        if os.path.exists(config.HOMOGRAPHY_FILE):
            try:
                with open(config.HOMOGRAPHY_FILE, "r") as f:
                    data = json.load(f)
                src = np.array(data["image_points"], dtype=np.float32)
                dst = np.array(data["world_points"], dtype=np.float32)
                self.H, _ = cv2.findHomography(src, dst)
                self.enabled = self.H is not None
                print("[homography] Loaded. Speed aur gap meter mein (perspective-corrected).")
            except (ValueError, KeyError):
                print("[homography] homography.json kharab hai, METERS_PER_PIXEL use hoga.")
        else:
            print("[homography] homography.json nahi mili, METERS_PER_PIXEL use hoga.")

    def to_world(self, x, y):
        p = np.array([[[x, y]]], dtype=np.float32)
        out = cv2.perspectiveTransform(p, self.H)[0][0]
        return float(out[0]), float(out[1])