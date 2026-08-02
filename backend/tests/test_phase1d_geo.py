"""Phase-1D Geo Verification Test Suite for CivicConnect.

Tests the Geo Verification Engine under strict Phase 1D security rules:
1. Basic Coordinate Validation: Range checks, NaN/Infinity handling, structural numeric parsing.
2. Spatial PostGIS & Municipal Boundary Analysis: PostGIS queries, POINT(lon, lat) ordering, SRID:4326.
3. Three-State Semantics: Distinguishes True (authoritative PostGIS match), False (out-of-bounds), and None (GIS unavailable or dev bbox fallback).
4. Bounding Box Fallback Semantics: Dev bbox match produces analysis_status="PARTIAL", boundary_matched=None, approximate_boundary_match=True.
5. Failure Semantics & Fail-Safe Integration: Infrastructure/DB failure produces UNAVAILABLE without citizen rejection.
6. Security Hardening: Parameterized SQL injection resistance, client hint isolation.
7. Boundary Uncertainty: Configurable geo_boundary_uncertainty_meters threshold & near_boundary detection.
8. LangGraph Pipeline Integration: End-to-end multi-agent workflow validation.
"""

from __future__ import annotations

import math
from typing import Any
import pytest
from sqlalchemy.exc import OperationalError

from backend.agents.geo_validator import GeoValidationAgent, PUNE_PMC_BOUNDARIES
from backend.agents.pipeline import create_civic_pipeline_graph
from backend.core.config import settings


# ---------------------------------------------------------------------------
# Override global conftest DB fixture — Geo tests use mock DB factories
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_and_cleanup_db():
    yield


# ---------------------------------------------------------------------------
# Mock DB Session Factories for PostGIS Query Testing
# ---------------------------------------------------------------------------

class MockExecuteResult:
    def __init__(self, row: tuple | None) -> None:
        self._row = row

    def fetchone(self) -> tuple | None:
        return self._row


class MockAsyncSession:
    def __init__(self, row: tuple | None, should_fail: bool = False) -> None:
        self.row = row
        self.should_fail = should_fail
        self.last_params: dict[str, Any] = {}

    async def __aenter__(self) -> MockAsyncSession:
        if self.should_fail:
            raise OperationalError("SELECT * FROM departments", {}, Exception("PostGIS Connection Timeout"))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def execute(self, query: Any, params: dict[str, Any]) -> MockExecuteResult:
        if self.should_fail:
            raise OperationalError("ST_Covers query failed", params, Exception("PostGIS 503 Unavailable"))
        self.last_params = params
        return MockExecuteResult(self.row)


def make_mock_db_factory(row: tuple | None = None, should_fail: bool = False):
    def factory():
        return MockAsyncSession(row=row, should_fail=should_fail)
    return factory


# ---------------------------------------------------------------------------
# 1. Basic Coordinate Validation Tests (Tests 1 to 10)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_01_valid_pune_coordinates_bbox_fallback():
    """TEST 1: Valid Pune coordinates without DB session produce PARTIAL status with unconfirmed boundary."""
    agent = GeoValidationAgent(db_session_factory=None)
    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "PARTIAL"
    assert geo["coordinates_valid"] is True
    assert geo["municipality_matched"] is None  # Authoritative match unconfirmed
    assert geo["boundary_matched"] is None      # Authoritative ward match unconfirmed
    assert geo["ward_id"] == "WARD_03"
    assert geo["signals"]["approximate_boundary_match"] is True


@pytest.mark.asyncio
async def test_02_latitude_above_90():
    """TEST 2: Latitude > 90 is structurally invalid."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 91.5, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert geo["municipality_matched"] is False
    assert geo["boundary_matched"] is False
    assert "structurally_invalid_coordinates" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_03_latitude_below_minus_90():
    """TEST 3: Latitude < -90 is structurally invalid."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": -95.0, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert geo["municipality_matched"] is False
    assert geo["boundary_matched"] is False


@pytest.mark.asyncio
async def test_04_longitude_above_180():
    """TEST 4: Longitude > 180 is structurally invalid."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 18.5204, "longitude": 185.0}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert geo["municipality_matched"] is False


@pytest.mark.asyncio
async def test_05_longitude_below_minus_180():
    """TEST 5: Longitude < -180 is structurally invalid."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 18.5204, "longitude": -190.0}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False


@pytest.mark.asyncio
async def test_06_nan_coordinates():
    """TEST 6: NaN coordinate inputs handled gracefully without throwing exception."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": float("nan"), "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert geo["boundary_matched"] is False


@pytest.mark.asyncio
async def test_07_infinity_coordinates():
    """TEST 7: Infinity coordinates handled gracefully."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": float("inf"), "longitude": float("-inf")}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert geo["boundary_matched"] is False


