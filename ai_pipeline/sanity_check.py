import cv2
from video_source import VideoSource
from tracker import PersonTracker
from motion import MotionEstimator
from risk_scorer import RiskScorer
from config import settings

def run(source):
    tracker = PersonTracker()
    motion = MotionEstimator()
    scorer = RiskScorer()

    with VideoSource(source) as vs:
        while True:
            ret, frame = vs.read()
            if not ret:
                break

            frame = cv2.resize(frame, (settings.frame_resize_width,
                                        int(frame.shape[0] * settings.frame_resize_width / frame.shape[1])))

            tracks = tracker.update(frame)
            flow = motion.compute_flow(frame)

            motion_vectors = []
            for t in tracks:
                x1, y1, x2, y2 = map(int, t["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'ID {t["track_id"]}', (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                if flow is not None:
                    motion_vectors.append(motion.person_vector(flow, t["bbox"]))

            if flow is not None:
                result = scorer.score(tracks, motion_vectors, frame.shape)
                color = (0, 255, 0) if result["phase"] == "NORMAL" else \
                        (0, 165, 255) if result["phase"] == "RISING" else (0, 0, 255)
                cv2.putText(frame, f'RISK: {result["score"]} [{result["phase"]}]',
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                cv2.putText(frame, f'People: {len(tracks)}',
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow("Risk Scoring Sanity Check", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run("/Users/siddhanthmungekar/Documents/FINAL YEAR/Project/Crowd-Activity-All.mp4")