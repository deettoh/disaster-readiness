"""Plate detection module using YOLOv8."""

from pathlib import Path

from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "best.pt"


class PlateDetector:
    """Detect license plates in images using a YOLOv8 model."""

    def __init__(
        self,
        model_path=None,
        conf=0.25,
    ):
        """Initialize the plate detector with the specified model and confidence threshold."""
        model_path = model_path or MODEL_PATH
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, image):
        """Detect license plates in the given image and return bounding boxes as (x, y, w, h)."""
        results = self.model.predict(source=image, conf=self.conf, verbose=False)[0]

        boxes = []

        if results.boxes is not None:
            for box in results.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = box[:4]
                w = int(x2) - int(x1)
                h = int(y2) - int(y1)
                boxes.append((int(x1), int(y1), w, h))

        return boxes
