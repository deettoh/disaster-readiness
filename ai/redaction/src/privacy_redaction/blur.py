"""Blurring module for privacy redaction."""

import cv2


def blur_boxes(image, boxes):
    """Apply a strong blur to the specified bounding boxes in the image."""
    h_img, w_img = image.shape[:2]

    for x, y, w, h in boxes:
        x = max(0, x)
        y = max(0, y)
        w = min(w, w_img - x)
        h = min(h, h_img - y)

        if w <= 0 or h <= 0:
            continue

        roi = image[y : y + h, x : x + w]

        if roi.size == 0:
            continue

        blurred = cv2.GaussianBlur(roi, (31, 31), 0)

        image[y : y + h, x : x + w] = blurred

    return image
