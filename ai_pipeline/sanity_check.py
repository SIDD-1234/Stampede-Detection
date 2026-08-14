import cv2
from video_source import VideoSource
from detector import PersonDetector

def run(source):
    detector = PersonDetector()
    with VideoSource(source) as vs:
        while True:
            ret, frame = vs.read()
            if not ret:
                break
            for det in detector.detect(frame):
                x1, y1, x2, y2 = map(int, det["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{det["conf"]:.2f}', (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.imshow("Detection Sanity Check", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run("/Users/siddhanthmungekar/Documents/FINAL YEAR/Project/Crowd-Activity-All.mp4")  # replace with your actual mock video path
