from ultralytics import YOLO
from config import settings

class PersonTracker:
    PERSON_CLASS_ID = 0

    def __init__(self):
        self.model = YOLO(settings.yolo_model)
        self.model.to("mps")

    def update(self, frame):
        results = self.model.track(
            frame,
            classes=[self.PERSON_CLASS_ID],
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            device="mps",
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )
        tracks = []
        if results[0].boxes.id is not None:
            for box, track_id in zip(results[0].boxes.xyxy, results[0].boxes.id):
                x1, y1, x2, y2 = box.tolist()
                tracks.append({"track_id": int(track_id), "bbox": (x1, y1, x2, y2)})
        return tracks