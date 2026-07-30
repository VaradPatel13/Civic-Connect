"""
Tests for media uploads router and Cloudinary upload service.
"""
from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_unsupported_media_type(async_client: AsyncClient) -> None:
    """Test that uploading a non-image file returns HTTP 415."""
    response = await async_client.post(
        "/api/v1/uploads/",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file(async_client: AsyncClient) -> None:
    """Test that uploading an empty file returns HTTP 422."""
    response = await async_client.post(
        "/api/v1/uploads/",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 422
    assert "Empty file uploaded" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_successful_mocked(async_client: AsyncClient) -> None:
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
        response = await async_client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["secure_url"] == "https://res.cloudinary.com/demo/image/upload/sample.jpg"
        assert data["public_id"] == "civicconnect/reports/sample"


@pytest.mark.asyncio
async def test_upload_cloudinary_error_sanitized(async_client: AsyncClient) -> None:
    """Test that Cloudinary exceptions return generic 502 message without leaking internal details."""
    from cloudinary.exceptions import Error as CloudinaryError

    with patch("backend.api.uploads.settings.cloudinary_url", "cloudinary://key:secret@cloud_name"), \
         patch("backend.api.uploads.upload_file", side_effect=CloudinaryError("Sensitive internal API key leaked!")):
        response = await async_client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
        )
        assert response.status_code == 502
        assert response.json()["detail"] == "Cloudinary upload failed."
        assert "Sensitive" not in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_generic_error_sanitized(async_client: AsyncClient) -> None:
    """Test that generic exceptions return generic 500 message without leaking raw stack trace/error details."""
    with patch("backend.api.uploads.settings.cloudinary_url", "cloudinary://key:secret@cloud_name"), \
         patch("backend.api.uploads.upload_file", side_effect=Exception("Database connection postgres://admin:secret_pass@db:5432 failed")):
        response = await async_client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 100, "image/jpeg")},
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "Upload failed."
        assert "secret_pass" not in response.json()["detail"]


