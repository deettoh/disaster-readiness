"""Model architecture and loading mechanism for the hazard classification task."""

import torch
import torch.nn as nn
from torchvision import models

CLASS_LABELS = ["fire", "flood", "landslide", "normal"]


def build_model(num_classes: int):
    """Builds the EfficientNet-B0 model with a modified classifier for the specified number of classes."""
    model = models.efficientnet_b0(pretrained=False)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def load_trained_model(model_path: str, device: torch.device):
    """Loads the trained model from the specified path for inference."""
    model = build_model(num_classes=len(CLASS_LABELS))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model
