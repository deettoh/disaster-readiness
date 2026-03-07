"""Plate detection module using YOLOv8."""

from ultralytics import YOLO


class PlateDetector:
    """Detect license plates in images using a YOLOv8 model."""

    def __init__(
        self,
        model_path="/Users/amber/Desktop/hackathon/disaster-readiness/ai/redaction/models/best.pt",
        conf=0.25,
    ):
        """Initialize the plate detector with the specified model and confidence threshold."""
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, image):
        """Detect license plates in the given image and return bounding boxes."""
        results = self.model.predict(source=image, conf=self.conf, verbose=False)[0]

        boxes = []

        if results.boxes is not None:
            for box in results.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = box[:4]
                boxes.append([int(x1), int(y1), int(x2), int(y2)])

        return boxes
