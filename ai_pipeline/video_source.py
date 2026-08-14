import cv2

class VideoSource:
    """Unified interface for file path / webcam index / stream URL."""

    def __init__(self, source):
        self.source = self._resolve(source)
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {source}")

    @staticmethod
    def _resolve(source):
        # webcam index passed as int or numeric string -> int
        if isinstance(source, int):
            return source
        if isinstance(source, str) and source.isdigit():
            return int(source)
        return source  # file path or stream URL, str as-is

    def read(self):
        ret, frame = self.cap.read()
        return ret, frame

    def get_fps(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return fps if fps > 0 else None

    def release(self):
        self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()