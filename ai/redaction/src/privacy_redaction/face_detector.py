"""Face detection module using MediaPipe."""

import cv2
import mediapipe as mp

class FaceDetector:
    """Detects faces in an image using MediaPipe."""
    def __init__(self):
        """Initializes the face detection model."""
        self.mp_face = mp.solutions.face_detection
        self.detector = self.mp_face.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )

    def detect_faces(self, image):
            """Returns lists of bounding boxes [(x1, y1, x2, y2),...]"""

            h, w, _ = image.shape
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.detector.process(rgb_image)

            boxes = []
            if results.detections:
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    x1 = int(bbox.xmin * w)
                    y1 = int(bbox.ymin * h)
                    x2 = int((bbox.xmin + bbox.width) * w)
                    y2 = int((bbox.ymin + bbox.height) * h)
                    boxes.append((x1, y1, x2, y2))
            return boxes