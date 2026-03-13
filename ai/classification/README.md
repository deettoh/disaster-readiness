# Hazard Classification Model

This module implements an automated hazard classification pipeline that analyzes disaster imagery and identifies the type of hazard present in the scene. The model helps emergency responders quickly understand the situation on the ground and prioritize appropriate response actions.

## Pipeline

Input Image → Image Preprocessing → Hazard Classification Model → Predicted Hazard Category → Output Label

## Folder Structure

```text
ai/classification/
├── models/                 # Trained model weights (hazard_classifier.pt)
├── notebook/               # Jupyter notebooks for EDA and model training
├── scripts/                # CLI scripts for evaluation
└── src/                    # Core source code (dataset, model, inference logic)
```

## Components

### Dataset Preprocessing

Before classification, images undergo preprocessing and augmentation to standardize the input format and improve model generalization.

- **Resize (224 × 224)** to match the model input resolution
- **Random Horizontal Flip (p = 0.5)** to improve robustness to orientation changes
- **Random Rotation (±15°)** to simulate different camera angles
- **Color Jitter** (brightness, contrast, saturation, hue) to increase lighting variation robustness
- **Convert to Tensor**
- **Normalize pixel values** using ImageNet mean and standard deviation

## Hazard Categories

The classifier identifies the following hazard types:

1. Flooded roads
2. Fire
3. Landslide
4. No Hazard/Normal

These categories help emergency planners determine whether a location is accessible, hazardous, or requires intervention.

## Output

Predicted hazard labels are saved to:

`disaster-readiness/ai/classification/outputs`

Each prediction includes:

- Predicted hazard class
- Confidence score

This output can be integrated into the disaster response pipeline to assist **route planning and situation awareness**.

## Data Requirements

To train or evaluate the model, the following datasets are required (not included in this repository due to size constraints):

| Dataset | Source | Format | Location |
| :--- | :--- | :--- | :--- |
| **Disaster Damage Images** | [Kaggle — Disaster Damage 5-Class](https://www.kaggle.com/datasets/sarthaktandulje/disaster-damage-5class) | `.jpg` | `data/external/` |
| **Clean/Dirty Road Images** | [Kaggle — Clean/Dirty Road Classification](https://www.kaggle.com/datasets/faizalkarim/cleandirty-road-classification?select=Images) | `.jpg` | `data/external/` |

### Dataset Details

**Disaster Damage 5-Class** — raw image dataset filtered to match project hazard classes:

| Class | Images |
| :--- | :--- |
| Flood | 600 |
| Fire | 600 |
| Landslide | 310 |

**Clean/Dirty Road Classification** — used for the "normal / no hazard" class (clean roads only): **113 images**.

### Notes and Limitations

- Imbalanced dataset for landslide and normal classes (though no major misclassification observed on the landslide class)
- Dataset filtered from original multi-class sources to match the 4 project hazard categories

## Hazard Classification

The system classifies images into predefined hazard categories using a deep learning model trained on disaster-related imagery.

- **Model Architecture**: EfficientNet-B0
- **Framework**: PyTorch
- **Task**: Multi-class image classification
- **Input Size**: 224 × 224

EfficientNet-B0 pretrained on ImageNet is fine-tuned on the disaster hazard dataset. Transfer learning allows the model to leverage previously learned visual features such as edges, textures, and shapes, improving performance while requiring fewer training samples.

## Model Training

Training configuration:

- **Optimizer**: Adam
- **Loss Function**: Cross Entropy Loss
- **Epochs**: 30
- **Batch Size**: 32
- **Input Size**: 224 × 224

## Model Performance

Best validation performance:

- **Validation Accuracy**: 0.981
- **Validation Loss**: 0.0568

Final test performance:

- **Test Accuracy**: 0.9953
- **Macro F1-score**: 0.9960

### Per-Class Performance

| Class     | Precision | Recall | F1-score |
| --------- | --------- | ------ | -------- |
| Fire      | 1.0000    | 1.0000 | 1.0000   |
| Flood     | 0.9836    | 1.0000 | 0.9917   |
| Landslide | 1.0000    | 1.0000 | 1.0000   |
| Normal    | 1.0000    | 0.9844 | 0.9921   |

## Model Files

The trained model weights are stored in:

`ai/classification/models/`

Example:

`hazard_classifier.pth`

These weights are required for running inference.

## Running the Model

From the project root:

```bash
python ai/classification/inference.py --image path/to/image.jpg
```