@pytest.mark.asyncio
async def test_08_non_numeric_coordinates():
    """TEST 8: Non-numeric strings handled as invalid coordinates."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": "eighteen", "longitude": "seventy-three"}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert geo["boundary_matched"] is False


@pytest.mark.asyncio
async def test_09_missing_latitude():
    """TEST 9: Missing latitude returns PARTIAL status with None signal semantics."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "PARTIAL"
    assert geo["coordinates_valid"] is None
    assert geo["municipality_matched"] is None
    assert geo["boundary_matched"] is None
    assert "missing_gps_coordinates" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_10_missing_longitude():
    """TEST 10: Missing longitude returns PARTIAL status."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 18.5204}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "PARTIAL"
    assert geo["coordinates_valid"] is None
    assert geo["boundary_matched"] is None


# ---------------------------------------------------------------------------
# 2. PostGIS & Municipality Tests (Tests 11 to 17)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_11_point_inside_municipality_postgis():
    """TEST 11: Authoritative PostGIS query returns SUCCESS status and matched boundary."""
    mock_row = ("WARD_03", "Shivajinagar-Ghole Road", "Zone 2", True, 150.0)
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is True
    assert geo["municipality_matched"] is True
    assert geo["boundary_matched"] is True
    assert geo["ward_id"] == "WARD_03"
    assert geo["near_boundary"] is False


@pytest.mark.asyncio
async def test_12_point_outside_municipality():
    """TEST 12: Point outside Pune regional envelope returns SUCCESS with municipality_matched=False."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 28.6139, "longitude": 77.2090}}  # Delhi coordinates
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is True
    assert geo["municipality_matched"] is False
    assert geo["boundary_matched"] is False
    assert geo["confidence"] == 0.95  # High confidence in negative determination
    assert "outside_supported_municipality" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_13_point_inside_known_ward_bbox_fallback():
    """TEST 13: Point inside known dev ward bbox produces PARTIAL status and ward metadata."""
    agent = GeoValidationAgent(db_session_factory=None)
    state = {"raw_payload": {"latitude": 18.5600, "longitude": 73.8000}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "PARTIAL"
    assert geo["boundary_matched"] is None  # Dev bbox != authoritative match
    assert geo["ward_id"] == "WARD_01"
    assert geo["ward_name"] == "Aundh-Baner"


@pytest.mark.asyncio
async def test_14_point_on_polygon_boundary():
    """TEST 14: Point exactly on boundary covered by PostGIS ST_Covers."""
    mock_row = ("WARD_02", "Kothrud-Bavdhan", "Zone 1", True, 0.0)
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5000, "longitude": 73.8000}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["boundary_matched"] is True
    assert geo["near_boundary"] is True
    assert "near_ward_boundary" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_15_point_near_ward_boundary():
    """TEST 15: Point within 15 meters of boundary triggers near_boundary flag."""
    mock_row = ("WARD_01", "Aundh-Baner", "Zone 1", True, 15.0)  # 15m <= 30m threshold
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5500, "longitude": 73.8100}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["boundary_matched"] is True
    assert geo["near_boundary"] is True
    assert "near_ward_boundary" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_16_coordinate_order_postgis_point():
    """TEST 16: Verifies POINT(longitude latitude) ordering in PostGIS spatial query."""
    mock_row = ("WARD_03", "Shivajinagar", "Zone 2", True, 100.0)
    factory = make_mock_db_factory(mock_row)
    agent = GeoValidationAgent(db_session_factory=factory)

    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["details"]["point_wkt"] == "POINT(73.8567 18.5204)"
    assert geo["details"]["srid"] == 4326


@pytest.mark.asyncio
async def test_17_srid_4326_behavior():
    """TEST 17: Ensures EPSG:4326 is passed into spatial query details."""
    mock_row = ("WARD_04", "Kasba-Vishrambaug", "Zone 2", True, 50.0)
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5100, "longitude": 73.8500}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["details"]["srid"] == 4326


# ---------------------------------------------------------------------------
# 3. Failure Semantics & Fail-Safe Integration (Tests 18 to 21)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_18_postgis_timeout_failsafe():
    """TEST 18: PostGIS timeout returns UNAVAILABLE status without failing closed as False."""
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(should_fail=True))
    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}

    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "UNAVAILABLE"
    assert geo["coordinates_valid"] is True
    assert geo["municipality_matched"] is None
    assert geo["boundary_matched"] is None
    assert "geo_database_unavailable" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_19_database_unavailable_does_not_reject():
    """TEST 19: Database unavailability does not emit boundary_matched=False."""
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(should_fail=True))
    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}

    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["boundary_matched"] is not False  # Must be None, NOT False


