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


def test_geo_validator_bounding_box_match():
    """Verify Geo-Validator correctly matches Pune PMC Aundh-Baner ward coordinates."""
    agent = GeoValidationAgent(db_session_factory=None)
    state = {
        "report_id": "test-rep-001",
        "raw_payload": {"latitude": 18.55, "longitude": 73.80},
    }
    output = agent.process(state)
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
    def generate_structured(self, prompt, response_model, system_prompt=None, temperature=0.2):
        sys_str = system_prompt or ""
        if "Forensics" in sys_str:
            data = {"authentic": True, "confidence": 0.99, "reason": "Mock forensics pass", "duplicate_detected": False}
        elif "Classifier" in sys_str:
            data = {"category": "ROADS", "priority": "P2", "urgency": "high", "department_code": "PMC_DEPT_ROADS", "confidence": 0.95, "summary": "Pothole report"}
        elif "Moderation" in sys_str:
            data = {"approved": True, "toxicity_score": 0.0, "flagged_reason": "", "pii_found": False, "sanitized_text": prompt}
        elif "Enhancement" in sys_str:
            data = {"enhanced_title": "Pothole Issue", "enhanced_description": prompt, "key_tags": ["pothole", "roads"]}
        elif "Router" in sys_str:
            data = {"department_code": "PMC_DEPT_ROADS", "ward_name": "Aundh-Baner", "estimated_sla_hours": 48, "routing_reason": "Road issue in Aundh"}
        else:
            data = {}

        obj = response_model.model_validate(data)
        return obj, 1.0, 10, "mock-model"


def test_full_pipeline_graph_execution():
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

    final_state = graph.invoke(initial_state)

    assert final_state["report_id"] == "report-12345"
    assert final_state["pipeline_status"] == "PROCESSING"

    outputs = final_state["agent_outputs"]
    assert "geo_validation" in outputs
    assert "classification" in outputs
    assert "enhancement" in outputs
    assert "routing" in outputs
    assert "notification" in outputs

    assert outputs["geo_validation"]["boundary_matched"] is True
    assert outputs["routing"]["department_code"] in ["PMC_DEPT_ROADS", "PMC_DEPT_DRAIN", "PMC_DEPT_ADMIN"]
