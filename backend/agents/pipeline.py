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
from datetime import UTC, datetime
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.audit_tracer import create_node_trace_metadata
from backend.agents.classifier import ClassificationAgent
from backend.agents.forensics import ForensicsAgent
from backend.agents.geo_validator import GeoValidationAgent
from backend.agents.moderator import ModerationAgent
from backend.agents.quality_gate import evaluate_quality_gate
from backend.agents.state import PipelineSharedState, get_agent_output
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine
from backend.core.config import settings
from backend.core.pii_masker import mask_pii

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
    start_mono = time.monotonic()
    started_at_utc = datetime.now(UTC)

    report_id = state.get("report_id") or str(uuid.uuid4())
    trace_id = state.get("trace_id") or str(uuid.uuid4())

    # IDEMPOTENT: preserve existing workflow_run_id under resumed/retried execution.
    workflow_run_id = state.get("workflow_run_id") or str(uuid.uuid4())

    raw_payload = state.get("raw_payload", {})

    # Prepare AI-safe text representation (original raw_payload is never mutated)
    raw_text_val = raw_payload.get("description") or state.get("sanitised_text") or ""
    sanitised_text, _ = mask_pii(str(raw_text_val).strip())

    end_mono = time.monotonic()
    ended_at_utc = datetime.now(UTC)

    trace = create_node_trace_metadata(
        node_name="supervisor",
        workflow_run_id=workflow_run_id,
        report_id=report_id,
        start_mono=start_mono,
        end_mono=end_mono,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        output_dict={"status": "INITIALIZED", "analysis_status": "SUCCESS"},
        provider="INTERNAL",
        model="supervisor_orchestrator",
    )

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
                "trace": trace,
            }
        },
    }


# ── Safety & Abuse Verification Adapter ─────────────────────────────────────
def make_safety_node(agent: ModerationAgent) -> Any:
    """Returns a Safety & Abuse Verification node wrapping ModerationAgent."""
    async def safety_node(state: PipelineSharedState) -> dict[str, Any]:
        start_mono = time.monotonic()
        started_at_utc = datetime.now(UTC)
        workflow_run_id = state.get("workflow_run_id", "unknown")
        report_id = state.get("report_id", "unknown")
        agent_err: Exception | None = None

        try:
            result = await agent.process(state)
            moderation_out = (result.get("agent_outputs") or {}).get("moderation") or {}
            if not moderation_out:
                raise ValueError("ModerationAgent returned empty output")
        except Exception as err:
            end_mono = time.monotonic()
            ended_at_utc = datetime.now(UTC)
            agent_err = err
            logger.error(f"[SafetyNode] Agent failed: {err}. Returning missing-output marker.")
            trace = create_node_trace_metadata(
                node_name="safety",
                workflow_run_id=workflow_run_id,
                report_id=report_id,
                start_mono=start_mono,
                end_mono=end_mono,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                output_dict={"analysis_status": "UNAVAILABLE"},
                provider="NVIDIA_NIM",
                model=settings.nim_model_moderator or settings.ai_model or "llama-3.1-70b-instruct",
                error=agent_err,
            )
            return {
                "agent_outputs": {
                    "moderation": {"trace": trace},
                }
            }

        end_mono = time.monotonic()
        ended_at_utc = datetime.now(UTC)

        safety_out = (result.get("agent_outputs") or {}).get("safety") or {
            "clean": moderation_out.get("clean"),
            "flags": moderation_out.get("flags", []),
            "toxicity_score": moderation_out.get("toxicity_score"),
            "confidence": moderation_out.get("confidence"),
            "injection_detected": "prompt_injection" in moderation_out.get("flags", []),
            "analysis_status": moderation_out.get("analysis_status", "SUCCESS"),
        }

        trace = create_node_trace_metadata(
            node_name="safety",
            workflow_run_id=workflow_run_id,
            report_id=report_id,
            start_mono=start_mono,
            end_mono=end_mono,
            started_at_utc=started_at_utc,
            ended_at_utc=ended_at_utc,
            output_dict=safety_out,
            provider="NVIDIA_NIM",
            model=settings.nim_model_moderator or settings.ai_model or "llama-3.1-70b-instruct",
        )
        safety_out["trace"] = trace
        moderation_out["trace"] = trace

        return {
            "agent_outputs": {
                "moderation": moderation_out,
                "safety": safety_out,
            }
        }
    return safety_node


