"""
Cloudinary asset upload service.

Handles secure, signed direct-to-Cloudinary uploads.
The mobile client requests a signed upload URL, then uploads the file
directly to Cloudinary — binary never passes through our API server.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    url:          str
    secure_url:   str
    public_id:    str
    format:       str
    width:        int | None
    height:       int | None
    bytes:        int


_CONFIGURED: bool = False


def _configure() -> None:
    """Lazily configure Cloudinary from settings."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    if not settings.cloudinary_url:
        raise RuntimeError(
            "Cloudinary is not configured. Set CLOUDINARY_URL in your .env file.\n"
            "Format: cloudinary://<api_key>:<api_secret>@<cloud_name>"
        )

    parsed = urlparse(settings.cloudinary_url)
    if parsed.scheme == "cloudinary" and parsed.username and parsed.password and parsed.hostname:
        cloudinary.config(
            cloud_name=parsed.hostname,
            api_key=parsed.username,
            api_secret=parsed.password,
            secure=True,
        )
    else:
        cloudinary.config(cloudinary_url=settings.cloudinary_url)
    _CONFIGURED = True


def upload_file(file_content: bytes, filename: str, folder: str = "civicconnect/reports") -> UploadResult:
    """
    Upload a file buffer to Cloudinary under the given folder.

    Args:
        file_content: Raw bytes of the file.
        filename:     Original filename (used to derive the public_id).
        folder:       Cloudinary folder path.

    Returns:
        UploadResult with CDN and metadata.

    Raises:
        RuntimeError: If Cloudinary is not configured.
        cloudinary.api.Error: On upload failure.
    """
    _configure()

    result: dict[str, Any] = cloudinary.uploader.upload(
        file_content,
        folder=folder,
        use_filename=True,
        unique_filename=True,
        overwrite=False,
        resource_type="image",
        quality="auto:good",
        fetch_format="auto",
    )

    return UploadResult(
        url        = result.get("url", ""),
        secure_url = result.get("secure_url", ""),
        public_id  = result.get("public_id", ""),
        format     = result.get("format", ""),
        width      = result.get("width"),
        height     = result.get("height"),
        bytes      = result.get("bytes", 0),
    )


def upload_from_bytesio(stream: io.BytesIO, filename: str, folder: str = "civicconnect/reports") -> UploadResult:
    """Upload from an in-memory BytesIO stream."""
    data = stream.getvalue()
    return upload_file(data, filename, folder)


def delete_asset(public_id: str) -> None:
    """Delete a cloudinary asset by public_id."""
    _configure()
    try:
        cloudinary.uploader.destroy(public_id, resource_type="image")
    except CloudinaryError as e:
        logger.warning("Failed to delete Cloudinary asset %s: %s", public_id, e)
