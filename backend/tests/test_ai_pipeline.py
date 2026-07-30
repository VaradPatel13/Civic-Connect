"""Comprehensive Test Suite for CivicConnect Multi-Agent AI Engine & LangGraph Pipeline.

Tests:
1. State Reducer merging parallel dictionary outputs
2. Atomic Redis Token Bucket Limiter fallback logic
3. Geo-Validator PostGIS boundary & PMC bounding-box lookups
4. Classifier regex scoring fallbacks, tag extraction, taxonomy validation, and word boundary checks
5. Full LangGraph state graph compilation & end-to-end execution
"""

import pytest
from pydantic import ValidationError

from backend.agents.classifier import (
    ClassificationAgent,
    ClassifierPydanticOutput,
)
from backend.agents.geo_validator import GeoValidationAgent
from backend.agents.pipeline import create_civic_pipeline_graph
from backend.agents.state import merge_agent_outputs
from backend.core.ai_engine import BaseAIEngine
from backend.core.rate_limiter import RedisTokenBucketLimiter


@pytest.fixture(autouse=True)
def setup_and_cleanup_db():
    """Override database setup fixture to allow unit tests to run without DB connection."""
    yield


def test_state_reducer_shallow_merge():
    """Verify state reducer merges parallel agent dictionaries without overwriting."""
    left = {"forensics": {"authentic": True}}
    right = {"classification": {"category": "ROADS"}}
    merged = merge_agent_outputs(left, right)

    assert "forensics" in merged
    assert "classification" in merged
    assert merged["forensics"]["authentic"] is True
    assert merged["classification"]["category"] == "ROADS"


def test_rate_limiter_in_memory_fallback():
    """Verify rate limiter allows requests when tokens are available."""
    limiter = RedisTokenBucketLimiter(redis_client=None)
    allowed, wait_sec = limiter.consume("test_key", max_tokens=10, refill_rate=1.0)

    assert allowed is True
    assert wait_sec == 0.0


@pytest.mark.asyncio
async def test_geo_validator_bounding_box_match():
    """Verify Geo-Validator correctly matches Pune PMC Aundh-Baner ward coordinates."""
    agent = GeoValidationAgent(db_session_factory=None)
    state = {
        "report_id": "test-rep-001",
        "raw_payload": {"latitude": 18.55, "longitude": 73.80},
    }
    output = await agent.process(state)
    geo_res = output["agent_outputs"]["geo_validation"]

    assert geo_res["boundary_matched"] is True
    assert geo_res["ward_name"] == "Aundh-Baner"
    assert geo_res["confidence"] > 0.90



def test_classifier_regex_fallback():
    """Verify Classifier applies regex rule fallback for pothole issues with score counting."""
    agent = ClassificationAgent()
    fallback_res = agent._rule_fallback("Deep pothole on main road causing severe traffic jam")

    assert fallback_res["category"] in ["ROADS", "TRAFF"]
    assert fallback_res["urgency"] == "high"
    assert fallback_res["fallback_used"] is True
    assert "pothole" in fallback_res["tags"] or "road" in fallback_res["tags"]


def test_classifier_scoring_and_keyword_tag_extraction():
    """Verify category match scoring and extracted tags."""
    agent = ClassificationAgent()
    # Water keywords (4): water, pipeline, pipe, leak vs drain keyword (1): drain
    result = agent._rule_fallback("Water pipeline pipe leak spilling near drain")

    assert result["category"] == "WATER"
    assert "water" in result["tags"] or "pipeline" in result["tags"] or "leak" in result["tags"]


def test_classifier_urgency_word_boundaries():
    """Verify word boundary matching prevents false urgency triggers like 'fireplace'."""
    agent = ClassificationAgent()
    res_normal = agent._rule_fallback("The old fireplace in the park shelter has a broken bench.")
    assert res_normal["urgency"] == "medium"

    res_urgent = agent._rule_fallback("Fire broke out near the power transformer explosion!")
    assert res_urgent["urgency"] == "high"


def test_classifier_pydantic_output_validation():
    """Verify taxonomy and urgency validation on ClassifierPydanticOutput schema."""
    valid_output = ClassifierPydanticOutput(
        category="roads",
        urgency="HIGH",
        tags=["pothole", "asphalt"],
        confidence=0.85,
    )
    assert valid_output.category == "ROADS"
    assert valid_output.urgency == "high"

    with pytest.raises(ValidationError):
        ClassifierPydanticOutput(
            category="INVALID_DEPT",
            urgency="high",
            tags=["tag"],
            confidence=0.9,
        )


class MockAIEngine(BaseAIEngine):
    """Fast, deterministic mock engine for AI pipeline unit tests."""
    async def generate_structured(self, prompt, response_model, system_prompt=None, temperature=0.2, image_urls=None):
        sys_str = system_prompt or ""
        if "Forensics" in sys_str:
            data = {
                "authentic": True,
                "supports_report": True,
                "reported_issue_visible": True,
                "issue_category_match": True,
                "source_type": "camera_photo",
                "quality_ok": True,
                "ai_generated": False,
                "manipulated": False,
                "confidence": 0.99,
                "reason": "Mock forensics pass",
                "duplicate_detected": False,
            }
        elif "Classifier" in sys_str:
            data = {"category": "ROADS", "priority": "P2", "urgency": "high", "department_code": "PMC_DEPT_ROADS", "confidence": 0.95, "summary": "Pothole report"}
        elif "Moderat" in sys_str:
            data = {"clean": True, "flags": [], "toxicity_score": 0.0, "confidence": 0.99, "requires_human_review": False}
        elif "Enhancement" in sys_str:
            data = {"enhanced_title": "Pothole Issue", "enhanced_description": prompt, "key_tags": ["pothole", "roads"]}
        elif "Router" in sys_str:
            data = {"department_code": "PMC_DEPT_ROADS", "ward_name": "Aundh-Baner", "estimated_sla_hours": 48, "routing_reason": "Road issue in Aundh"}
        else:
            data = {}

        obj = response_model.model_validate(data)
        return obj, 1.0, 10, "mock-model"


