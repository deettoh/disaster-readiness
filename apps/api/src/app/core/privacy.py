"""Privacy guard utilities for outbound API payloads."""


def sanitize_redacted_image_url(url: str | None) -> str | None:
    """Return URL only if it appears to reference a redacted artifact."""
    if not url:
        return None
    normalized = url.lower()
    if "redacted" in normalized:
        return url
    return None
