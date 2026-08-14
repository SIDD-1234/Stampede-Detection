import numpy as np
from collections import deque
from config import settings

class RiskScorer:
    def __init__(self, ema_alpha=0.3):
        self.ema_alpha = ema_alpha
        self.ema_score = 0.0
        self.position_history = {}  # track_id -> deque of recent positions

    def _density_score(self, tracks, frame_shape):
        """People per grid cell, normalized 0-1."""
        h, w = frame_shape[:2]
        rows, cols = settings.zone_grid_rows, settings.zone_grid_cols
        cell_h, cell_w = h / rows, w / cols
        grid = np.zeros((rows, cols))
        for t in tracks:
            x1, y1, x2, y2 = t["bbox"]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            r, c = min(int(cy // cell_h), rows - 1), min(int(cx // cell_w), cols - 1)
            grid[r][c] += 1
        max_cell = grid.max() if grid.max() > 0 else 1
        return min(max_cell / 10, 1.0)  # tune divisor to your crowd scale

    def _entropy_score(self, motion_vectors):
        """High entropy = chaotic/divergent movement directions."""
        if len(motion_vectors) < 2:
            return 0.0
        angles = [np.arctan2(dy, dx) for dx, dy in motion_vectors if (dx, dy) != (0, 0)]
        if len(angles) < 2:
            return 0.0
        hist, _ = np.histogram(angles, bins=8, range=(-np.pi, np.pi))
        probs = hist / hist.sum() if hist.sum() > 0 else hist
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))
        max_entropy = np.log2(8)
        return entropy / max_entropy

    def _stagnation_score(self, tracks):
        """Ratio of people barely moving (crowd stuck/crushed)."""
        if not tracks:
            return 0.0
        stagnant = 0
        for t in tracks:
            tid = t["track_id"]
            x1, y1, x2, y2 = t["bbox"]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if tid not in self.position_history:
                self.position_history[tid] = deque(maxlen=15)
            self.position_history[tid].append((cx, cy))
            hist = self.position_history[tid]
            if len(hist) >= 15:
                dist = np.hypot(hist[-1][0] - hist[0][0], hist[-1][1] - hist[0][1])
                if dist < 5:  # px threshold, tune per resolution
                    stagnant += 1
        return stagnant / len(tracks)

    def score(self, tracks, motion_vectors, frame_shape):
        density = self._density_score(tracks, frame_shape)
        entropy = self._entropy_score(motion_vectors)
        stagnation = self._stagnation_score(tracks)

        raw = (density * 50) + (entropy * 20) + (stagnation * 30)  # weights, tune later
        raw = min(raw, 100)

        self.ema_score = (self.ema_alpha * raw) + ((1 - self.ema_alpha) * self.ema_score)

        if self.ema_score <= settings.risk_score_stable_max:
            phase = "NORMAL"
        elif self.ema_score <= settings.risk_score_rising_max:
            phase = "RISING"
        else:
            phase = "IMMINENT"

        return {
            "score": round(self.ema_score, 1),
            "phase": phase,
            "density": round(density, 2),
            "entropy": round(entropy, 2),
            "stagnation": round(stagnation, 2),
        }