@pytest.mark.asyncio
async def test_full_pipeline_graph_execution():
    """Verify full end-to-end execution of compiled LangGraph workflow."""
    mock_engine = MockAIEngine()
    graph = create_civic_pipeline_graph(ai_engine=mock_engine)

    initial_state = {
        "report_id": "report-12345",
        "trace_id": "trace-67890",
        "raw_payload": {
            "description": "Pothole on main road causing water logging near Baner hill.",
            "latitude": 18.55,
            "longitude": 73.80,
        },
    }

    final_state = await graph.ainvoke(initial_state)

    assert final_state["report_id"] == "report-12345"
    assert final_state["pipeline_status"] == "COMPLETED"

    outputs = final_state["agent_outputs"]
    assert "geo_validation" in outputs
    assert "classification" in outputs
    assert "enhancement" in outputs
    assert "routing" in outputs
    assert "notification" in outputs

    assert outputs["geo_validation"]["boundary_matched"] is True
    assert outputs["routing"]["department_code"] in ["PMC_DEPT_ROADS", "PMC_DEPT_DRAIN", "PMC_DEPT_ADMIN"]


@pytest.mark.asyncio
async def test_forensics_agent_duplicate_detection():
    """Verify ForensicsAgent parses and returns duplicate_detected and matching_report_id (AI-10)."""
    from backend.agents.forensics import ForensicsAgent, ForensicsPydanticOutput


    class MockDuplicateAIEngine(BaseAIEngine):
        async def generate_structured(self, prompt, response_model, system_prompt=None, temperature=0.2, image_urls=None):
            output = ForensicsPydanticOutput(
                authentic=False,
                supports_report=False,
                reported_issue_visible=False,
                issue_category_match=False,
                source_type="internet_image",
                quality_ok=True,
                ai_generated=False,
                manipulated=True,
                confidence=0.98,
                reason="Identical image perceptual hash found in system",
                duplicate_detected=True,
                matching_report_id="rep-uuid-9999-8888",
            )
            return output, 1.0, 10, "mock-model"


    agent = ForensicsAgent(ai_engine=MockDuplicateAIEngine())
    state = {
        "report_id": "test-rep-002",
        "raw_payload": {"media_urls": ["https://example.com/duplicate_photo.jpg"]},
    }
    result = await agent.process(state)
    forensics_out = result["agent_outputs"]["forensics"]


    assert forensics_out["duplicate_detected"] is True
    assert forensics_out["matching_report_id"] == "rep-uuid-9999-8888"
    assert forensics_out["authentic"] is False


@pytest.mark.asyncio
async def test_notification_agent_process():
    """Verify NotificationAgent processes state and returns notification payload (CQ-01)."""

    from backend.agents.notifier import NotificationAgent

    agent = NotificationAgent()
    state = {
        "report_id": "rep-abc-12345678",
        "agent_outputs": {
            "classification": {"category": "ROADS"},
            "geo_validation": {"ward_name": "Aundh-Baner"},
            "routing": {"department_name": "Roads Department", "sla_target_hours": 48},
        },
    }
    output = await agent.process(state)

    notif = output["agent_outputs"]["notification"]

    assert notif["status"] == "DISPATCHED"
    assert notif["points_awarded"] == 15
    assert "ROADS" in notif["body"]
    assert "Aundh-Baner" in notif["body"]


@pytest.mark.asyncio
async def test_forensics_trust_score_and_metadata_validation():
    """Verify ForensicsAgent calculates trust_score and validates metadata (capture_source, HMAC, distance)."""
    import hashlib
    import hmac

    from backend.agents.forensics import ForensicsAgent, ForensicsPydanticOutput

    secret = "civicconnect_secret_key"
    hash_str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    sig = hmac.new(secret.encode("utf-8"), hash_str.encode("utf-8"), hashlib.sha256).hexdigest()

    class MockTrustEngine(BaseAIEngine):
        async def generate_structured(self, prompt, response_model, system_prompt=None, temperature=0.2, image_urls=None):
            output = ForensicsPydanticOutput(
                authentic=True,
                supports_report=True,
                reported_issue_visible=True,
                issue_category_match=True,
                source_type="camera_photo",
                quality_ok=True,
                ai_generated=False,
                manipulated=False,
                confidence=0.95,
                reason="Camera photo evidence verified",
                duplicate_detected=False,
            )
            return output, 1.0, 10, "mock-model"

    agent = ForensicsAgent(ai_engine=MockTrustEngine())
    state = {
        "report_id": "test-rep-003",
        "raw_payload": {
            "latitude": 18.5204,
            "longitude": 73.8567,
            "media_urls": ["https://example.com/live_photo.jpg"],
            "photo_metadata": [
                {
                    "url": "https://example.com/live_photo.jpg",
                    "capture_source": "camera",
                    "latitude": 18.5205,
                    "longitude": 73.8568,
                    "gps_accuracy_m": 5.0,
                    "sha256_hash": hash_str,
                    "hmac_signature": sig,
                }
            ],
        },
    }
    result = await agent.process(state)
    forensics = result["agent_outputs"]["forensics"]

    assert forensics["trust_score"] == 100
    assert forensics["signature_valid"] is True
    assert forensics["capture_source"] == "camera"
    assert forensics["location_uncertain"] is None


