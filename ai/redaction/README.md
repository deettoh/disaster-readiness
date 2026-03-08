# Privacy Redaction Pipeline

This module implements an automated privacy redaction pipeline for disaster response imagery.

## Pipeline

Input image -> Face detection -> License plate detection -> Blur sensitive regions -> Save redacted image & Delete Original Image

## Components

Face Detection:

- Model: RetinaFace
- Detects human faces in images

License Plate Detection:

- Model: YOLOv8
- Custom trained on Malaysian license plate dataset

Redaction:

- Gaussian blur applied to detected regions

## Redaction Policy

The system redacts the following sensitive content:

1. Human faces
2. Vehicle license plates

All detected regions are blurred before storage.

## Output

Redacted images are saved in: disaster-readiness/ai/redaction/outputs

## Dataset

The license plate detection model was trained using a Malaysian license plate dataset from Roboflow.

Dataset source:
https://universe.roboflow.com/licenseplatemalaysia/license-plate-malaysia-tjifn

Dataset details:

- Images: 4358
- Classes: 1 (license plate)
- Annotation format: YOLO
- Training / validation split used for model training

The dataset is not included in this repository due to size constraints.

## Model Training

The license plate detector was trained using YOLOv8.

Model: yolov8s  
Image size: 640  
Batch size: 8  
Epochs: 100  
Device: Apple MPS

Best validation performance:

- mAP50: 0.83
- mAP50-95: 0.56
