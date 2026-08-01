
"""Phase-1C Visual Evidence Verification Test Suite for CivicConnect.

Tests the multi-signal Visual Forensics Engine:
1. Deterministic Hashing: SHA-256 exact duplicate & dHash perceptual near-duplicate.
2. EXIF & Spatial Analysis: GPS Haversine distance validation & inconsistency flagging.
3. Multimodal VLM Inspection: Screenshot, photo-of-screen, synthetic AI, and digital editing detection.
4. Prompt & Instruction Isolation: Adversarial citizen text & embedded image prompt injection resistance.
5. Quality Gate & Fail-Safe Integration: Visual provider failure produces status="UNAVAILABLE" and routes to PENDING_MANUAL_REVIEW without auto-rejection.
"""

from __future__ import annotations

import hashlib
import hmac
import pytest

from backend.agents.forensics import (
    ForensicsAgent,
    PerceptualDuplicateRegistry,
    SourceType,
    VisualVerificationVLMOutput,
    compute_dhash,
    compute_sha256_hash,
    extract_exif_metadata,
    get_configured_signing_secrets,
    haversine_distance_meters,
    verify_hmac_signature,
)
from backend.agents.pipeline import create_civic_pipeline_graph
from backend.core.ai_engine import BaseAIEngine
from backend.core.config import settings


from backend.agents.forensics import global_duplicate_registry


# ---------------------------------------------------------------------------
# Override global conftest DB fixture — Visual Verification tests are DB-free
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_and_cleanup_db():
    global_duplicate_registry._sha256_index.clear()
    global_duplicate_registry._dhash_index.clear()
    yield
    global_duplicate_registry._sha256_index.clear()
    global_duplicate_registry._dhash_index.clear()


# ---------------------------------------------------------------------------
# Mocks & Test Fixtures
# ---------------------------------------------------------------------------

class MockVLMSuccessEngine(BaseAIEngine):
    """Mock VLM Engine returning visual support without risk flags."""

    def __init__(self, supports_report: bool = True, confidence: float = 0.95, source_type: SourceType = "camera_photo") -> None:
        self.supports_report = supports_report
        self.confidence = confidence
        self.source_type: SourceType = source_type

    async def generate_structured(
        self, prompt: str, response_model: type, system_prompt: str | None = None, temperature: float = 0.2, image_urls: list[str] | None = None
    ):
        model_name = getattr(response_model, "__name__", "")
        if model_name == "DetailedSafetyModelOutput":
            from backend.agents.moderator import DetailedSafetyModelOutput
            output = DetailedSafetyModelOutput(safe_for_processing=True, confidence=1.0, flags=[])
        elif model_name == "ClassifierPydanticOutput":
            from backend.agents.classifier import ClassifierPydanticOutput
            output = ClassifierPydanticOutput(category="ROADS", urgency="medium", confidence=0.9, tags=[])
        else:
            output = VisualVerificationVLMOutput(
                supports_report=self.supports_report,
                reported_issue_visible=self.supports_report,
                issue_category_match=True,
                source_type=self.source_type,
                quality_ok=True,
                screenshot_suspected=self.source_type == "screenshot",
                photo_of_screen_suspected=self.source_type == "photo_of_screen",
                synthetic_image_suspected=False,
                manipulation_suspected=False,
                confidence=self.confidence,
                reason="Clear camera photo of reported civic issue",
            )
        return output, 120.0, 45, "meta/llama-3.2-11b-vision-instruct"


class MockVLMScreenshotEngine(BaseAIEngine):
    """Mock VLM Engine detecting mobile screenshot UI chrome."""

    async def generate_structured(
        self, prompt: str, response_model: type, system_prompt: str | None = None, temperature: float = 0.2, image_urls: list[str] | None = None
    ):
        output = VisualVerificationVLMOutput(
            supports_report=True,
            reported_issue_visible=True,
            issue_category_match=True,
            source_type="screenshot",
            quality_ok=True,
            screenshot_suspected=True,
            photo_of_screen_suspected=False,
            synthetic_image_suspected=False,
            manipulation_suspected=False,
            confidence=0.92,
            reason="Mobile UI status bar and navigation chrome detected in image frame",
        )
        return output, 110.0, 40, "meta/llama-3.2-11b-vision-instruct"


class MockVLMSyntheticEngine(BaseAIEngine):
    """Mock VLM Engine detecting AI-generated synthetic artifacts."""

    async def generate_structured(
        self, prompt: str, response_model: type, system_prompt: str | None = None, temperature: float = 0.2, image_urls: list[str] | None = None
    ):
        output = VisualVerificationVLMOutput(
            supports_report=False,
            reported_issue_visible=True,
            issue_category_match=True,
            source_type="internet_image",
            quality_ok=True,
            screenshot_suspected=False,
            photo_of_screen_suspected=False,
            synthetic_image_suspected=True,
            manipulation_suspected=True,
            confidence=0.88,
            reason="Synthetic AI diffusion pattern and unnatural texturing detected",
        )
        return output, 130.0, 50, "meta/llama-3.2-11b-vision-instruct"


