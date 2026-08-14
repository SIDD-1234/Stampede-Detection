import cv2
import numpy as np

class MotionEstimator:
    def __init__(self):
        self.prev_gray = None

    def compute_flow(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.prev_gray is None:
            self.prev_gray = gray
            return None
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        self.prev_gray = gray
        return flow  # HxWx2 array: dx, dy per pixel

    @staticmethod
    def person_vector(flow, bbox):
        """Average motion vector inside a person's bbox."""
        x1, y1, x2, y2 = map(int, bbox)
        region = flow[y1:y2, x1:x2]
        if region.size == 0:
            return (0.0, 0.0)
        dx = np.mean(region[..., 0])
        dy = np.mean(region[..., 1])
        return (float(dx), float(dy))