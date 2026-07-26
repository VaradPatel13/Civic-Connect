"""
Tests for media uploads router and Cloudinary upload service.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_upload_unsupported_media_type() -> None:
    """Test that uploading a non-image file returns HTTP 415."""
    response = client.post(
        "/api/v1/uploads/",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_empty_file() -> None:
    """Test that uploading an empty file returns HTTP 422."""
    response = client.post(
        "/api/v1/uploads/",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 422
    assert "Empty file uploaded" in response.json()["detail"]


def test_upload_successful_mocked() -> None:
    """Test uploading a valid image file with mocked Cloudinary service."""
    from backend.services.upload_service import UploadResult

    mock_result = UploadResult(
        url="http://res.cloudinary.com/demo/image/upload/sample.jpg",
        secure_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
        public_id="civicconnect/reports/sample",
        format="jpg",
        width=800,
        height=600,
        bytes=1024,
    )

    with patch("backend.api.uploads.settings.cloudinary_url", "cloudinary://key:secret@cloud_name"), \
         patch("backend.api.uploads.upload_file", return_value=mock_result):
        response = client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["secure_url"] == "https://res.cloudinary.com/demo/image/upload/sample.jpg"
        assert data["public_id"] == "civicconnect/reports/sample"
