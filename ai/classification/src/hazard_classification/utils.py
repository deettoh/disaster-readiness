"""Utility functions for image loading and trasnforms."""

import io

import torchvision.transforms as transforms
from PIL import Image


def get_inference_transform():
    """Returns the transformation pipeline for inference."""
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def load_image(image_bytes: bytes):
    """Loads an image from bytes and converts it to RGB."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return image
