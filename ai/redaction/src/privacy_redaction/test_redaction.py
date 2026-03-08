"""Integration test for face + plate redaction."""

from pathlib import Path

import cv2

from .blur import blur_boxes
from .face_detector import FaceDetector
from .plate_detector import PlateDetector

BASE_DIR = Path(__file__).resolve().parents[2]

image_path = Path("/Users/amber/Desktop/hackathon/redact2.jpg")
output_path = BASE_DIR / "outputs/redacted_output.jpg"

image = cv2.imread(str(image_path))

face_detector = FaceDetector()
plate_detector = PlateDetector()

face_boxes = face_detector.detect_faces(image)
print("Detected face boxes:", face_boxes)

plate_boxes = plate_detector.detect(image)
print("Detected plate boxes:", plate_boxes)

all_boxes = face_boxes + plate_boxes

redacted = blur_boxes(image.copy(), all_boxes)

cv2.imwrite(str(output_path), redacted)
