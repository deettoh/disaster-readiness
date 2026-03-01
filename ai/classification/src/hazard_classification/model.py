"""This module defines the model architecture and loading mechanism for the hazard classification task. It uses EfficientNet-B0 as the base model and modifies the classifier to fit the number of classes in our dataset. The module also provides a function to load a trained model from disk, ready for inference."""

import torch
import torch.nn as nn
from torchvision import models

CLASS_LABELS = ["fire", "flood", "landslide", "normal"]


def build_model(num_classes: int):
    """Builds and returns the EfficientNet-B0 model with a modified classifier for the specified number of classes."""
    model = models.efficientnet_b0(pretrained=False)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def load_trained_model(model_path: str, device: torch.device):
    """Loads the trained model from the specified path and returns it ready for inference."""
    model = build_model(num_classes=len(CLASS_LABELS))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model