# ── Visual Evidence Verification Adapter ────────────────────────────────────
def make_visual_verification_node(agent: ForensicsAgent) -> Any:
    """Returns a Visual Evidence Verification node wrapping ForensicsAgent."""
    async def visual_verification_node(state: PipelineSharedState) -> dict[str, Any]:
        start_mono = time.monotonic()
        started_at_utc = datetime.now(UTC)
        workflow_run_id = state.get("workflow_run_id", "unknown")
        report_id = state.get("report_id", "unknown")
        agent_err: Exception | None = None

        try:
            result = await agent.process(state)
            agent_outs = result.get("agent_outputs") or {}
            visual_verification_out = agent_outs.get("visual_verification")
            forensics_out = agent_outs.get("forensics") or {}

            if not visual_verification_out and not forensics_out:
                raise ValueError("ForensicsAgent returned empty output")
        except Exception as err:
            end_mono = time.monotonic()
            ended_at_utc = datetime.now(UTC)
            agent_err = err
            logger.error(f"[VisualNode] Agent failed: {err}. Returning missing-output marker.")
            trace = create_node_trace_metadata(
                node_name="visual_verification",
                workflow_run_id=workflow_run_id,
                report_id=report_id,
                start_mono=start_mono,
                end_mono=end_mono,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                output_dict={"analysis_status": "UNAVAILABLE"},
                provider="NVIDIA_NIM",
                model=settings.nim_model_forensics or settings.ai_model or "neva-22b",
                error=agent_err,
            )
            return {
                "agent_outputs": {
                    "forensics": {"trace": trace},
                }
            }

        end_mono = time.monotonic()
        ended_at_utc = datetime.now(UTC)

        if not visual_verification_out:
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
                "supports_report": forensics_out.get("supports_report"),
                "evidence_confidence": (
                    float(forensics_out["confidence"])
                    if "confidence" in forensics_out
                    else None
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

        trace = create_node_trace_metadata(
            node_name="visual_verification",
            workflow_run_id=workflow_run_id,
            report_id=report_id,
            start_mono=start_mono,
            end_mono=end_mono,
            started_at_utc=started_at_utc,
            ended_at_utc=ended_at_utc,
            output_dict=visual_verification_out,
            provider="NVIDIA_NIM",
            model=settings.nim_model_forensics or settings.ai_model or "neva-22b",
        )
        visual_verification_out["trace"] = trace
        forensics_out["trace"] = trace

        return {
            "agent_outputs": {
                "forensics": forensics_out,
                "visual_verification": visual_verification_out,
            }
        }
    return visual_verification_node


# ── Geo Verification Adapter ─────────────────────────────────────────────────
def make_geo_node(agent: GeoValidationAgent) -> Any:
    """Returns a Geo Verification node wrapping GeoValidationAgent."""
    async def geo_node(state: PipelineSharedState) -> dict[str, Any]:
        start_mono = time.monotonic()
        started_at_utc = datetime.now(UTC)
        workflow_run_id = state.get("workflow_run_id", "unknown")
        report_id = state.get("report_id", "unknown")

        try:
            res = await agent.process(state)
            end_mono = time.monotonic()
            ended_at_utc = datetime.now(UTC)
            geo_out = (res.get("agent_outputs") or {}).get("geo_validation") or {}
            trace = create_node_trace_metadata(
                node_name="geo_validator",
                workflow_run_id=workflow_run_id,
                report_id=report_id,
                start_mono=start_mono,
                end_mono=end_mono,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                output_dict=geo_out,
                provider="POSTGIS / DETERMINISTIC",
                model="postgis_spatial_engine",
            )
            if geo_out:
                geo_out["trace"] = trace
            return res
        except Exception as err:
            end_mono = time.monotonic()
            ended_at_utc = datetime.now(UTC)
            logger.error(f"[GeoNode] Agent failed: {err}. Returning missing-output marker.")
            trace = create_node_trace_metadata(
                node_name="geo_validator",
                workflow_run_id=workflow_run_id,
                report_id=report_id,
                start_mono=start_mono,
                end_mono=end_mono,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                output_dict={"analysis_status": "UNAVAILABLE"},
                provider="POSTGIS / DETERMINISTIC",
                model="postgis_spatial_engine",
                error=err,
            )
            return {"agent_outputs": {"geo_validation": {"trace": trace}}}
    return geo_node


# ── Issue Intelligence Adapter ────────────────────────────────────────────────
def make_issue_intelligence_node(agent: ClassificationAgent) -> Any:
    """Returns an Issue Intelligence node executing ClassificationAgent."""
    async def issue_intelligence_node(state: PipelineSharedState) -> dict[str, Any]:
        start_mono = time.monotonic()
        started_at_utc = datetime.now(UTC)
        workflow_run_id = state.get("workflow_run_id", "unknown")
        report_id = state.get("report_id", "unknown")

        try:
            res = await agent.process(state)
            end_mono = time.monotonic()
            ended_at_utc = datetime.now(UTC)
            issue_out = (res.get("agent_outputs") or {}).get("issue_intelligence") or {}
            trace = create_node_trace_metadata(
                node_name="issue_intelligence",
                workflow_run_id=workflow_run_id,
                report_id=report_id,
                start_mono=start_mono,
                end_mono=end_mono,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                output_dict=issue_out,
                provider="NVIDIA_NIM",
                model=settings.nim_model_classifier or settings.ai_model or "llama-3.1-70b-instruct",
            )
            if issue_out:
                issue_out["trace"] = trace
            return res
        except Exception as err:
            end_mono = time.monotonic()
            ended_at_utc = datetime.now(UTC)
            logger.error(f"[IssueNode] Agent failed: {err}. Returning missing-output marker.")
            trace = create_node_trace_metadata(
                node_name="issue_intelligence",
                workflow_run_id=workflow_run_id,
                report_id=report_id,
                start_mono=start_mono,
                end_mono=end_mono,
                started_at_utc=started_at_utc,
                ended_at_utc=ended_at_utc,
                output_dict={"analysis_status": "UNAVAILABLE"},
                provider="NVIDIA_NIM",
                model=settings.nim_model_classifier or settings.ai_model or "llama-3.1-70b-instruct",
                error=err,
            )
            return {
                "agent_outputs": {
                    "classification": {},
                    "issue_intelligence": {"trace": trace},
                }
            }
    return issue_intelligence_node


# ── Quality Gate Prerequisite Validation ────────────────────────────────────
def _validate_prerequisites(state: PipelineSharedState) -> list[str]:
    """Validates presence of all required verification outputs."""
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
    """
    start_mono = time.monotonic()
    started_at_utc = datetime.now(UTC)

    report_id = state.get("report_id", "unknown")
    workflow_run_id = state.get("workflow_run_id", "unknown")
    agent_outputs = state.get("agent_outputs", {})

    qg_result = evaluate_quality_gate(agent_outputs, report_id=report_id)
    decision = qg_result["verification_decision"]

    end_mono = time.monotonic()
    ended_at_utc = datetime.now(UTC)

    trace = create_node_trace_metadata(
        node_name="quality_gate",
        workflow_run_id=workflow_run_id,
        report_id=report_id,
        start_mono=start_mono,
        end_mono=end_mono,
        started_at_utc=started_at_utc,
        ended_at_utc=ended_at_utc,
        output_dict=qg_result,
        provider="DETERMINISTIC_POLICY",
        model="quality_gate_policy_engine",
    )
    qg_result["trace"] = trace

    return {
        "verification_decision": decision,
        "pipeline_status": STATUS_COMPLETED,
        "agent_outputs": {
            "quality_gate": qg_result,
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
