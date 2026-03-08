"""Redaction pipeline that detects faces and license plates, then blurs them."""

from .blur import blur_boxes
from .face_detector import FaceDetector
from .plate_detector import PlateDetector


class RedactionPipeline:
    """Pipeline to detect and redact faces and license plates in images."""

    def __init__(self):
        """Initialize the redaction pipeline with face and plate detectors."""
        self.face_detector = FaceDetector()
        self.plate_detector = PlateDetector()

    def redact(self, image):
        """Detect faces and plates, then apply blurring to those regions."""
        face_boxes = self.face_detector.detect(image)
        plate_boxes = self.plate_detector.detect(image)

        all_boxes = face_boxes + plate_boxes

        redacted = blur_boxes(image.copy(), all_boxes)
        del image
        return redacted
