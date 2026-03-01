"""Test script for hazard classification model inference.

This module tests the hazard classification model's predictions on a sample image.
"""

import os

from hazard_classification.inference import predict_hazard

# change this to any test image
TEST_IMAGE = "/Users/amber/Desktop/hackathon/flood.jpg"


def main():
    """Test the hazard classification model predictions on a sample image."""
    if not os.path.exists(TEST_IMAGE):
        print("Test image not found")
        return

    with open(TEST_IMAGE, "rb") as f:
        image_bytes = f.read()

    label, confidence = predict_hazard(image_bytes)

    print("Prediction:")
    print("Hazard label:", label)
    print("Confidence:", round(confidence, 4))


if __name__ == "__main__":
    main()
