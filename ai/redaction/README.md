# Privacy Redaction Pipeline

This module implements an automated privacy redaction pipeline for disaster response imagery.

## Pipeline

Input image → Face detection → License plate detection → Blur sensitive regions → Save redacted image & Delete Original Image

## Folder Structure

```text
ai/redaction/
├── artifacts/              # Output redacted images
├── models/                 # YOLOv8 license plate model weights
├── notebook/               # Notebooks for YOLOv8 and RetinaFace testing
└── src/                    # Core source code (blurring, pipeline, utils)
```

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

Redacted images are saved in: `disaster-readiness/ai/redaction/outputs`

## Data Requirements

To train or evaluate the license plate detection model, the following dataset is required (not included in this repository due to size constraints):

| Dataset | Source | Format | Location |
| :--- | :--- | :--- | :--- |
| **Malaysian License Plates** | [Roboflow — License Plate Malaysia](https://universe.roboflow.com/licenseplatemalaysia/license-plate-malaysia-tjifn) | YOLO annotation | `data/external/` |

### Dataset Details

**License Plate Malaysia**:

- **Images**: 4,358
- **Classes**: 1 (license plate)
- **Annotation format**: YOLO
- Training / validation split used for model training

Face detection uses the pretrained RetinaFace model and does not require a separate training dataset.

## Model Training

The license plate detector was trained using YOLOv8.

- **Model**: yolov8s
- **Image size**: 640
- **Batch size**: 8
- **Epochs**: 100

## Performance

- **mAP50**: 0.83
- **mAP50-95**: 0.56
