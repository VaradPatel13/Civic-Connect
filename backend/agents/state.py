"""Shared state definition and merge reducers for CivicConnect LangGraph multi-agent pipeline.

This module defines the typed shared state and isolation boundaries for all 9 agents:
1. Validation Supervisor
2. Image Forensics
3. Issue Classifier
4. Geo-Validator
5. Content Moderator
6. Report Enhancer
7. Department Router
8. Notifier
9. Audit Recorder
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

    When parallel execution nodes (Forensics, Classifier, Geo-Val, Moderator) return
    state updates simultaneously in LangGraph, this reducer merges dictionary keys
    without destroying existing keys written by faster concurrent nodes.
    """
    merged: dict[str, Any] = dict(left) if left else {}
    if right:
        merged.update(right)
    return merged


def get_agent_output(state: PipelineSharedState, agent_key: str) -> dict[str, Any]:
    """Safely retrieve an agent's output dictionary from shared pipeline state (CQ-03).

    Eliminates repetitive defensive type-checking boilerplate across all downstream agents.
    """
    outputs = state.get("agent_outputs") or {}
    result = outputs.get(agent_key)
    return result if isinstance(result, dict) else {}


# Canonical mapping from PMC classifier codes → IssueCategory DB enum values (CQ-02)
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


class ForensicsResult(TypedDict, total=False):
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
    category: str
    urgency: str  # low, medium, high, critical
    tags: list[str]
    confidence: float
    fallback_used: bool


class GeoValidationResult(TypedDict, total=False):
    ward_id: str | None
    ward_name: str | None
    zone_name: str | None
    boundary_matched: bool
    confidence: float


class ModerationResult(TypedDict, total=False):
    clean: bool
    flags: list[str]
    toxicity_score: float
    confidence: float
    requires_human_review: bool


class EnhancementResult(TypedDict, total=False):
    ai_summary: str
    translated_text_en: str
    dept_notes: str


class RoutingResult(TypedDict, total=False):
    department_id: str
    department_code: str
    department_name: str
    sla_target_hours: int
    priority_score: int  # 1 to 100


class AgentOutputs(TypedDict, total=False):
    supervisor: dict[str, Any] | None
    forensics: ForensicsResult | None
    classification: ClassificationResult | None
    geo_validation: GeoValidationResult | None
    moderation: ModerationResult | None
    enhancement: EnhancementResult | None
    routing: RoutingResult | None
    notification: dict[str, Any] | None


class PipelineSharedState(TypedDict, total=False):
    report_id: str
    trace_id: str
    citizen_id: str
    raw_payload: dict[str, Any]
    sanitised_text: str
    pii_mask_map: dict[str, str]
    agent_outputs: Annotated[dict[str, Any], merge_agent_outputs]
    pipeline_status: str  # PENDING, PROCESSING, COMPLETED, INTERRUPTED, FAILED
    error: str | None
    metadata: dict[str, Any]