@pytest.mark.asyncio
async def test_20_missing_ward_dataset():
    """TEST 20: Missing ward dataset returns UNAVAILABLE state."""
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(row=None))
    agent._query_pmc_bounding_box = lambda lat, lon, acc, src: agent._build_unavailable_result(acc, src, "Dataset missing")

    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "UNAVAILABLE"
    assert geo["boundary_matched"] is None


@pytest.mark.asyncio
async def test_21_malformed_stored_geometry_failsafe():
    """TEST 21: PostGIS geometry error fails safe to UNAVAILABLE."""
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(should_fail=True))
    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}

    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "UNAVAILABLE"
    assert geo["confidence"] == 0.0


# ---------------------------------------------------------------------------
# 4. Security Hardening Tests (Tests 22 to 25)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_22_sql_injection_coordinate_strings():
    """TEST 22: SQL injection payloads in coordinate fields handled safely."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": "18.5204'; DROP TABLE departments; --", "longitude": "73.8567"}}

    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["analysis_status"] == "SUCCESS"
    assert geo["coordinates_valid"] is False
    assert "structurally_invalid_coordinates" in geo["risk_flags"]


@pytest.mark.asyncio
async def test_23_client_provided_fake_distance_ignored():
    """TEST 23: Untrusted client capture_distance field is not trusted or echoed as proof."""
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(("WARD_03", "Shivajinagar", "Zone 2", True, 100.0)))
    state = {
        "raw_payload": {
            "latitude": 18.5204,
            "longitude": 73.8567,
            "capture_distance": 0.0,
            "distance_from_location": 0.0,
        }
    }

    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["boundary_matched"] is True
    assert "capture_distance" not in geo["signals"]


@pytest.mark.asyncio
async def test_24_high_precision_malicious_coordinates():
    """TEST 24: High decimal precision does not grant arbitrary trust or bypass boundaries."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 40.71277533211942, "longitude": -74.00597281093841}}

    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["municipality_matched"] is False
    assert geo["boundary_matched"] is False


@pytest.mark.asyncio
async def test_25_geo_component_cannot_emit_verification_decision():
    """TEST 25: Geo Verification component cannot independently set verification_decision."""
    agent = GeoValidationAgent()
    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}

    result = await agent.process(state)
    assert "verification_decision" not in result
    assert "pipeline_status" not in result


# ---------------------------------------------------------------------------
# 5. Boundary Uncertainty Tests (Tests 26 to 28)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_26_point_well_inside_ward():
    """TEST 26: Point 200 meters inside ward boundary has near_boundary=False."""
    mock_row = ("WARD_03", "Shivajinagar", "Zone 2", True, 200.0)
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["near_boundary"] is False
    assert "near_ward_boundary" not in geo["risk_flags"]
    assert geo["confidence"] == 0.95


@pytest.mark.asyncio
async def test_27_point_within_boundary_uncertainty(monkeypatch):
    """TEST 27: Point within configured 30m boundary uncertainty has near_boundary=True."""
    monkeypatch.setattr(settings, "geo_boundary_uncertainty_meters", 30.0)
    mock_row = ("WARD_03", "Shivajinagar", "Zone 2", True, 20.0)  # 20m <= 30m
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["near_boundary"] is True
    assert "near_ward_boundary" in geo["risk_flags"]
    assert geo["confidence"] == 0.80


@pytest.mark.asyncio
async def test_28_point_exactly_on_boundary():
    """TEST 28: Point 0.0m from boundary ring has near_boundary=True."""
    mock_row = ("WARD_01", "Aundh-Baner", "Zone 1", True, 0.0)
    agent = GeoValidationAgent(db_session_factory=make_mock_db_factory(mock_row))

    state = {"raw_payload": {"latitude": 18.5500, "longitude": 73.8000}}
    result = await agent.process(state)
    geo = result["agent_outputs"]["geo_validation"]

    assert geo["near_boundary"] is True
    assert "near_ward_boundary" in geo["risk_flags"]