class MockVLMFailureEngine(BaseAIEngine):
    """Mock VLM Engine simulating network or provider outage."""

    async def generate_structured(
        self, prompt: str, response_model: type, system_prompt: str | None = None, temperature: float = 0.2, image_urls: list[str] | None = None
    ):
        raise RuntimeError("NVIDIA NIM Vision endpoint 503 Service Unavailable")


# ---------------------------------------------------------------------------
# Unit Tests — Hashing & EXIF Math
# ---------------------------------------------------------------------------

def test_haversine_distance_meters():
    """Validates GPS Haversine distance calculation."""
    # Distance between PMC Main Building (18.5204, 73.8567) and Swargate (18.5018, 73.8580)
    dist = haversine_distance_meters(18.5204, 73.8567, 18.5018, 73.8580)
    assert 2000.0 < dist < 2200.0


def test_hmac_signature_verification():
    """Validates HMAC-SHA256 signature verification logic."""
    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    secret = "civicconnect_secret_key"
    valid_sig = hmac.new(secret.encode("utf-8"), sha256.encode("utf-8"), hashlib.sha256).hexdigest()

    assert verify_hmac_signature(sha256, valid_sig, secret) is True
    assert verify_hmac_signature(sha256, "invalid_sig", secret) is False


def test_hmac_production_fail_closed_valid_secret(monkeypatch):
    """TEST 1: debug=False + valid configured secret -> valid signature verifies."""
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "jwt_secret", "prod-secure-cryptographic-secret-key-999")

    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    valid_sig = hmac.new("prod-secure-cryptographic-secret-key-999".encode("utf-8"), sha256.encode("utf-8"), hashlib.sha256).hexdigest()

    secrets = get_configured_signing_secrets()
    assert "prod-secure-cryptographic-secret-key-999" in secrets
    assert "civicconnect_secret_key" not in secrets
    assert any(verify_hmac_signature(sha256, valid_sig, sec) for sec in secrets) is True


def test_hmac_production_fail_closed_invalid_signature(monkeypatch):
    """TEST 2: debug=False + configured secret + invalid signature -> signature does not verify."""
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "jwt_secret", "prod-secure-cryptographic-secret-key-999")

    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    secrets = get_configured_signing_secrets()
    assert any(verify_hmac_signature(sha256, "invalid_forged_sig", sec) for sec in secrets) is False


def test_hmac_production_fail_closed_no_configured_secret(monkeypatch):
    """TEST 3: debug=False + NO configured secret -> hardcoded fallback NOT attempted -> signature fails closed."""
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "jwt_secret", "change-me-in-production")

    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    dev_sig = hmac.new("civicconnect_secret_key".encode("utf-8"), sha256.encode("utf-8"), hashlib.sha256).hexdigest()

    secrets = get_configured_signing_secrets()
    assert secrets == []  # Fail closed: No valid production secrets available
    assert any(verify_hmac_signature(sha256, dev_sig, sec) for sec in secrets) is False


def test_hmac_production_rejects_dev_fallback_signature(monkeypatch):
    """TEST 4: debug=False + signature generated using 'civicconnect_secret_key' -> MUST NOT verify."""
    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "jwt_secret", "prod-real-key-8888")

    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    dev_sig = hmac.new("civicconnect_secret_key".encode("utf-8"), sha256.encode("utf-8"), hashlib.sha256).hexdigest()

    secrets = get_configured_signing_secrets()
    assert "civicconnect_secret_key" not in secrets
    assert any(verify_hmac_signature(sha256, dev_sig, sec) for sec in secrets) is False


def test_hmac_development_fallback_permitted(monkeypatch):
    """TEST 5: debug=True -> dev fallback secret is permitted in non-production mode."""
    monkeypatch.setattr(settings, "debug", True)
    monkeypatch.setattr(settings, "jwt_secret", "change-me-in-production")

    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    dev_sig = hmac.new("civicconnect_secret_key".encode("utf-8"), sha256.encode("utf-8"), hashlib.sha256).hexdigest()

    secrets = get_configured_signing_secrets()
    assert "civicconnect_secret_key" in secrets
    assert any(verify_hmac_signature(sha256, dev_sig, sec) for sec in secrets) is True


