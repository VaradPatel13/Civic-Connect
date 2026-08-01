"""Shared state definition and merge reducers for CivicConnect Phase-1 LangGraph pipeline.

This module defines the typed shared state and isolation boundaries for the
Phase-1 Report Verification Engine components:

1. Supervisor / Orchestrator
2. Safety & Abuse Verification  (legacy: ModerationAgent)
3. Visual Evidence Verification (legacy: ForensicsAgent)
4. Geo Verification             (legacy: GeoValidationAgent)
5. Issue Intelligence           (legacy: ClassificationAgent)
6. Trust / Quality Gate

Downstream components (Enhancer, Router, Notifier) are excluded from Phase-1
and reserved for future phases. Their result TypedDicts are preserved here
so their implementation files do not need modification.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""
            
from __future__ import annotations

from typing import Annotated, Any

try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore


def merge_agent_outputs(
    left: dict[str, Any] | None, right: dict[str, Any] | None
) -> dict[str, Any]:
    """Shallow-merges agent outputs dictionary to prevent parallel race overwrites.

    When parallel execution nodes (Safety, Visual, Geo, Issue Intelligence) return
    state updates simultaneously in LangGraph, this reducer merges dictionary keys
    without destroying existing keys written by faster concurrent nodes.

    This is the correct mechanism for Phase-1 fan-out/fan-in safety.
    """
    merged: dict[str, Any] = dict(left) if left else {}
    if right:
        merged.update(right)
    return merged


def get_agent_output(state: PipelineSharedState, agent_key: str) -> dict[str, Any]:
    """Safely retrieve a component's output dictionary from shared pipeline state.

    Eliminates repetitive defensive type-checking boilerplate across all downstream
    components (Quality Gate, AIPipelineService).
    """
    outputs = state.get("agent_outputs") or {}
    result = outputs.get(agent_key)
    return result if isinstance(result, dict) else {}


# Canonical mapping from PMC classifier codes → IssueCategory DB enum values
PMC_TO_ISSUE_CATEGORY: dict[str, str] = {
    "ROADS": "roads",
    "WATER": "water_supply",
    "DRAIN": "drainage",
    "ELEC": "street_lighting",
    "HEALTH": "public_health",
    "SANIT": "waste_management",
    "FIRE": "public_health",       # nearest semantic match
    "BUILD": "encroachment",
    "TRAFF": "traffic_infrastructure",
    "PARKS": "parks",
    "ADMIN": "other",
}


# ---------------------------------------------------------------------------
# Component Result TypedDicts
# ---------------------------------------------------------------------------

class VisualVerificationResult(TypedDict, total=False):
    """Phase-1 Visual Evidence Verification output contract.

    Visual Verification produces evidence SIGNALS. It does NOT claim absolute
    authenticity. The Trust / Quality Gate makes the final trust decision.
    """
    supports_report: bool | None
    evidence_confidence: float | None
    analysis_status: str  # "SUCCESS", "PARTIAL", "UNAVAILABLE"
    signals: dict[str, Any]   # screenshot_suspected, photo_of_screen_suspected, etc.
    risk_flags: list[str]
    details: dict[str, Any]


class SafetyResult(TypedDict, total=False):
    """Phase-1 Safety & Abuse Verification output contract."""
    clean: bool | None
    flags: list[str]
    toxicity_score: float | None
    confidence: float
    injection_detected: bool | None
    signals: dict[str, Any]
    analysis_status: str  # "SUCCESS", "UNAVAILABLE", "PARTIAL"


class GeoValidationResult(TypedDict, total=False):
    """Phase-1 Geo Verification output contract."""
    ward_id: str | None
    ward_name: str | None
    zone_name: str | None
    boundary_matched: bool | None
    confidence: float
    analysis_status: str  # "SUCCESS", "PARTIAL", "UNAVAILABLE"
    coordinates_valid: bool | None
    municipality_matched: bool | None
    near_boundary: bool | None
    signals: dict[str, Any]
    risk_flags: list[str]
    details: dict[str, Any]


class IssueIntelligenceResult(TypedDict, total=False):
    """Phase-1 Issue Intelligence output contract."""
    category: str
    urgency: str  # low, medium, high, critical
    tags: list[str]
    public_safety_risk: bool
    confidence: float
    fallback_used: bool


class QualityGateResult(TypedDict, total=False):
    """Phase-1 Trust / Quality Gate output contract."""
    verification_decision: str   # VERIFIED, REJECTED, PENDING_MANUAL_REVIEW
    trust_score: float
    decision_reasons: list[str]


# ---------------------------------------------------------------------------
# Legacy TypedDicts — preserved so agent implementation files compile unchanged
# ---------------------------------------------------------------------------

class ForensicsResult(TypedDict, total=False):
    """Legacy Visual Verification result — kept for ForensicsAgent compatibility."""
    authentic: bool
    supports_report: bool
    reported_issue_visible: bool
    issue_category_match: bool
    source_type: str
    quality_ok: bool
    ai_generated: bool
    manipulated: bool
    confidence: float
    reason: str
    duplicate_detected: bool
    matching_report_id: str | None
    capture_source: str | None
    signature_valid: bool | None
    location_uncertain: bool | None
    capture_distance_km: float | None
    trust_score: int


class ClassificationResult(TypedDict, total=False):
    """Legacy Issue Intelligence result — kept for ClassificationAgent compatibility."""
    category: str
    urgency: str  # low, medium, high, critical
    tags: list[str]
    confidence: float
    fallback_used: bool


class ModerationResult(TypedDict, total=False):
    """Legacy Safety result — kept for ModerationAgent compatibility."""
    clean: bool
    flags: list[str]
    toxicity_score: float
    confidence: float
    requires_human_review: bool


class EnhancementResult(TypedDict, total=False):
    """Downstream Phase-3 result — excluded from Phase-1 graph."""
    ai_summary: str
    translated_text_en: str
    dept_notes: str


class RoutingResult(TypedDict, total=False):
    """Downstream Phase-3 result — excluded from Phase-1 graph."""
    department_id: str
    department_code: str
    department_name: str
    sla_target_hours: int
    priority_score: int


# ---------------------------------------------------------------------------
# Phase-1 Shared State Contract
# ---------------------------------------------------------------------------

class PipelineSharedState(TypedDict, total=False):
    """Shared workflow state for the Phase-1 Report Verification Engine.

    IMPORTANT DISAMBIGUATION:
      pipeline_status:       Operational graph execution status.
                             Values: PROCESSING, COMPLETED, FAILED
      verification_decision: Final Quality Gate verification outcome.
                             Values: VERIFIED, REJECTED, PENDING_MANUAL_REVIEW

    These are intentionally separate concepts:
      - REJECTED != pipeline failure (a rejected report is a successfully
        completed verification workflow).
      - pipeline_status = COMPLETED + verification_decision = VERIFIED is the
        "happy path" for a verified report.
      - pipeline_status = FAILED means an unexpected system error occurred.

    workflow_run_id hierarchy:
      report_id
        └── workflow_run_id
               ├── safety execution
               ├── visual_verification execution
               ├── geo_validation execution
               ├── issue_intelligence execution
               └── quality_gate execution
    """
    # ── Identifiers ─────────────────────────────────────────────────────────
    report_id: str
    trace_id: str
    workflow_run_id: str          # Generated once per Phase-1 execution in Supervisor
    citizen_id: str

    # ── Report content ───────────────────────────────────────────────────────
    raw_payload: dict[str, Any]   # Original: never mutated after Supervisor reads it
    sanitised_text: str           # AI-safe representation (PII masked)
    pii_mask_map: dict[str, str]  # Redaction mapping for audit use

    # ── Component outputs ────────────────────────────────────────────────────
    agent_outputs: Annotated[dict[str, Any], merge_agent_outputs]
    # Keys used in Phase-1:
    #   "supervisor"           → dict
    #   "safety"               → SafetyResult (via ModerationAgent)
    #   "visual_verification"  → VisualVerificationResult (via ForensicsAgent)
    #   "geo_validation"       → GeoValidationResult (via GeoValidationAgent)
    #   "issue_intelligence"   → IssueIntelligenceResult (via ClassificationAgent)
    #   "quality_gate"         → QualityGateResult

    # ── Operational status ────────────────────────────────────────────────────
    pipeline_status: str          # PROCESSING | COMPLETED | FAILED
    verification_decision: str    # VERIFIED | REJECTED | PENDING_MANUAL_REVIEW

    # ── Error & metadata ──────────────────────────────────────────────────────
    error: str | None
    metadata: dict[str, Any]
