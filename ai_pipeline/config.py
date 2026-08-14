from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Detection
    yolo_model: str = "yolov8n.pt"
    confidence_threshold: float = 0.4
    iou_threshold: float = 0.5

    # Tracking
    max_age: int = 30              # DeepSORT: frames to keep lost tracks
    n_init: int = 3                # frames before a track is confirmed

    # Zone grid (for density/heatmap)
    zone_grid_rows: int = 4
    zone_grid_cols: int = 4

    # Risk scoring thresholds
    density_threshold: float = 0.7
    entropy_threshold: float = 0.6
    stagnation_threshold: float = 0.5
    risk_score_stable_max: int = 40
    risk_score_rising_max: int = 70   # above this = IMMINENT

    # Pipeline
    target_fps: int = 15
    frame_resize_width: int = 640

    # Alerts
    alert_cooldown_seconds: int = 60

    class Config:
        env_file = ".env"
        env_prefix = "STAMPEDE_"

settings = Settings()