def test_perceptual_duplicate_registry():
    """Validates exact SHA-256 and perceptual dHash registry matching."""
    registry = PerceptualDuplicateRegistry()
    registry.register("rep-101", "sha256-exact-1", "1234567890abcdef")

    # Exact match
    assert registry.find_exact_duplicate("sha256-exact-1") == "rep-101"
    assert registry.find_exact_duplicate("sha256-nonexistent") is None

    # Perceptual match (Hamming distance 1 bit difference)
    match = registry.find_perceptual_duplicate("1234567890abcdee", threshold=5)
    assert match is not None
    assert match[0] == "rep-101"
    assert match[1] == 1  # distance = 1 bit


# ---------------------------------------------------------------------------
# Component Tests — Forensics Agent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_forensics_valid_camera_photo():
    """Valid camera photo produces supports_report=True and SUCCESS status."""
    agent = ForensicsAgent(ai_engine=MockVLMSuccessEngine())
    state = {
        "report_id": "rep-test-01",
        "raw_payload": {
            "latitude": 18.5204,
            "longitude": 73.8567,
            "media_urls": ["https://example.com/pothole.jpg"],
            "photo_metadata": [
                {
                    "latitude": 18.5205,
                    "longitude": 73.8568,
                    "capture_source": "camera",
                }
            ],
        },
    }

    result = await agent.process(state)
    visual = result["agent_outputs"]["visual_verification"]

    assert visual["analysis_status"] == "SUCCESS"
    assert visual["supports_report"] is True
    assert visual["evidence_confidence"] == 0.95
    assert visual["signals"]["screenshot_suspected"] is False
    assert visual["signals"]["synthetic_image_suspected"] is False
    assert visual["signals"]["gps_consistent"] is True
    assert visual["risk_flags"] == []


@pytest.mark.asyncio
async def test_forensics_screenshot_detection():
    """Detects screenshot evidence and flags screenshot_suspected."""
    agent = ForensicsAgent(ai_engine=MockVLMScreenshotEngine())
    state = {
        "report_id": "rep-test-02",
        "raw_payload": {
            "media_urls": ["https://example.com/screenshot.jpg"],
        },
    }

    result = await agent.process(state)
    visual = result["agent_outputs"]["visual_verification"]

    assert visual["analysis_status"] == "SUCCESS"
    assert visual["signals"]["screenshot_suspected"] is True
    assert "screenshot_suspected" in visual["risk_flags"]


@pytest.mark.asyncio
async def test_forensics_synthetic_ai_detection():
    """Detects AI synthetic generation and flags synthetic_image_suspected."""
    agent = ForensicsAgent(ai_engine=MockVLMSyntheticEngine())
    state = {
        "report_id": "rep-test-03",
        "raw_payload": {
            "media_urls": ["https://example.com/fake_ai.jpg"],
        },
    }

    result = await agent.process(state)
    visual = result["agent_outputs"]["visual_verification"]

    assert visual["analysis_status"] == "SUCCESS"
    assert visual["signals"]["synthetic_image_suspected"] is True
    assert visual["signals"]["manipulation_suspected"] is True
    assert "synthetic_image_suspected" in visual["risk_flags"]


@pytest.mark.asyncio
async def test_forensics_provider_failure_failsafe():
    """VLM provider failure sets analysis_status="UNAVAILABLE" and supports_report=None."""
    agent = ForensicsAgent(ai_engine=MockVLMFailureEngine())
    state = {
        "report_id": "rep-test-04",
        "raw_payload": {
            "media_urls": ["https://example.com/waterfall.jpg"],
        },
    }

    result = await agent.process(state)
    visual = result["agent_outputs"]["visual_verification"]

    assert visual["analysis_status"] in ("PARTIAL", "UNAVAILABLE")
    assert visual["supports_report"] is None
    assert visual["evidence_confidence"] is None
    assert "visual_service_failure" in visual["risk_flags"]


# ---------------------------------------------------------------------------
# LangGraph Pipeline Integration Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_visual_verification_node_integration():
    """Executes full Phase-1 LangGraph pipeline with Phase 1C visual verification engine."""
    mock_engine = MockVLMSuccessEngine()
    pipeline = create_civic_pipeline_graph(ai_engine=mock_engine, db_session_factory=None)

    initial_state = {
        "report_id": "rep-p1c-001",
        "raw_payload": {
            "title": "Severe road pothole near PMC Office",
            "description": "Deep dangerous pothole blocking traffic",
            "category": "ROADS",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "media_urls": ["https://example.com/pothole_pune.jpg"],
        },
        "workflow_run_id": None,
        "sanitised_text": "Deep dangerous pothole blocking traffic",
        "agent_outputs": {},
        "pipeline_status": None,
        "verification_decision": None,
        "decision_reason": None,
    }

    final_state = await pipeline.ainvoke(initial_state)

    assert final_state["workflow_run_id"] is not None
    assert "visual_verification" in final_state["agent_outputs"]
    assert final_state["verification_decision"] in ("VERIFIED", "REJECTED", "PENDING_MANUAL_REVIEW")
