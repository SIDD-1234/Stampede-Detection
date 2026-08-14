import cv2
from video_source import VideoSource
from tracker import PersonTracker
from config import settings

def run(source):
    tracker = PersonTracker()
    with VideoSource(source) as vs:
        while True:
            ret, frame = vs.read()
            if not ret:
                break

            frame = cv2.resize(frame, (settings.frame_resize_width,
                                        int(frame.shape[0] * settings.frame_resize_width / frame.shape[1])))

            tracks = tracker.update(frame)
            for t in tracks:
                x1, y1, x2, y2 = map(int, t["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'ID {t["track_id"]}', (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            cv2.imshow("Tracking Sanity Check", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run("/Users/siddhanthmungekar/Documents/FINAL YEAR/Project/Crowd-Activity-All.mp4")