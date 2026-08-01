"""Phase-1A Hardened Test Suite — LangGraph Foundation.

Covers all 30 required tests from the Phase-1A hardening spec.
No live AI providers. All external calls mocked.
No database connection required.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.pipeline import (
    DECISION_PENDING_MANUAL_REVIEW,
    DECISION_REJECTED,
    DECISION_VERIFIED,
    REQUIRED_VERIFICATION_OUTPUTS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PROCESSING,
    _validate_prerequisites,
    create_civic_pipeline_graph,
    quality_gate_node,
    supervisor_node,
)
from backend.agents.state import PipelineSharedState, merge_agent_outputs
from backend.core.ai_engine import BaseAIEngine


# ---------------------------------------------------------------------------
# Override global conftest DB fixture — Phase-1A tests are DB-free
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_and_cleanup_db():  # type: ignore[override]
    yield


# ---------------------------------------------------------------------------
# Mock AI Engine
# ---------------------------------------------------------------------------

class MockAIEngine(BaseAIEngine):
    async def generate_structured(self, prompt, response_model, system_prompt=None,
                                   temperature=0.2, image_urls=None):
        sys_str = system_prompt or ""
        if "Forensics" in sys_str or "forensic" in sys_str.lower():
            data = {"authentic": True, "supports_report": True,
                    "reported_issue_visible": True, "issue_category_match": True,
                    "source_type": "camera_photo", "quality_ok": True,
                    "ai_generated": False, "manipulated": False, "confidence": 0.92,
                    "reason": "Mock forensics", "duplicate_detected": False}
        elif "Safety" in sys_str or "Moderat" in sys_str or "moderator" in sys_str.lower():
            data = {"clean": True, "flags": [], "toxicity_score": 0.01,
                    "confidence": 0.99, "requires_human_review": False,
                    "safe_for_processing": True}
        elif "Classifier" in sys_str or "classif" in sys_str.lower():
            data = {"category": "ROADS", "urgency": "high", "tags": ["pothole"], "confidence": 0.91}
        else:
            data = {}
        return response_model.model_validate(data), 1.0, 10, "mock-model"


@pytest.fixture
def mock_engine():
    return MockAIEngine()


@pytest.fixture
def base_initial_state():
    return {
        "report_id": "rep-test-001",
        "raw_payload": {
            "description": "Pothole on Baner road.",
            "latitude": 18.55, "longitude": 73.80, "media_urls": [],
        },
        "agent_outputs": {},
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _full_state(overrides: dict[str, Any] | None = None) -> PipelineSharedState:
    """Returns a state dict with all four required verification outputs."""
    s: PipelineSharedState = {
        "report_id": "rep-helper-001",
        "agent_outputs": {
            "safety": {"clean": True, "flags": [], "confidence": 0.99},
            "visual_verification": {"supports_report": True, "evidence_confidence": 0.90,
                                    "signals": {}, "risk_flags": []},
            "geo_validation": {"boundary_matched": True, "ward_name": "Aundh", "confidence": 0.99},
            "issue_intelligence": {"category": "ROADS", "confidence": 0.91, "tags": []},
        },
    }
    if overrides:
        s.update(overrides)  # type: ignore[arg-type]
    return s


# ===========================================================================
# TEST 01 — Supervisor initializes required state fields
# ===========================================================================

def test_01_supervisor_initializes_state():
    state = {"report_id": "r1", "raw_payload": {"description": "Pothole"}, "agent_outputs": {}}
    result = supervisor_node(state)
    assert result["report_id"] == "r1"
    assert result["pipeline_status"] == STATUS_PROCESSING
    assert result["verification_decision"] == ""
    assert "workflow_run_id" in result
    assert result["sanitised_text"] == "Pothole"
    assert result["agent_outputs"]["supervisor"]["status"] == "INITIALIZED"


# ===========================================================================
# TEST 02 — Supervisor generates workflow_run_id for new execution
# ===========================================================================

def test_02_supervisor_generates_workflow_run_id_for_new_execution():
    state = {"report_id": "r2", "raw_payload": {"description": "test"}, "agent_outputs": {}}
    result = supervisor_node(state)
    wfr = result["workflow_run_id"]
    assert isinstance(wfr, str) and len(wfr) > 0


# ===========================================================================
# TEST 03 — Supervisor preserves existing workflow_run_id
# ===========================================================================

def test_03_supervisor_preserves_existing_workflow_run_id():
    existing = "existing-run-123"
    state = {"report_id": "r3", "workflow_run_id": existing,
             "raw_payload": {"description": "test"}, "agent_outputs": {}}
    result = supervisor_node(state)
    assert result["workflow_run_id"] == existing


# ===========================================================================
# TEST 04 — Four verification branches execute
# ===========================================================================

@pytest.mark.asyncio
async def test_04_four_verification_branches_execute(mock_engine, base_initial_state):
    graph = create_civic_pipeline_graph(ai_engine=mock_engine)
    final = await graph.ainvoke(base_initial_state)
    outputs = final["agent_outputs"]
    for key in REQUIRED_VERIFICATION_OUTPUTS:
        assert key in outputs, f"Missing key: {key}"


# ===========================================================================
# TEST 05 — Parallel outputs survive reducer fan-in
# ===========================================================================

def test_05_parallel_outputs_survive_reducer():
    merged = {}
    for key in ["safety", "visual_verification", "geo_validation", "issue_intelligence"]:
        merged = merge_agent_outputs(merged, {key: {"data": key}})
    for key in ["safety", "visual_verification", "geo_validation", "issue_intelligence"]:
        assert key in merged
        assert merged[key]["data"] == key


# ===========================================================================
# TEST 06 — Quality Gate executes exactly once in compiled LangGraph
# ===========================================================================

@pytest.mark.asyncio
async def test_06_quality_gate_executes_exactly_once(mock_engine, base_initial_state):
    """Proves Quality Gate executes EXACTLY ONCE when compiled fan-in graph runs."""
    quality_gate_call_count = 0

    def counting_quality_gate(state):
        nonlocal quality_gate_call_count
        quality_gate_call_count += 1
        return quality_gate_node(state)

    from langgraph.graph import END, START, StateGraph
    from backend.agents.pipeline import (
        make_geo_node,
        make_issue_intelligence_node,
        make_safety_node,
        make_visual_verification_node,
        route_after_quality_gate,
    )
    from backend.agents.classifier import ClassificationAgent
    from backend.agents.forensics import ForensicsAgent
    from backend.agents.geo_validator import GeoValidationAgent
    from backend.agents.moderator import ModerationAgent
    from backend.agents.state import PipelineSharedState

    safety_agent = ModerationAgent(ai_engine=mock_engine)
    visual_agent = ForensicsAgent(ai_engine=mock_engine)
    geo_agent = GeoValidationAgent(db_session_factory=None)
    issue_agent = ClassificationAgent(ai_engine=mock_engine)

    workflow: Any = StateGraph(PipelineSharedState)  # type: ignore
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("safety", make_safety_node(safety_agent))
    workflow.add_node("visual_verification", make_visual_verification_node(visual_agent))
    workflow.add_node("geo_validator", make_geo_node(geo_agent))
    workflow.add_node("issue_intelligence", make_issue_intelligence_node(issue_agent))
    workflow.add_node("quality_gate", counting_quality_gate)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "safety")
    workflow.add_edge("supervisor", "visual_verification")
    workflow.add_edge("supervisor", "geo_validator")
    workflow.add_edge("supervisor", "issue_intelligence")
    workflow.add_edge(
        ["safety", "visual_verification", "geo_validator", "issue_intelligence"],
        "quality_gate",
    )
    workflow.add_conditional_edges(
        "quality_gate",
        route_after_quality_gate,
        {"verified": END, "rejected": END, "pending_review": END},
    )

    graph = workflow.compile()
    await graph.ainvoke(base_initial_state)

    assert quality_gate_call_count == 1


def test_quality_gate_emits_single_valid_decision_contract(mock_engine, base_initial_state):
    """Quality Gate output contains a valid decision contract string."""
    state = _full_state()
    res = quality_gate_node(state)
    qg = res["agent_outputs"]["quality_gate"]
    assert isinstance(qg["verification_decision"], str)
    assert qg["verification_decision"] in (
        DECISION_VERIFIED,
        DECISION_REJECTED,
        DECISION_PENDING_MANUAL_REVIEW,
    )


# ===========================================================================
# TEST 07 — Quality Gate executes only after all four branches (staggered async)
# ===========================================================================

@pytest.mark.asyncio
async def test_07_quality_gate_sees_all_four_outputs_after_staggered_branches():
    """Staggered async branches: Quality Gate must execute after all branches finish."""
    events: list[str] = []
    quality_gate_call_count = 0

    async def slow_safety(state):
        await asyncio.sleep(0.01)
        events.append("safety_complete")
        return {"agent_outputs": {"safety": {"clean": True, "flags": [], "confidence": 0.99}}}

    async def slow_visual(state):
        await asyncio.sleep(0.05)
        events.append("visual_complete")
        return {"agent_outputs": {"visual_verification": {
            "supports_report": True, "evidence_confidence": 0.90,
            "signals": {}, "risk_flags": []}}}

    async def slow_geo(state):
        await asyncio.sleep(0.02)
        events.append("geo_complete")
        return {"agent_outputs": {"geo_validation": {"boundary_matched": True, "confidence": 0.99}}}

    async def slow_issue(state):
        await asyncio.sleep(0.03)
        events.append("issue_complete")
        return {"agent_outputs": {"issue_intelligence": {
            "category": "ROADS", "confidence": 0.91, "tags": []}}}

    def counting_quality_gate(state):
        nonlocal quality_gate_call_count
        quality_gate_call_count += 1
        events.append("quality_gate")
        return quality_gate_node(state)

    from langgraph.graph import END, START, StateGraph
    from backend.agents.state import PipelineSharedState

    workflow: Any = StateGraph(PipelineSharedState)  # type: ignore
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("safety", slow_safety)
    workflow.add_node("visual_verification", slow_visual)
    workflow.add_node("geo_validator", slow_geo)
    workflow.add_node("issue_intelligence", slow_issue)
    workflow.add_node("quality_gate", counting_quality_gate)
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "safety")
    workflow.add_edge("supervisor", "visual_verification")
    workflow.add_edge("supervisor", "geo_validator")
    workflow.add_edge("supervisor", "issue_intelligence")
    workflow.add_edge(
        ["safety", "visual_verification", "geo_validator", "issue_intelligence"],
        "quality_gate",
    )
    workflow.add_edge("quality_gate", END)
    graph = workflow.compile()

    final = await graph.ainvoke({
        "report_id": "rep-stagger-001",
        "raw_payload": {"description": "test", "latitude": 18.55, "longitude": 73.80},
        "agent_outputs": {},
    })

    # 1. Quality Gate executed exactly once
    assert quality_gate_call_count == 1

    # 2. All four completion events exist
    for evt in ["safety_complete", "visual_complete", "geo_complete", "issue_complete"]:
        assert evt in events, f"Missing completion event: {evt}"

    # 3. Quality Gate occurs AFTER all verification completions
    qg_index = events.index("quality_gate")
    assert events.index("safety_complete") < qg_index
    assert events.index("visual_complete") < qg_index
    assert events.index("geo_complete") < qg_index
    assert events.index("issue_complete") < qg_index


# ===========================================================================
# TEST 08-10 — VERIFIED / REJECTED / PENDING_MANUAL_REVIEW reach END
# ===========================================================================

@pytest.mark.asyncio
async def test_08_verified_reaches_end(mock_engine, base_initial_state):
    from backend.tests.test_phase1d_geo import make_mock_db_factory
    mock_db = make_mock_db_factory(("WARD_03", "Shivajinagar", "Zone 2", True, 100.0))
    graph = create_civic_pipeline_graph(ai_engine=mock_engine, db_session_factory=mock_db)
    final = await graph.ainvoke(base_initial_state)
    assert final["pipeline_status"] == STATUS_COMPLETED
    assert final["verification_decision"] == DECISION_VERIFIED


def test_09_rejected_reaches_end():
    state = _full_state()
    state["agent_outputs"]["safety"] = {"clean": False, "flags": ["prompt_injection"], "confidence": 0.99}
    result = quality_gate_node(state)
    assert result["verification_decision"] == DECISION_REJECTED
    assert result["pipeline_status"] == STATUS_COMPLETED


def test_10_pending_manual_review_reaches_end():
    state = _full_state()
    state["agent_outputs"]["issue_intelligence"]["confidence"] = 0.40
    result = quality_gate_node(state)
    assert result["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert result["pipeline_status"] == STATUS_COMPLETED


# ===========================================================================
# TEST 11-12 — REJECTED and PENDING both use pipeline_status = COMPLETED
# ===========================================================================

def test_11_rejected_uses_pipeline_status_completed():
    state = _full_state()
    state["agent_outputs"]["safety"] = {"clean": False, "flags": ["toxicity"], "confidence": 0.99}
    result = quality_gate_node(state)
    assert result["verification_decision"] == DECISION_REJECTED
    assert result["pipeline_status"] == STATUS_COMPLETED
    assert result["pipeline_status"] != STATUS_FAILED


def test_12_pending_manual_review_uses_pipeline_status_completed():
    state = _full_state()
    state["agent_outputs"]["geo_validation"]["boundary_matched"] = False
    result = quality_gate_node(state)
    assert result["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert result["pipeline_status"] == STATUS_COMPLETED


# ===========================================================================
# TESTS 13-18 — Fail-closed: missing/malformed outputs cannot VERIFIED
# ===========================================================================

def test_13_missing_safety_cannot_verified():
    state: PipelineSharedState = {"report_id": "r13", "agent_outputs": {
        "visual_verification": {"supports_report": True, "evidence_confidence": 0.90, "risk_flags": []},
        "geo_validation": {"boundary_matched": True, "confidence": 0.99},
        "issue_intelligence": {"category": "ROADS", "confidence": 0.91},
    }}
    result = quality_gate_node(state)
    assert result["verification_decision"] != DECISION_VERIFIED


def test_14_missing_visual_cannot_verified():
    state: PipelineSharedState = {"report_id": "r14", "agent_outputs": {
        "safety": {"clean": True, "flags": [], "confidence": 0.99},
        "geo_validation": {"boundary_matched": True, "confidence": 0.99},
        "issue_intelligence": {"category": "ROADS", "confidence": 0.91},
    }}
    result = quality_gate_node(state)
    assert result["verification_decision"] != DECISION_VERIFIED


def test_15_missing_geo_cannot_verified():
    state: PipelineSharedState = {"report_id": "r15", "agent_outputs": {
        "safety": {"clean": True, "flags": [], "confidence": 0.99},
        "visual_verification": {"supports_report": True, "evidence_confidence": 0.90, "risk_flags": []},
        "issue_intelligence": {"category": "ROADS", "confidence": 0.91},
    }}
    result = quality_gate_node(state)
    assert result["verification_decision"] != DECISION_VERIFIED


def test_16_missing_issue_intelligence_cannot_verified():
    state: PipelineSharedState = {"report_id": "r16", "agent_outputs": {
        "safety": {"clean": True, "flags": [], "confidence": 0.99},
        "visual_verification": {"supports_report": True, "evidence_confidence": 0.90, "risk_flags": []},
        "geo_validation": {"boundary_matched": True, "confidence": 0.99},
    }}
    result = quality_gate_node(state)
    assert result["verification_decision"] != DECISION_VERIFIED


def test_17_all_outputs_missing_cannot_verified():
    state: PipelineSharedState = {"report_id": "r17", "agent_outputs": {}}
    result = quality_gate_node(state)
    assert result["verification_decision"] != DECISION_VERIFIED
    assert result["verification_decision"] == DECISION_PENDING_MANUAL_REVIEW
    assert result["pipeline_status"] == STATUS_COMPLETED


def test_18_malformed_component_result_cannot_verified():
    """A non-dict component output (e.g., string/None) must not become VERIFIED."""
    state: PipelineSharedState = {"report_id": "r18", "agent_outputs": {
        "safety": "not-a-dict",  # malformed  # type: ignore[dict-item]
        "visual_verification": {"supports_report": True, "evidence_confidence": 0.90, "risk_flags": []},
        "geo_validation": {"boundary_matched": True, "confidence": 0.99},
        "issue_intelligence": {"category": "ROADS", "confidence": 0.91},
    }}
    result = quality_gate_node(state)
    assert result["verification_decision"] != DECISION_VERIFIED


# ===========================================================================
# TEST 19 — Actual graph exception produces FAILED, not REJECTED
# ===========================================================================

@pytest.mark.asyncio
async def test_19_graph_exception_produces_failed_not_rejected():
    """Service must return pipeline_status=FAILED when ainvoke raises."""
    from unittest.mock import AsyncMock, patch, MagicMock
    from uuid import UUID as _UUID

    mock_report = MagicMock()
    mock_report.issue_category = MagicMock()
    mock_report.issue_category.value = "roads"
    mock_report.photos = []
    mock_report.title = "test"
    mock_report.description = "test desc"
    mock_report.latitude = 18.55
    mock_report.longitude = 73.80
    mock_report.address = "Pune"
    mock_report.citizen_id = _UUID("00000000-0000-0000-0000-000000000001")

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_report_repo = AsyncMock()
    mock_report_repo.get_by_id = AsyncMock(return_value=mock_report)
    mock_report_repo.update_status = AsyncMock()
    mock_agent_repo = AsyncMock()

    from backend.services.ai_pipeline_service import AIPipelineService
    svc = AIPipelineService(session=mock_session)
    svc.report_repo = mock_report_repo
    svc.agent_repo = mock_agent_repo

    crashing_graph = AsyncMock()
    crashing_graph.ainvoke = AsyncMock(side_effect=RuntimeError("simulated graph failure"))

    with patch("backend.services.ai_pipeline_service._get_pipeline_graph", return_value=crashing_graph):
        result = await svc.process_report(_UUID("00000000-0000-0000-0000-000000000002"))

    assert result["pipeline_status"] == STATUS_FAILED
    assert "verification_decision" not in result
    assert "simulated graph failure" in result.get("error", "")


# ===========================================================================
# TEST 20 — Graph exception does NOT set REJECTED
# ===========================================================================

@pytest.mark.asyncio
async def test_20_graph_exception_does_not_become_rejected():
    """pipeline_status=FAILED must never include verification_decision=REJECTED."""
    from unittest.mock import AsyncMock, patch, MagicMock
    from uuid import UUID as _UUID

    mock_report = MagicMock()
    mock_report.issue_category = MagicMock()
    mock_report.issue_category.value = "roads"
    mock_report.photos = []
    mock_report.citizen_id = _UUID("00000000-0000-0000-0000-000000000001")

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_report_repo = AsyncMock()
    mock_report_repo.get_by_id = AsyncMock(return_value=mock_report)
    mock_report_repo.update_status = AsyncMock()
    mock_agent_repo = AsyncMock()

    from backend.services.ai_pipeline_service import AIPipelineService
    svc = AIPipelineService(session=mock_session)
    svc.report_repo = mock_report_repo
    svc.agent_repo = mock_agent_repo

    crashing_graph = AsyncMock()
    crashing_graph.ainvoke = AsyncMock(side_effect=RuntimeError("crash"))

    with patch("backend.services.ai_pipeline_service._get_pipeline_graph", return_value=crashing_graph):
        result = await svc.process_report(_UUID("00000000-0000-0000-0000-000000000003"))

    assert result.get("verification_decision") != DECISION_REJECTED
    assert result.get("verification_decision") != DECISION_VERIFIED


# ===========================================================================
# TESTS 21-22 — Unknown/empty verification_decision = contract failure
# ===========================================================================

@pytest.mark.asyncio
async def _service_with_fake_graph(fake_state: dict, report_uuid: str | None = None) -> dict:
    from unittest.mock import AsyncMock, patch, MagicMock
    from uuid import UUID as _UUID
    from backend.services.ai_pipeline_service import AIPipelineService
    import uuid as _uuid_mod

    _report_id = _UUID(report_uuid) if report_uuid else _uuid_mod.uuid4()

    mock_report = MagicMock()
    mock_report.issue_category = MagicMock()
    mock_report.issue_category.value = "roads"
    mock_report.photos = []
    mock_report.citizen_id = _UUID("00000000-0000-0000-0000-000000000001")

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_report_repo = AsyncMock()
    mock_report_repo.get_by_id = AsyncMock(return_value=mock_report)
    mock_report_repo.update_status = AsyncMock()
    mock_agent_repo = AsyncMock()

    svc = AIPipelineService(session=mock_session)
    svc.report_repo = mock_report_repo
    svc.agent_repo = mock_agent_repo

    fake_graph = AsyncMock()
    fake_graph.ainvoke = AsyncMock(return_value=fake_state)

    with patch("backend.services.ai_pipeline_service._get_pipeline_graph", return_value=fake_graph):
        return await svc.process_report(_report_id)


@pytest.mark.asyncio
async def test_21_unknown_verification_decision_is_contract_failure():
    fake_state = {"pipeline_status": STATUS_COMPLETED, "verification_decision": "BANANA",
                  "workflow_run_id": "wfr-21", "agent_outputs": {}}
    result = await _service_with_fake_graph(fake_state)
    assert result["pipeline_status"] == STATUS_FAILED
    assert "BANANA" in result.get("error", "")


@pytest.mark.asyncio
async def test_22_empty_verification_decision_is_contract_failure():
    fake_state = {"pipeline_status": STATUS_COMPLETED, "verification_decision": "",
                  "workflow_run_id": "wfr-22", "agent_outputs": {}}
    result = await _service_with_fake_graph(fake_state)
    assert result["pipeline_status"] == STATUS_FAILED


# ===========================================================================
# TEST 23 — Explicit PENDING_MANUAL_REVIEW maps correctly to DB status
# ===========================================================================

def test_23_explicit_pending_manual_review_maps_to_db_status():
    from backend.services.ai_pipeline_service import DECISION_TO_REPORT_STATUS
    from backend.models.reports import ReportStatus
    assert DECISION_TO_REPORT_STATUS[DECISION_PENDING_MANUAL_REVIEW] == ReportStatus.PENDING_MANUAL_REVIEW
    assert DECISION_TO_REPORT_STATUS[DECISION_VERIFIED] == ReportStatus.VERIFIED
    assert DECISION_TO_REPORT_STATUS[DECISION_REJECTED] == ReportStatus.REJECTED
    assert "" not in DECISION_TO_REPORT_STATUS
    assert "BANANA" not in DECISION_TO_REPORT_STATUS


# ===========================================================================
# TESTS 24-26 — Downstream nodes absent from Phase-1 outputs
# ===========================================================================

@pytest.mark.asyncio
async def test_24_enhancer_does_not_execute(mock_engine, base_initial_state):
    graph = create_civic_pipeline_graph(ai_engine=mock_engine)
    final = await graph.ainvoke(base_initial_state)
    assert "enhancement" not in final.get("agent_outputs", {})


@pytest.mark.asyncio
async def test_25_router_does_not_execute(mock_engine, base_initial_state):
    graph = create_civic_pipeline_graph(ai_engine=mock_engine)
    final = await graph.ainvoke(base_initial_state)
    assert "routing" not in final.get("agent_outputs", {})


@pytest.mark.asyncio
async def test_26_notifier_does_not_execute(mock_engine, base_initial_state):
    graph = create_civic_pipeline_graph(ai_engine=mock_engine)
    final = await graph.ainvoke(base_initial_state)
    assert "notification" not in final.get("agent_outputs", {})


# ===========================================================================
# TEST 27-28 — AIPipelineService trusts LangGraph QG, does not duplicate
# ===========================================================================

@pytest.mark.asyncio
async def test_27_service_trusts_graph_verified_decision():
    fake_state = {
        "pipeline_status": STATUS_COMPLETED, "verification_decision": DECISION_VERIFIED,
        "workflow_run_id": "wfr-27",
        "agent_outputs": {"quality_gate": {"verification_decision": DECISION_VERIFIED,
                                            "trust_score": 0.92, "decision_reasons": []}},
    }
    result = await _service_with_fake_graph(fake_state)
    assert result.get("verification_decision") == DECISION_VERIFIED
    assert result.get("pipeline_status") == STATUS_COMPLETED


@pytest.mark.asyncio
async def test_28_service_does_not_run_independent_quality_gate():
    """Service must not independently reject/verify after LangGraph completes."""
    fake_state = {
        "pipeline_status": STATUS_COMPLETED,
        "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
        "workflow_run_id": "wfr-28",
        "agent_outputs": {"quality_gate": {"verification_decision": DECISION_PENDING_MANUAL_REVIEW,
                                            "trust_score": 0.5, "decision_reasons": ["Low confidence"]}},
    }
    result = await _service_with_fake_graph(fake_state)
    # Service must preserve the QG decision, not override it
    assert result.get("verification_decision") == DECISION_PENDING_MANUAL_REVIEW


# ===========================================================================
# TEST 29 — workflow_run_id propagates into service response
# ===========================================================================

@pytest.mark.asyncio
async def test_29_workflow_run_id_propagates_into_service_response():
    fake_state = {
        "pipeline_status": STATUS_COMPLETED, "verification_decision": DECISION_VERIFIED,
        "workflow_run_id": "wfr-propagation-test-29",
        "agent_outputs": {"quality_gate": {"verification_decision": DECISION_VERIFIED,
                                            "trust_score": 0.92, "decision_reasons": []}},
    }
    result = await _service_with_fake_graph(fake_state)
    assert result.get("workflow_run_id") == "wfr-propagation-test-29"


# ===========================================================================
# TEST 30 — Legacy standalone agent tests still pass
# ===========================================================================

@pytest.mark.asyncio
async def test_30a_geo_validator_standalone_still_works():
    from backend.agents.geo_validator import GeoValidationAgent
    agent = GeoValidationAgent(db_session_factory=None)
    output = await agent.process({"report_id": "bc-geo", "raw_payload": {"latitude": 18.55, "longitude": 73.80}})
    geo = output["agent_outputs"]["geo_validation"]
    assert geo["analysis_status"] == "PARTIAL"
    assert geo["ward_name"] == "Aundh-Baner"
    assert geo["boundary_matched"] is None  # Bounding box is dev approximation, not authoritative PostGIS match


def test_30b_classifier_fallback_standalone_still_works():
    from backend.agents.classifier import ClassificationAgent
    agent = ClassificationAgent()
    result = agent._rule_fallback("Deep pothole on main road")
    assert result["category"] in ["ROADS", "TRAFF"]
    assert result["fallback_used"] is True


def test_30c_state_reducer_backward_compat():
    merged = merge_agent_outputs({"forensics": {"trust_score": 100}},
                                  {"classification": {"category": "ROADS"}})
    assert "forensics" in merged and "classification" in merged


# ===========================================================================
# Additional — EXIF signals are None (unknown) not fabricated bools
# ===========================================================================

@pytest.mark.asyncio
async def test_exif_signals_are_none_not_fabricated(mock_engine, base_initial_state):
    """Visual adapter must not fabricate EXIF signals from non-EXIF legacy fields."""
    graph = create_civic_pipeline_graph(ai_engine=mock_engine)
    final = await graph.ainvoke(base_initial_state)
    vis = final["agent_outputs"].get("visual_verification", {})
    signals = vis.get("signals", {})
    assert signals.get("exif_present") is None
    assert signals.get("exif_gps_present") is None
    assert signals.get("gps_consistent") is None


# ===========================================================================
# Additional — prerequisite validator helper unit test
# ===========================================================================

def test_validate_prerequisites_all_present():
    state = _full_state()
    missing = _validate_prerequisites(state)
    assert missing == []


def test_validate_prerequisites_detects_each_missing_key():
    for key in REQUIRED_VERIFICATION_OUTPUTS:
        outputs = {k: {"x": 1} for k in REQUIRED_VERIFICATION_OUTPUTS if k != key}
        state: PipelineSharedState = {"agent_outputs": outputs}
        missing = _validate_prerequisites(state)
        assert any(key.replace("_", " ") in m.lower() or key in m for m in missing)
