"""Face detection module using RetinaFace."""

from retinaface import RetinaFace


class FaceDetector:
    """Detect faces in images using RetinaFace."""

    def __init__(self, confidence_threshold: float = 0.6):
        """Initialize the face detector with a confidence threshold."""
        self.conf_threshold = confidence_threshold

    def detect(self, image):
        """Detect faces and return bounding boxes in pixel coordinates."""
        detections = RetinaFace.detect_faces(image)

        boxes = []

        if isinstance(detections, dict):
            for _, face_data in detections.items():
                score = face_data["score"]
                if score < self.conf_threshold:
                    continue

                x1, y1, x2, y2 = face_data["facial_area"]
                w = x2 - x1
                h = y2 - y1

                boxes.append((x1, y1, w, h))

        return boxes
