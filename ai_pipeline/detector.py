from ultralytics import YOLO
from config import settings

class PersonDetector:
    PERSON_CLASS_ID = 0  # COCO class 0 = person

    def __init__(self):
        self.model = YOLO(settings.yolo_model)

    def detect(self, frame):
        results = self.model.predict(
            frame,
            classes=[self.PERSON_CLASS_ID],
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            verbose=False
        )
        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            detections.append({"bbox": (x1, y1, x2, y2), "conf": conf})
        return detections