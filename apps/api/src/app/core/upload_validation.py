"""Upload validation utilities for report image intake."""

from os import SEEK_END, SEEK_SET
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import DomainValidationError

ALLOWED_IMAGE_EXTENSIONS_BY_MIME: dict[str, set[str]] = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
}


def validate_report_image_content_type(
    *,
    content_type: str | None,
    allowed_content_types: list[str],
) -> str:
    """Validate uploaded image content type and return normalized value."""
    normalized_content_type = (content_type or "").lower().strip()
    if normalized_content_type not in {value.lower() for value in allowed_content_types}:
        raise DomainValidationError(
            message="Unsupported file type. Allowed types: image/jpeg, image/png, image/webp",
            field="image.content_type",
            details={"content_type": content_type},
        )
    return normalized_content_type


def validate_report_image_filename(
    *,
    filename: str | None,
    normalized_content_type: str,
) -> str:
    """Validate filename presence and extension for image upload."""
    normalized_filename = (filename or "").strip()
    if not normalized_filename:
        raise DomainValidationError(
            message="Uploaded file must include a filename",
            field="image.filename",
        )

    extension = Path(normalized_filename).suffix.lower()
    allowed_extensions = ALLOWED_IMAGE_EXTENSIONS_BY_MIME.get(
        normalized_content_type, set()
    )
    if extension and extension not in allowed_extensions:
        raise DomainValidationError(
            message="Filename extension does not match the uploaded image type",
            field="image.filename",
            details={
                "filename": normalized_filename,
                "content_type": normalized_content_type,
            },
        )

    return normalized_filename


def get_upload_size_bytes(upload_file: UploadFile) -> int:
    """Return uploaded file size in bytes."""
    stream = upload_file.file
    current_position = stream.tell()
    stream.seek(0, SEEK_END)
    size_bytes = stream.tell()
    stream.seek(current_position, SEEK_SET)
    return int(size_bytes)


def validate_report_image_size(
    *,
    upload_file: UploadFile,
    max_size_bytes: int,
) -> int:
    """Validate image size and return size bytes when valid."""
    size_bytes = get_upload_size_bytes(upload_file)
    if size_bytes > max_size_bytes:
        raise DomainValidationError(
            message="Uploaded file exceeds allowed size limit",
            field="image",
            details={"max_size_bytes": max_size_bytes, "size_bytes": size_bytes},
        )
    return size_bytes
