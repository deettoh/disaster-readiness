"""Core high level API workflow tests."""


def test_report_upload_and_completion_flow(
    client,
    report_id_str,
    valid_image_upload,
) -> None:
    """Uploading an image should enqueue processing and allow status updates."""
    upload_response = client.post(
        f"/api/v1/reports/{report_id_str}/image",
        files={"image": valid_image_upload},
    )
    assert upload_response.status_code == 202

    status_response = client.get(f"/api/v1/reports/{report_id_str}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "processing"

    complete_response = client.post(
        f"/api/v1/reports/{report_id_str}/processing-result",
        json={"status": "complete"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "complete"


def test_upload_report_image_rejects_unsupported_content_type(
    client,
    report_id_str,
) -> None:
    """Image upload must reject non-image content types."""
    response = client.post(
        f"/api/v1/reports/{report_id_str}/image",
        files={"image": ("notes.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_report_rate_limit(client, custom_settings, report_create_payload) -> None:
    """Report creation must enforce anti spam limits."""
    custom_settings(
        rate_limit_reports_per_minute=1,
        rate_limit_report_images_per_minute=30,
    )
    first_response = client.post("/api/v1/reports", json=report_create_payload)
    second_response = client.post("/api/v1/reports", json=report_create_payload)
    assert first_response.status_code == 201
    assert second_response.status_code == 429
    assert second_response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_get_hazards_sanitizes_non_redacted_urls(
    client,
    override_hazard_service,
    unsafe_hazard_service,
) -> None:
    """Hazard responses should expose only redacted image URLs."""
    override_hazard_service(unsafe_hazard_service)
    response = client.get("/api/v1/hazards")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["redacted_image_url"] is None
    assert payload["items"][1]["redacted_image_url"] is not None
