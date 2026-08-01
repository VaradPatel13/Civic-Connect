"""Phase-1 Report Verification Engine — LangGraph Pipeline (Phase-1A Hardened).

Implements the Phase-1 CivicConnect LangGraph graph topology:

    START
      |
      v
    SUPERVISOR
      |
      +---+---+---+----+
      |   |   |   |
      v   v   v   v
   SAFETY VISUAL GEO ISSUE
      |   |   |   |
      +---+---+---+----+
              |
              |  (explicit 4-way barrier via add_edge([...], "quality_gate"))
              v
      TRUST / QUALITY GATE
        /        |        \\
       v         v         v
   VERIFIED  REVIEW   REJECTED
       |         |         |
       +---------+---------+
                 |
                 v
                END

Synchronization (JOIN / Fan-In):
  LangGraph 1.2.9 supports an explicit multi-start barrier edge:

    workflow.add_edge(
        ["safety", "visual_verification", "geo_validator", "issue_intelligence"],
        "quality_gate",
    )

  This is the canonical way to express a 4-way synchronization barrier in
  LangGraph 1.x. The Quality Gate is scheduled EXACTLY ONCE, ONLY after ALL
  four branches complete. The four individual edges (one per branch) are NOT
  used — the list form provides the explicit barrier guarantee.

Quality Gate — Fail-Closed Invariant:
  MISSING REQUIRED COMPONENT OUTPUT MUST NEVER RESULT IN VERIFIED.
  The gate validates presence of all four required outputs BEFORE evaluating
  policy thresholds. Missing outputs → PENDING_MANUAL_REVIEW (not VERIFIED).

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.classifier import ClassificationAgent
from backend.agents.forensics import ForensicsAgent
from backend.core.pii_masker import mask_pii
from backend.agents.geo_validator import GeoValidationAgent
from backend.agents.moderator import ModerationAgent
from backend.agents.state import PipelineSharedState, get_agent_output
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine
from backend.core.config import settings

logger = logging.getLogger(__name__)


# ── Phase-1 Decision Vocabulary ─────────────────────────────────────────────
DECISION_VERIFIED = "VERIFIED"
DECISION_REJECTED = "REJECTED"
DECISION_PENDING_MANUAL_REVIEW = "PENDING_MANUAL_REVIEW"

VALID_DECISIONS: frozenset[str] = frozenset(
    {DECISION_VERIFIED, DECISION_REJECTED, DECISION_PENDING_MANUAL_REVIEW}
)

# ── Pipeline Operational Status ─────────────────────────────────────────────
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"

# ── Required Phase-1 Verification Output Keys ────────────────────────────────
REQUIRED_VERIFICATION_OUTPUTS: tuple[str, ...] = (
    "safety",
    "visual_verification",
    "geo_validation",
    "issue_intelligence",
)


# ── Supervisor Node ─────────────────────────────────────────────────────────
def supervisor_node(state: PipelineSharedState) -> dict[str, Any]:
    """Supervisor / Orchestrator node.

    Responsibilities:
    - Validate incoming payload has required fields.
    - Preserve original report evidence in raw_payload (never mutated).
    - Prepare AI-safe text representation (sanitised_text).
    - Generate workflow_run_id ONCE per Phase-1 execution — preserved if already set.
    - Set initial pipeline_status = PROCESSING.

    Idempotency: If state already contains a workflow_run_id (e.g., resumed
    execution), the existing value is preserved rather than regenerated.
    """
    report_id = state.get("report_id") or str(uuid.uuid4())
    trace_id = state.get("trace_id") or str(uuid.uuid4())

    # IDEMPOTENT: preserve existing workflow_run_id under resumed/retried execution.
    workflow_run_id = state.get("workflow_run_id") or str(uuid.uuid4())

    raw_payload = state.get("raw_payload", {})

    # Prepare AI-safe text representation (original raw_payload is never mutated)
    raw_text_val = raw_payload.get("description") or state.get("sanitised_text") or ""
    sanitised_text, _ = mask_pii(str(raw_text_val).strip())

    logger.info(
        f"[Supervisor] Initializing Phase-1 verification for report={report_id} "
        f"trace_id={trace_id} workflow_run_id={workflow_run_id}"
    )

    return {
        "report_id": report_id,
        "trace_id": trace_id,
        "workflow_run_id": workflow_run_id,
        "sanitised_text": sanitised_text,
        "pipeline_status": STATUS_PROCESSING,
        "verification_decision": "",  # Set exclusively by Quality Gate
        "agent_outputs": {
            "supervisor": {
                "status": "INITIALIZED",
                "timestamp": time.time(),
                "report_id": report_id,
                "workflow_run_id": workflow_run_id,
            }
        },
    }


# ── Safety & Abuse Verification Adapter ─────────────────────────────────────
def make_safety_node(agent: ModerationAgent) -> Any:
    """Returns a Safety & Abuse Verification node wrapping the legacy ModerationAgent.

    The legacy ModerationAgent writes to agent_outputs["moderation"].
    This adapter also writes a copy to agent_outputs["safety"] for Phase-1
    compatibility, preserving backward-compatible "moderation" key.

    Fail-safe: if the underlying agent fails, returns a conservative result that
    marks the output as missing so the Quality Gate prerequisite check fires.
    """
    async def safety_node(state: PipelineSharedState) -> dict[str, Any]:
        try:
            result = await agent.process(state)
            moderation_out = (result.get("agent_outputs") or {}).get("moderation") or {}
            if not moderation_out:
                raise ValueError("ModerationAgent returned empty output")
        except Exception as err:
            logger.error(f"[SafetyNode] Agent failed: {err}. Returning missing-output marker.")
            # Return marker dict with sentinel so Quality Gate prerequisite detects missing result.
            return {
                "agent_outputs": {
                    "moderation": {},
                    # "safety" key intentionally omitted so Quality Gate prerequisite fails.
                }
            }

        # Write under both "moderation" (legacy) and "safety" (Phase-1 canonical key)
        safety_out = (result.get("agent_outputs") or {}).get("safety") or {
            "clean": moderation_out.get("clean"),        # None if missing — not defaulted
            "flags": moderation_out.get("flags", []),
            "toxicity_score": moderation_out.get("toxicity_score"),
            "confidence": moderation_out.get("confidence"),
            "injection_detected": "prompt_injection" in moderation_out.get("flags", []),
        }

        return {
            "agent_outputs": {
                "moderation": moderation_out,
                "safety": safety_out,
            }
        }
    return safety_node


# ── Visual Evidence Verification Adapter ────────────────────────────────────
def make_visual_verification_node(agent: ForensicsAgent) -> Any:
    """Returns a Visual Evidence Verification node wrapping the legacy ForensicsAgent.

    The legacy ForensicsAgent writes to agent_outputs["forensics"].
    This adapter also writes a Phase-1 evidence-signal contract under
    agent_outputs["visual_verification"], preserving backward-compatible
    "forensics" key.

    IMPORTANT: Phase-1 Visual Verification does NOT assert "authentic": true.
    It produces evidence signals: supports_report, evidence_confidence,
    signals dict, and risk_flags. The Quality Gate makes the final trust decision.

    EXIF signals (Phase-1A temporary behavior):
    - exif_present, exif_gps_present, gps_consistent are set to None (UNKNOWN)
      because the legacy ForensicsAgent does not provide reliable EXIF data.
    - capture_source != EXIF, capture_distance_km != EXIF GPS.
    - Phase-1C will implement real dual-layer EXIF + VLM signal extraction.
    - None = UNKNOWN / NOT YET ESTABLISHED. Not negative. Not positive.
    - Quality Gate must not reject on unknown EXIF signals.
    """
    async def visual_verification_node(state: PipelineSharedState) -> dict[str, Any]:
        try:
            result = await agent.process(state)
            agent_outs = result.get("agent_outputs") or {}
            visual_verification_out = agent_outs.get("visual_verification")
            forensics_out = agent_outs.get("forensics") or {}

            if not visual_verification_out and not forensics_out:
                raise ValueError("ForensicsAgent returned empty output")
        except Exception as err:
            logger.error(f"[VisualNode] Agent failed: {err}. Returning missing-output marker.")
            return {
                "agent_outputs": {
                    "forensics": {},
                    # "visual_verification" key intentionally omitted.
                }
            }

        if not visual_verification_out:
            # Fallback adapter if legacy agent didn't return visual_verification key
            source_type = forensics_out.get("source_type", "unknown")
            risk_flags: list[str] = []

            if forensics_out.get("ai_generated"):
                risk_flags.append("synthetic_image_suspected")
            if forensics_out.get("manipulated"):
                risk_flags.append("manipulation_suspected")
            if forensics_out.get("duplicate_detected"):
                risk_flags.append("exact_duplicate_found")
            if source_type == "screenshot":
                risk_flags.append("screenshot_suspected")
            if source_type == "photo_of_screen":
                risk_flags.append("photo_of_screen_suspected")

            visual_verification_out = {
                "supports_report": forensics_out.get("supports_report"),  # None if missing
                "evidence_confidence": (
                    float(forensics_out["confidence"])
                    if "confidence" in forensics_out
                    else None           # None = unknown
                ),
                "analysis_status": "SUCCESS",
                "signals": {
                    "screenshot_suspected": source_type == "screenshot",
                    "photo_of_screen_suspected": source_type == "photo_of_screen",
                    "synthetic_image_suspected": bool(forensics_out.get("ai_generated", False)),
                    "manipulation_suspected": bool(forensics_out.get("manipulated", False)),
                    "exif_present": None,
                    "exif_gps_present": None,
                    "gps_consistent": None,
                    "exact_duplicate_found": bool(forensics_out.get("duplicate_detected", False)),
                    "perceptual_duplicate_found": False,
                },
                "risk_flags": risk_flags,
                "details": {},
            }

        return {
            "agent_outputs": {
                "forensics": forensics_out,                        # Legacy key
                "visual_verification": visual_verification_out,    # Phase-1 canonical
            }
        }
    return visual_verification_node


# ── Geo Verification Adapter ─────────────────────────────────────────────────
def make_geo_node(agent: GeoValidationAgent) -> Any:
    """Returns a Geo Verification node wrapping the legacy GeoValidationAgent.

    The legacy agent already writes to agent_outputs["geo_validation"] which
    is the Phase-1 canonical key — no renaming needed.
    """
    async def geo_node(state: PipelineSharedState) -> dict[str, Any]:
        try:
            return await agent.process(state)
        except Exception as err:
            logger.error(f"[GeoNode] Agent failed: {err}. Returning missing-output marker.")
            return {"agent_outputs": {}}  # No "geo_validation" key → prerequisite fails
    return geo_node


# ── Issue Intelligence Adapter ────────────────────────────────────────────────
def make_issue_intelligence_node(agent: ClassificationAgent) -> Any:
    """Returns an Issue Intelligence node wrapping the legacy ClassificationAgent.

    The legacy ClassificationAgent writes to agent_outputs["classification"].
    This adapter also writes a copy to agent_outputs["issue_intelligence"] for
    Phase-1 compatibility, preserving backward-compatible "classification" key.
    """
    async def issue_intelligence_node(state: PipelineSharedState) -> dict[str, Any]:
        try:
            result = await agent.process(state)
            classification_out = (result.get("agent_outputs") or {}).get("classification") or {}
            if not classification_out:
                raise ValueError("ClassificationAgent returned empty output")
        except Exception as err:
            logger.error(f"[IssueNode] Agent failed: {err}. Returning missing-output marker.")
            return {
                "agent_outputs": {
                    "classification": {},
                    # "issue_intelligence" key intentionally omitted.
                }
            }

        issue_intelligence_out = {
            "category": classification_out.get("category", "ADMIN"),
            "urgency": classification_out.get("urgency", "medium"),
            "tags": classification_out.get("tags", []),
            "public_safety_risk": classification_out.get("urgency") in ("critical", "high"),
            "confidence": float(classification_out["confidence"]) if "confidence" in classification_out else None,
            "fallback_used": bool(classification_out.get("fallback_used", False)),
        }
        return {
            "agent_outputs": {
                "classification": classification_out,
                "issue_intelligence": issue_intelligence_out,
            }
        }
    return issue_intelligence_node


# ── Quality Gate Prerequisite Validation ────────────────────────────────────
def _validate_prerequisites(state: PipelineSharedState) -> list[str]:
    """Validates presence of all required verification outputs.

    Returns a list of missing-output reason strings.
    Empty list means all prerequisites are present.

    INVARIANT: missing output must NEVER silently become VERIFIED.
    """
    agent_outputs = state.get("agent_outputs") or {}
    missing: list[str] = []
    for key in REQUIRED_VERIFICATION_OUTPUTS:
        val = agent_outputs.get(key)
        if not val or not isinstance(val, dict):
            missing.append(f"Missing required {key.replace('_', ' ').title()} verification result")
    return missing


# ── Trust / Quality Gate ──────────────────────────────────────────────────────
def quality_gate_node(state: PipelineSharedState) -> dict[str, Any]:
    """Trust / Quality Gate — the ONLY Phase-1 component authorized to set
    verification_decision.

    FAIL-CLOSED INVARIANT:
      1. Validate all four required verification outputs exist.
         If any are missing → PENDING_MANUAL_REVIEW (never VERIFIED).
      2. Apply safety check (explicit REJECTED path for safety failures).
      3. Apply conservative multi-signal evaluation.
         Missing optional fields are treated conservatively (not as positive signals).

    CRITICAL DISTINCTION:
      verification_decision = REJECTED
        != pipeline failure (pipeline_status = FAILED)
      A REJECTED report is a COMPLETED verification workflow.
      pipeline_status = FAILED means a system/infrastructure error occurred.
    """
    report_id = state.get("report_id", "unknown")
    decision_reasons: list[str] = []

    # ── STEP 1: Prerequisite validation (fail-closed) ─────────────────────
    missing = _validate_prerequisites(state)
    if missing:
        for reason in missing:
            decision_reasons.append(reason)
        logger.warning(
            f"[QualityGate] report={report_id} → PENDING_MANUAL_REVIEW "
            f"| Missing prerequisites: {missing}"
        )
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "pipeline_status": STATUS_COMPLETED,
            "agent_outputs": {
                "quality_gate": {
                    "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
                    "trust_score": 0.0,
                    "decision_reasons": decision_reasons,
                }
            },
        }

    # All prerequisites present — read outputs
    safety = get_agent_output(state, "safety")
    visual = get_agent_output(state, "visual_verification")
    geo = get_agent_output(state, "geo_validation")
    issue = get_agent_output(state, "issue_intelligence")

    # ── STEP 2: Safety Check ──────────────────────────────────────────────
    # CRITICAL SECURITY INVARIANT: Failure to run/obtain Safety evidence (clean is None or
    # analysis_status == "UNAVAILABLE") MUST NEVER result in REJECTED.
    # It must route to PENDING_MANUAL_REVIEW.
    analysis_status = safety.get("analysis_status")
    is_safe = safety.get("clean")

    if analysis_status == "UNAVAILABLE" or is_safe is None:
        decision_reasons.append(
            f"Safety analysis unavailable ({safety.get('flags', ['safety_service_failure'])}) — routed to manual review"
        )
        logger.warning(f"[QualityGate] report={report_id} → PENDING_MANUAL_REVIEW | Safety status={analysis_status} clean=None")
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "pipeline_status": STATUS_COMPLETED,
            "agent_outputs": {
                "quality_gate": {
                    "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
                    "trust_score": 0.0,
                    "decision_reasons": decision_reasons,
                }
            },
        }

    # ACTUAL UNSAFE CONTENT (clean is explicitly False)
    if is_safe is False:
        flags = safety.get("flags", [])
        decision_reasons.append(f"Safety violation: {flags}")
        logger.warning(f"[QualityGate] report={report_id} REJECTED — Safety flags: {flags}")
        return {
            "verification_decision": DECISION_REJECTED,
            "pipeline_status": STATUS_COMPLETED,
            "agent_outputs": {
                "quality_gate": {
                    "verification_decision": DECISION_REJECTED,
                    "trust_score": 0.0,
                    "decision_reasons": decision_reasons,
                }
            },
        }

    # ── STEP 3: Conservative Multi-Signal Evaluation ──────────────────────
    # Missing fields are NOT treated as positive evidence (fail-closed).
    # None values trigger review rather than passing through as optimistic defaults.
    class_conf_raw = issue.get("confidence")
    geo_matched = geo.get("boundary_matched")
    visual_supports = visual.get("supports_report")
    evidence_confidence_raw = visual.get("evidence_confidence")
    risk_flags = visual.get("risk_flags", [])

    # Convert None → sentinel that triggers review
    class_conf: float = class_conf_raw if isinstance(class_conf_raw, (int, float)) else -1.0
    evidence_confidence: float = evidence_confidence_raw if isinstance(evidence_confidence_raw, (int, float)) else -1.0

    logger.info(
        f"[QualityGate] report={report_id} | "
        f"class_conf={class_conf_raw} geo_matched={geo_matched} "
        f"visual_supports={visual_supports} evidence_conf={evidence_confidence_raw} "
        f"risk_flags={risk_flags}"
    )

    needs_review = (
        class_conf < 0.60                               # includes None sentinel (-1.0)
        or geo_matched is not True                       # None or False → review
        or visual_supports is not True                   # None or False → review
        or evidence_confidence < 0.5                     # includes None sentinel (-1.0)
        or len(risk_flags) >= 2
    )

    if needs_review:
        if class_conf < 0.60:
            reason = (
                "Issue Intelligence confidence unknown"
                if class_conf_raw is None
                else f"Low classification confidence: {class_conf:.2f}"
            )
            decision_reasons.append(reason)
        if geo_matched is not True:
            decision_reasons.append(
                "Geo boundary not confirmed"
                if geo_matched is None
                else "Report coordinates outside PMC jurisdiction"
            )
        if visual_supports is not True:
            decision_reasons.append(
                "Visual support unknown"
                if visual_supports is None
                else "Visual evidence does not support report"
            )
        if evidence_confidence < 0.5:
            decision_reasons.append(
                "Evidence confidence unknown"
                if evidence_confidence_raw is None
                else f"Low evidence confidence: {evidence_confidence:.2f}"
            )
        if len(risk_flags) >= 2:
            decision_reasons.append(f"Multiple visual risk signals: {risk_flags}")

        logger.warning(
            f"[QualityGate] report={report_id} → PENDING_MANUAL_REVIEW | {decision_reasons}"
        )
        safe_conf = max(class_conf, 0.0) if class_conf >= 0 else 0.0
        safe_ev = max(evidence_confidence, 0.0) if evidence_confidence >= 0 else 0.0
        return {
            "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
            "pipeline_status": STATUS_COMPLETED,
            "agent_outputs": {
                "quality_gate": {
                    "verification_decision": DECISION_PENDING_MANUAL_REVIEW,
                    "trust_score": round(safe_conf * safe_ev, 3),
                    "decision_reasons": decision_reasons,
                }
            },
        }

    # ── VERIFIED ─────────────────────────────────────────────────────────────
    trust_score = round(
        (class_conf * 0.4 + evidence_confidence * 0.4 + 0.2),
        3,
    )
    decision_reasons.append("All verification signals pass policy thresholds")
    logger.info(f"[QualityGate] report={report_id} → VERIFIED | trust_score={trust_score}")
    return {
        "verification_decision": DECISION_VERIFIED,
        "pipeline_status": STATUS_COMPLETED,
        "agent_outputs": {
            "quality_gate": {
                "verification_decision": DECISION_VERIFIED,
                "trust_score": trust_score,
                "decision_reasons": decision_reasons,
            }
        },
    }


# ── Conditional Router ────────────────────────────────────────────────────────
def route_after_quality_gate(state: PipelineSharedState) -> str:
    """Conditional edge function: routes to END based on verification_decision.

    All three outcomes route to END — Phase-1 ends here.
    Unknown/missing decisions also route to END (pipeline_status is already COMPLETED;
    the service layer validates this further and handles contract violations).
    """
    decision = state.get("verification_decision", "")
    if decision == DECISION_VERIFIED:
        return "verified"
    elif decision == DECISION_REJECTED:
        return "rejected"
    else:
        return "pending_review"


# ── Graph Factory ─────────────────────────────────────────────────────────────
def create_civic_pipeline_graph(
    ai_engine: BaseAIEngine | UnifiedAIEngine | Any | None = None,
    db_session_factory: Any | None = None,
) -> Any:
    """Compiles the Phase-1 Report Verification Engine LangGraph.

    Synchronization (LangGraph 1.2.9):
      The explicit multi-start barrier form is used:

        workflow.add_edge(
            ["safety", "visual_verification", "geo_validator", "issue_intelligence"],
            "quality_gate",
        )

      This guarantees quality_gate runs EXACTLY ONCE and ONLY after ALL four
      parallel branches have completed. Verified via LangGraph 1.2.9 API:
        add_edge signature: (self, start_key: str | list[str], end_key: str) -> Self

    Excluded from Phase-1 (reserved for future phases):
      - EnhancementAgent (Phase-3)
      - RouterAgent (Phase-3)
      - NotificationAgent (Phase-3)
    """
    provider = settings.ai_provider.lower()

    safety_engine: Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_moderator or settings.ai_model or None,
    )
    visual_engine: Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_forensics or settings.ai_model or None,
    )
    issue_engine: Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_classifier or settings.ai_model or None,
    )

    safety_agent = ModerationAgent(ai_engine=safety_engine)
    visual_agent = ForensicsAgent(ai_engine=visual_engine)
    geo_agent = GeoValidationAgent(db_session_factory=db_session_factory)
    issue_agent = ClassificationAgent(ai_engine=issue_engine)

    workflow: Any = StateGraph(PipelineSharedState)  # type: ignore

    # ── Phase-1 Nodes ──────────────────────────────────────────────────────
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("safety", make_safety_node(safety_agent))
    workflow.add_node("visual_verification", make_visual_verification_node(visual_agent))
    workflow.add_node("geo_validator", make_geo_node(geo_agent))
    workflow.add_node("issue_intelligence", make_issue_intelligence_node(issue_agent))
    workflow.add_node("quality_gate", quality_gate_node)

    # ── START → Supervisor ────────────────────────────────────────────────
    workflow.add_edge(START, "supervisor")

    # ── Supervisor → Parallel Fan-Out ──────────────────────────────────────
    workflow.add_edge("supervisor", "safety")
    workflow.add_edge("supervisor", "visual_verification")
    workflow.add_edge("supervisor", "geo_validator")
    workflow.add_edge("supervisor", "issue_intelligence")

    # ── EXPLICIT 4-WAY BARRIER → Quality Gate ─────────────────────────────
    # LangGraph 1.2.9 multi-start form: quality_gate runs exactly once,
    # only after ALL four branches have completed.
    workflow.add_edge(
        ["safety", "visual_verification", "geo_validator", "issue_intelligence"],
        "quality_gate",
    )

    # ── Conditional Routing: Quality Gate → END ───────────────────────────
    workflow.add_conditional_edges(
        "quality_gate",
        route_after_quality_gate,
        {
            "verified": END,
            "rejected": END,
            "pending_review": END,
        },
    )

    app = workflow.compile()
    logger.info(
        f"[PipelineGraph] Phase-1A Hardened Report Verification Engine compiled | "
        f"provider='{provider}' | fan-in: 4-way explicit barrier → quality_gate"
    )
    return app