# ---------------------------------------------------------------------------
# 6. Graph Integration & Three-State Semantics (Tests 29 to 32)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_29_pipeline_integration_geo_output_survives_fan_in():
    """TEST 29: Geo Verification node output survives LangGraph fan-in reducer."""
    from backend.tests.test_phase1e_issue_intelligence import MockAIEngineSuccess
    from backend.agents.classifier import IssueIntelligencePydanticOutput
    factory = make_mock_db_factory(("WARD_03", "Shivajinagar", "Zone 2", True, 100.0))
    mock_ai = MockAIEngineSuccess(IssueIntelligencePydanticOutput(
        civic_relevance=True, category="ROADS", subcategory="POTHOLE", severity="MEDIUM", urgency="MEDIUM", confidence=0.9, tags=["pothole"]
    ))
    graph = create_civic_pipeline_graph(db_session_factory=factory, ai_engine=mock_ai)
    initial_state = {
        "report_id": "rep-geo-test-29",
        "citizen_id": "cit-101",
        "raw_payload": {
            "text": "Pothole on Baner Road near Aundh",
            "latitude": 18.5500,
            "longitude": 73.8000,
            "media_urls": ["https://example.com/pothole.jpg"],
        },
    }

    final_state = await graph.ainvoke(initial_state)
    agent_outputs = final_state.get("agent_outputs", {})

    assert "geo_validation" in agent_outputs
    assert final_state["verification_decision"] in ("VERIFIED", "PENDING_MANUAL_REVIEW", "REJECTED")


@pytest.mark.asyncio
async def test_30_quality_gate_sees_geo_output():
    """TEST 30: Quality Gate evaluates geo_validation output correctly."""
    from backend.tests.test_phase1e_issue_intelligence import MockAIEngineSuccess
    from backend.agents.classifier import IssueIntelligencePydanticOutput
    factory = make_mock_db_factory(("WARD_02", "Kothrud", "Zone 1", True, 50.0))
    mock_ai = MockAIEngineSuccess(IssueIntelligencePydanticOutput(
        civic_relevance=True, category="WATER", subcategory="WATER_LEAK", severity="MEDIUM", urgency="MEDIUM", confidence=0.9, tags=["water"]
    ))
    graph = create_civic_pipeline_graph(db_session_factory=factory, ai_engine=mock_ai)
    initial_state = {
        "report_id": "rep-geo-test-30",
        "raw_payload": {
            "text": "Water leakage in Kothrud",
            "latitude": 18.5000,
            "longitude": 73.8100,
            "media_urls": ["https://example.com/water.jpg"],
        },
    }

    final_state = await graph.ainvoke(initial_state)
    assert final_state["pipeline_status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_31_explicit_three_state_municipality_semantics():
    """TEST 31: Explicitly verifies distinction between False (out-of-bounds) and None (GIS failure / unconfirmed bbox)."""
    agent_normal = GeoValidationAgent()
    state_out = {"raw_payload": {"latitude": 28.6139, "longitude": 77.2090}}
    res_out = await agent_normal.process(state_out)
    geo_out = res_out["agent_outputs"]["geo_validation"]

    agent_failed = GeoValidationAgent(db_session_factory=make_mock_db_factory(should_fail=True))
    state_fail = {"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}}
    res_fail = await agent_failed.process(state_fail)
    geo_fail = res_fail["agent_outputs"]["geo_validation"]

    # OUTSIDE MUNICIPALITY -> False
    assert geo_out["municipality_matched"] is False
    assert geo_out["analysis_status"] == "SUCCESS"

    # GIS FAILURE -> None
    assert geo_fail["municipality_matched"] is None
    assert geo_fail["analysis_status"] == "UNAVAILABLE"

    # Must NOT collapse into the same value!
    assert geo_out["municipality_matched"] != geo_fail["municipality_matched"]


@pytest.mark.asyncio
async def test_32_explicit_three_state_boundary_semantics():
    """TEST 32: Verifies True (PostGIS match) vs False (Unmatched) vs None (GIS Unavailable / dev bbox fallback)."""
    # 1. True (Authoritative PostGIS Matched)
    agent_match = GeoValidationAgent(db_session_factory=make_mock_db_factory(("WARD_03", "Shivajinagar", "Zone 2", True, 100.0)))
    res_match = await agent_match.process({"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}})
    assert res_match["agent_outputs"]["geo_validation"]["boundary_matched"] is True
    assert res_match["agent_outputs"]["geo_validation"]["analysis_status"] == "SUCCESS"

    # 2. False (Confirmed Unmatched)
    agent_outside = GeoValidationAgent()
    res_unmatch = await agent_outside.process({"raw_payload": {"latitude": 28.6139, "longitude": 77.2090}})
    assert res_unmatch["agent_outputs"]["geo_validation"]["boundary_matched"] is False
    assert res_unmatch["agent_outputs"]["geo_validation"]["analysis_status"] == "SUCCESS"

    # 3. None (GIS Unavailable or Dev Bbox Fallback)
    agent_fail = GeoValidationAgent(db_session_factory=make_mock_db_factory(should_fail=True))
    res_fail = await agent_fail.process({"raw_payload": {"latitude": 18.5204, "longitude": 73.8567}})
    assert res_fail["agent_outputs"]["geo_validation"]["boundary_matched"] is None
    assert res_fail["agent_outputs"]["geo_validation"]["analysis_status"] == "UNAVAILABLE"
