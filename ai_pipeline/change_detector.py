import numpy as np
from collections import deque
from config import settings

class ChangeDetector:
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.history = {
            "density": deque(maxlen=window_size),
            "entropy": deque(maxlen=window_size),
            "stagnation": deque(maxlen=window_size),
        }

    def _zscore(self, metric, value):
        hist = self.history[metric]
        if len(hist) < 10:
            return 0.0
        mean = np.mean(hist)
        std = np.std(hist)
        if std < 1e-6:
            return 0.0
        return (value - mean) / std

    def update(self, density, entropy, stagnation):
        z_threshold = settings.z_threshold

        z_density = self._zscore("density", density)
        z_entropy = self._zscore("entropy", entropy)
        z_stagnation = self._zscore("stagnation", stagnation)

        self.history["density"].append(density)
        self.history["entropy"].append(entropy)
        self.history["stagnation"].append(stagnation)

        density_spike = z_density > z_threshold
        entropy_spike = z_entropy > z_threshold
        stagnation_spike = z_stagnation > z_threshold

        event_type = None
        if density_spike and entropy_spike:
            event_type = "STAMPEDE"
        elif stagnation_spike and (density_spike or entropy_spike):
            event_type = "STAMPEDE"
        elif density_spike or entropy_spike or stagnation_spike:
            event_type = "ANOMALY"

        return {
            "event_type": event_type,
            "z_density": round(z_density, 2),
            "z_entropy": round(z_entropy, 2),
            "z_stagnation": round(z_stagnation, 2),
        }