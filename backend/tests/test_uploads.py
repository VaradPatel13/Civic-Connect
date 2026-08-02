from unittest.mock import patch
import uuid

import pytest
from httpx import AsyncClient

from backend.api.deps import get_current_user
from backend.main import app
from backend.models.citizens import Citizen

from backend.services.upload_service import UploadResult

import pytest_asyncio

# Mock authenticated citizen for fast unit testing without DB dependency locks
MOCK_CITIZEN_ID = uuid.uuid4()
mock_user = Citizen(id=MOCK_CITIZEN_ID, phone="9999999999", display_name="Test User", role="citizen")

@pytest_asyncio.fixture(autouse=True)
async def setup_and_cleanup_db():
    """Override DB autouse fixture to prevent DB connections for upload unit tests."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


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


@pytest.mark.asyncio
async def test_capture_challenge_creation(async_client: AsyncClient) -> None:
    """Test that POST /api/v1/uploads/challenge issues a short-lived signed challenge."""
    response = await async_client.post("/api/v1/uploads/challenge")
    assert response.status_code == 201
    data = response.json()
    assert "challenge_id" in data
    assert data["challenge_id"].startswith("chl_")
    assert "nonce" in data
    assert "signed_token" in data
    assert len(data["signed_token"]) == 64


@pytest.mark.asyncio
async def test_upload_with_valid_capture_challenge(async_client: AsyncClient) -> None:
    """Test uploading with valid challenge produces server-sealed HMAC signature and camera source."""
    from backend.services.upload_service import UploadResult

    # 1. Issue capture challenge
    ch_resp = await async_client.post("/api/v1/uploads/challenge")
    assert ch_resp.status_code == 201
    ch_data = ch_resp.json()

    mock_result = UploadResult(
        url="http://res.cloudinary.com/demo/image/upload/sample.jpg",
        secure_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
        public_id="civicconnect/reports/sample",
        format="jpg",
        width=800,
        height=600,
        bytes=1024,
    )

    img_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100

    with patch("backend.api.uploads.settings.cloudinary_url", "cloudinary://key:secret@cloud_name"), \
         patch("backend.api.uploads.upload_file", return_value=mock_result):
        response = await async_client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", img_content, "image/jpeg")},
            data={
                "challenge_id": ch_data["challenge_id"],
                "signed_token": ch_data["signed_token"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["capture_source"] == "camera"
        assert data["challenge_id"] == ch_data["challenge_id"]
        assert data["sha256_hash"] is not None
        assert data["hmac_signature"] is not None


@pytest.mark.asyncio
async def test_upload_with_invalid_or_expired_challenge(async_client: AsyncClient) -> None:
    """Test uploading with invalid challenge falls back to gallery capture_source and unsigned HMAC."""
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

    img_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100

    with patch("backend.api.uploads.settings.cloudinary_url", "cloudinary://key:secret@cloud_name"), \
         patch("backend.api.uploads.upload_file", return_value=mock_result):
        response = await async_client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", img_content, "image/jpeg")},
            data={
                "challenge_id": "chl_invalid_12345",
                "signed_token": "fake_signed_token",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["capture_source"] == "gallery"
        assert data["hmac_signature"] is None


@pytest.mark.asyncio
async def test_forensics_verifies_server_sealed_hmac(async_client: AsyncClient) -> None:
    """Verify that ForensicsAgent validates the server-sealed HMAC signature."""
    from backend.agents.forensics import ForensicsAgent

    # 1. Issue capture challenge
    ch_resp = await async_client.post("/api/v1/uploads/challenge")
    ch_data = ch_resp.json()

    mock_result = UploadResult(
        url="http://res.cloudinary.com/demo/image/upload/sample.jpg",
        secure_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
        public_id="civicconnect/reports/sample",
        format="jpg",
        width=800,
        height=600,
        bytes=1024,
    )

    img_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100

    with patch("backend.api.uploads.settings.cloudinary_url", "cloudinary://key:secret@cloud_name"), \
         patch("backend.api.uploads.upload_file", return_value=mock_result):
        upload_resp = await async_client.post(
            "/api/v1/uploads/",
            files={"file": ("test.jpg", img_content, "image/jpeg")},
            data={"challenge_id": ch_data["challenge_id"], "signed_token": ch_data["signed_token"]},
        )
        upload_data = upload_resp.json()

    # 2. Run ForensicsAgent with photo_metadata containing server sealed signature
    agent = ForensicsAgent()
    with patch.object(agent, "_fetch_image_bytes", return_value=img_content):
        state = {
            "raw_payload": {
                "media_urls": [upload_data["secure_url"]],
                "photo_metadata": [
                    {
                        "url": upload_data["secure_url"],
                        "capture_source": upload_data["capture_source"],
                        "sha256_hash": upload_data["sha256_hash"],
                        "hmac_signature": upload_data["hmac_signature"],
                    }
                ],
                "latitude": 18.5204,
                "longitude": 73.8567,
            }
        }

        with patch.object(agent.ai_engine, "generate_structured") as mock_vlm:
            mock_vlm.return_value = type("VLMRes", (), {
                "supports_report": True,
                "reported_issue_visible": True,
                "issue_category_match": True,
                "source_type": "camera_photo",
                "screenshot_suspected": False,
                "photo_of_screen_suspected": False,
                "synthetic_image_suspected": False,
                "manipulation_suspected": False,
                "confidence": 0.95,
                "reason": "Authentic pothole photo",
            })()
            result = await agent.process(state)

    forensics_out = result["agent_outputs"]["forensics"]
    assert forensics_out["signature_valid"] is True
    assert forensics_out["capture_source"] == "camera"




