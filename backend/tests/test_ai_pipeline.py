"""Comprehensive Test Suite for CivicConnect Multi-Agent AI Engine & LangGraph Pipeline.

Tests:
1. State Reducer merging parallel dictionary outputs
2. Atomic Redis Token Bucket Limiter fallback logic
3. Geo-Validator PostGIS boundary & PMC bounding-box lookups
4. Classifier regex fallbacks and Presidio placeholder prompts
5. Full LangGraph state graph compilation & end-to-end execution
"""

import pytest
from backend.agents.classifier import ClassificationAgent
from backend.agents.geo_validator import GeoValidationAgent
from backend.agents.pipeline import create_civic_pipeline_graph
from backend.agents.state import merge_agent_outputs
from backend.core.rate_limiter import RedisTokenBucketLimiter


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
    """Verify Classifier applies regex rule fallback for pothole issues."""
    agent = ClassificationAgent()
    fallback_res = agent._rule_fallback("Deep pothole on main road causing severe traffic jam")

    assert fallback_res["category"] == "ROADS"
    assert fallback_res["urgency"] == "high"
    assert fallback_res["fallback_used"] is True


def test_full_pipeline_graph_execution():
    """Verify full end-to-end execution of compiled LangGraph workflow."""
    graph = create_civic_pipeline_graph()
    
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
