"""
Tests for Core Application Configuration & Security Validation (S-01).
"""
import pytest
from pydantic import ValidationError

from backend.core.config import Settings


def test_jwt_secret_validation_rejects_default_in_production():
    """Verify that default 'change-me-in-production' secret raises ValidationError when debug=False."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(debug=False, jwt_secret="change-me-in-production")
    assert "JWT secret must be set" in str(exc_info.value)


def test_jwt_secret_validation_allows_default_in_debug_mode():
    """Verify that default secret is permitted when debug=True for local development."""
    s = Settings(debug=True, jwt_secret="change-me-in-production")
    assert s.jwt_secret == "change-me-in-production"
    assert s.debug is True


def test_jwt_secret_validation_allows_custom_secret_in_production():
    """Verify that custom secure secrets are accepted when debug=False."""
    custom_secret = "a-very-secure-random-jwt-secret-key-123456789"
    s = Settings(debug=False, jwt_secret=custom_secret)
    assert s.jwt_secret == custom_secret
    assert s.debug is False
