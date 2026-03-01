"""Hazard classification inference module.

This module provides functionality to predict hazard types from images
using a trained deep learning model.
"""

from pathlib import Path

import torch
import torch.nn.functional as F

from .model import CLASS_LABELS, load_trained_model
from .utils import get_inference_transform, load_image

DEVICE = torch.device(
    "mps"
    if torch.backends.mps.is_available()
    else "cuda"
    if torch.cuda.is_available()
    else "cpu"
)
BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "best_model.pth"


def predict_hazard(image_bytes: bytes) -> tuple[str, float]:
    """Predicts the hazard type and confidence from image bytes."""
    image = load_image(image_bytes)
    transform = get_inference_transform()
    tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = load_trained_model(MODEL_PATH, DEVICE)(tensor)
        probs = F.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probs, 1)

    hazard_label = CLASS_LABELS[predicted.item()]
    confidence = float(confidence.item())

    return hazard_label, confidence
