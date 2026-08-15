import cv2
from video_source import VideoSource
from tracker import PersonTracker
from motion import MotionEstimator
from risk_scorer import RiskScorer
from config import settings
import sys

class StampedePipeline:
    def __init__(self):
        self.tracker = PersonTracker()
        self.motion = MotionEstimator()
        self.scorer = RiskScorer()

    def process_frame(self, frame):
        frame = cv2.resize(frame, (settings.frame_resize_width,
                                    int(frame.shape[0] * settings.frame_resize_width / frame.shape[1])))

        tracks = self.tracker.update(frame)
        flow = self.motion.compute_flow(frame)

        motion_vectors = []
        if flow is not None:
            for t in tracks:
                motion_vectors.append(self.motion.person_vector(flow, t["bbox"]))

        result = None
        if flow is not None:
            result = self.scorer.score(tracks, motion_vectors, frame.shape)

        return {
            "frame": frame,
            "tracks": tracks,
            "risk": result,
        }

    def run_on_source(self, source, display=True):
        with VideoSource(source) as vs:
            while True:
                ret, frame = vs.read()
                if not ret:
                    break
                output = self.process_frame(frame)
                if display:
                    self._draw(output)
                    cv2.imshow("StampedeShield Pipeline", output["frame"])
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        cv2.destroyAllWindows()

    @staticmethod
    def _draw(output):
        frame = output["frame"]
        for t in output["tracks"]:
            x1, y1, x2, y2 = map(int, t["bbox"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f'ID {t["track_id"]}', (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        if output["risk"]:
            r = output["risk"]
            color = (0, 255, 0) if r["phase"] == "NORMAL" else \
                    (0, 165, 255) if r["phase"] == "RISING" else (0, 0, 255)
            cv2.putText(frame, f'RISK: {r["score"]} [{r["phase"]}]',
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(frame, f'People: {len(output["tracks"])}',
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "/Users/siddhanthmungekar/Documents/FINAL YEAR/Project/backend/uploads/Crowd-Activity-All.mp4"
    pipeline = StampedePipeline()
    pipeline.run_on_source(source)