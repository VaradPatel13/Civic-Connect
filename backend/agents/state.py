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

from typing import Annotated, Any, Dict, List, Optional
try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore


def merge_agent_outputs(
    left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Shallow-merges agent outputs dictionary to prevent parallel race overwrites.
    
    When parallel execution nodes (Forensics, Classifier, Geo-Val, Moderator) return
    state updates simultaneously in LangGraph, this reducer merges dictionary keys
    without destroying existing keys written by faster concurrent nodes.
    """
    merged: Dict[str, Any] = dict(left) if left else {}
    if right:
        merged.update(right)
    return merged


class ForensicsResult(TypedDict, total=False):
    authentic: bool
    confidence: float
    reason: str
    duplicate_detected: bool
    matching_report_id: Optional[str]


class ClassificationResult(TypedDict, total=False):
    category: str
    urgency: str  # low, medium, high, critical
    tags: List[str]
    confidence: float
    fallback_used: bool


class GeoValidationResult(TypedDict, total=False):
    ward_id: Optional[str]
    ward_name: Optional[str]
    zone_name: Optional[str]
    boundary_matched: bool
    confidence: float


class ModerationResult(TypedDict, total=False):
    clean: bool
    flags: List[str]
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
    supervisor: Optional[Dict[str, Any]]
    forensics: Optional[ForensicsResult]
    classification: Optional[ClassificationResult]
    geo_validation: Optional[GeoValidationResult]
    moderation: Optional[ModerationResult]
    enhancement: Optional[EnhancementResult]
    routing: Optional[RoutingResult]
    notification: Optional[Dict[str, Any]]


class PipelineSharedState(TypedDict, total=False):
    report_id: str
    trace_id: str
    citizen_id: str
    raw_payload: Dict[str, Any]
    sanitised_text: str
    pii_mask_map: Dict[str, str]
    agent_outputs: Annotated[Dict[str, Any], merge_agent_outputs]
    pipeline_status: str  # PENDING, PROCESSING, COMPLETED, INTERRUPTED, FAILED
    error: Optional[str]
    metadata: Dict[str, Any]
