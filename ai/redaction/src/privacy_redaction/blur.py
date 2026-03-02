"""Module for blurring bounding boxes in images for privacy redaction."""

import cv2


def blur_boxes(image, boxes, ksize=51):
    """Applies Gaussian Blur to bounding boxes in the image."""
    for x1, y1, x2, y2 in boxes:
        face = image[y1:y2, x1:x2]
        if face.size == 0:
            continue
        blurred_face = cv2.GaussianBlur(face, (ksize, ksize), 0)
        image[y1:y2, x1:x2] = blurred_face
    return image
