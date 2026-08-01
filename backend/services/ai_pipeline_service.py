"""Phase-1 AI Pipeline Service for CivicConnect.

Responsibilities:
  - Invoke the Phase-1 LangGraph Report Verification Engine.
  - Persist verification results to the database.
  - Translate verification_decision → ReportStatus DB enum.
  - Record audit information to agent_executions.
  - Handle infrastructure failures (pipeline_status = FAILED).

IMPORTANT — Quality Gate authority:
  The Trust / Quality Gate now executes INSIDE LangGraph and is the
  ONLY component authorized to set verification_decision.
  AIPipelineService does NOT perform a second Quality Gate evaluation
  after graph.ainvoke(). It reads verification_decision from the final
  graph state and maps it to a ReportStatus.

Audit gap (workflow_run_id):
  The agent_executions table currently stores workflow_id (str).
  Phase-1 introduces workflow_run_id as a formal identifier. For now
  workflow_run_id is passed as workflow_id to the existing audit repo.
  A schema migration to rename/formalize this column is deferred to
  the Phase-1G full audit implementation pass.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

import contextlib
import logging
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.pipeline import (
    DECISION_PENDING_MANUAL_REVIEW,
    DECISION_REJECTED,
    DECISION_VERIFIED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    create_civic_pipeline_graph,
)
from backend.agents.state import get_agent_output
from backend.core.config import settings
from backend.models.agent_executions import AgentStatus
from backend.models.reports import ReportStatus
from backend.repositories.agent_executions import AgentExecutionRepository
from backend.repositories.reports import ReportRepository

logger = logging.getLogger(__name__)

# ── verification_decision → ReportStatus mapping ─────────────────────────────
# Phase-1 verification_decision values map to existing ReportStatus DB enum
# values without requiring a schema migration.
# IMPORTANT: unknown/empty decisions are NOT in this mapping and must be treated
# as graph contract violations, NOT silently mapped to PENDING_MANUAL_REVIEW.
DECISION_TO_REPORT_STATUS: dict[str, ReportStatus] = {
    DECISION_VERIFIED: ReportStatus.VERIFIED,
    DECISION_REJECTED: ReportStatus.REJECTED,
    DECISION_PENDING_MANUAL_REVIEW: ReportStatus.PENDING_MANUAL_REVIEW,
}

# Module-level compiled pipeline graph singleton — compiled once at import time
# and reused across all requests to avoid per-request graph compilation overhead.
_PIPELINE_GRAPH: Any = None


def _get_pipeline_graph() -> Any:
    """Returns the cached compiled Phase-1 LangGraph pipeline, compiling on first call."""
    global _PIPELINE_GRAPH
    if _PIPELINE_GRAPH is None:
        logger.info("[AIPipelineService] Compiling Phase-1 LangGraph pipeline (first call).")
        _PIPELINE_GRAPH = create_civic_pipeline_graph()
    return _PIPELINE_GRAPH


class AIPipelineService:
    """Phase-1 AI Pipeline Orchestration Service.

    Invokes the Phase-1 Report Verification Engine (Supervisor, Safety & Abuse,
    Visual Evidence Verification, Geo Verification, Issue Intelligence, Trust /
    Quality Gate) and persists immutable audit logs.

    Does NOT independently make a second verification decision after LangGraph.
    LangGraph's Trust / Quality Gate is the sole source of truth for
    verification_decision.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_repo = ReportRepository(session)
        self.agent_repo = AgentExecutionRepository(session)

    async def _handle_pipeline_failure(
        self,
        report_id: UUID,
        workflow_run_id: str,
        reason: str,
        error: Exception | str,
    ) -> dict[str, Any]:
        """Centralized failure handler for system/contract failures.

        Used for:
          1. LangGraph execution exceptions (graph crashed)
          2. Graph contract violations (unknown/empty verification_decision)

        Pipeline failures are NOT business decisions (REJECTED). They are
        infrastructure failures. The report is reverted to PENDING for retry.
        """
        error_str = str(error)
        logger.error(
            f"[AIPipelineService] Pipeline failure | report={report_id} "
            f"workflow_run_id={workflow_run_id} reason={reason}: {error_str}"
        )
        with contextlib.suppress(Exception):
            err_exec = await self.agent_repo.start_execution(
                report_id=report_id,
                workflow_id=workflow_run_id,
                agent_name="phase1_orchestrator",
                model_used=settings.ai_model or settings.ai_provider,
                input_snapshot={"report_id": str(report_id), "reason": reason},
            )
            await self.agent_repo.complete_execution(
                execution_id=err_exec.id,
                status=AgentStatus.FAILED,
                error_snapshot={"error": error_str, "reason": reason},
            )
        # Revert to PENDING so the report is not stuck in PROCESSING
        await self.report_repo.update_status(
            report_id,
            ReportStatus.PENDING,
            changed_by="ai_orchestrator",
            reason=f"{reason} — reverted for retry",
        )
        return {
            "pipeline_status": STATUS_FAILED,
            "report_id": str(report_id),
            "error": error_str,
        }

    async def process_report(self, report_id: UUID) -> dict[str, Any]:
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            logger.error(f"[AIPipelineService] Report {report_id} not found.")
            return {"error": "Report not found"}

        category_str = (
            report.issue_category.value
            if hasattr(report.issue_category, "value")
            else str(report.issue_category)
        )
        logger.info(
            f"[AIPipelineService] Starting Phase-1 verification for report={report_id} "
            f"category={category_str}"
        )

        # 1. Update report status to PROCESSING
        await self.report_repo.update_status(
            report_id, ReportStatus.PROCESSING, changed_by="ai_orchestrator"
        )

        # 2. Collect photo URLs (original report evidence — not mutated)
        photo_urls: list[str] = []
        if report.photos:
            for p in report.photos:
                url_str = getattr(p, "cloudinary_url", None) or getattr(p, "secure_url", None)
                if url_str:
                    photo_urls.append(str(url_str))
        logger.info(f"[AIPipelineService] Photos: {len(photo_urls)}")

        # 3. Build initial state for LangGraph
        initial_state: dict[str, Any] = {
            "report_id": str(report_id),
            "trace_id": str(uuid.uuid4()),   # Distributed request trace ID
            "citizen_id": str(report.citizen_id),
            "raw_payload": {
                "title": report.title,
                "description": report.description,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "address": report.address,
                "category": category_str,
                "media_urls": photo_urls,
            },
            "agent_outputs": {},
        }

        # 4. Invoke Phase-1 LangGraph graph
        pipeline_graph = _get_pipeline_graph()
        trace_id = initial_state["trace_id"]
        final_state: dict[str, Any] = {}
        try:
            final_state = await pipeline_graph.ainvoke(initial_state)
        except Exception as exc:
            logger.error(
                f"[AIPipelineService] LangGraph execution failed for report={report_id}: {exc}",
                exc_info=True,
            )
            # System failure → pipeline_status = FAILED (NOT verification_decision = REJECTED)
            return await self._handle_pipeline_failure(
                report_id=report_id,
                workflow_run_id=trace_id,
                reason="Phase-1 LangGraph execution failed",
                error=exc,
            )

        # 5. Read results from LangGraph state (Quality Gate is sole source of truth)
        pipeline_status = final_state.get("pipeline_status", "")
        verification_decision = final_state.get("verification_decision", "")
        workflow_run_id = final_state.get("workflow_run_id", trace_id)
        agent_outputs = final_state.get("agent_outputs", {})

        logger.info(
            f"[AIPipelineService] Phase-1 complete | report={report_id} "
            f"pipeline_status={pipeline_status} verification_decision={verification_decision} "
            f"workflow_run_id={workflow_run_id}"
        )

        # 6. Strict contract validation
        # pipeline_status != COMPLETED means graph did not complete normally.
        if pipeline_status != STATUS_COMPLETED:
            return await self._handle_pipeline_failure(
                report_id=report_id,
                workflow_run_id=workflow_run_id,
                reason=f"Graph returned non-COMPLETED pipeline_status: {pipeline_status!r}",
                error=f"pipeline_status={pipeline_status!r}",
            )

        # verification_decision must be one of the three valid Phase-1 decisions.
        # Empty or unknown decisions are graph contract violations, NOT business decisions.
        # PENDING_MANUAL_REVIEW means the Quality Gate EXPLICITLY chose it — not a fallback.
        if verification_decision not in DECISION_TO_REPORT_STATUS:
            return await self._handle_pipeline_failure(
                report_id=report_id,
                workflow_run_id=workflow_run_id,
                reason=f"Graph contract violation: unexpected verification_decision={verification_decision!r}",
                error=f"verification_decision={verification_decision!r} not in VALID_DECISIONS",
            )

        # 7. Map verification_decision → ReportStatus and persist
        target_status = DECISION_TO_REPORT_STATUS[verification_decision]
        # 8. Persist quality gate decision
        quality_gate_out = agent_outputs.get("quality_gate") or {}
        decision_reasons = quality_gate_out.get("decision_reasons", [])
        trust_score = quality_gate_out.get("trust_score")

        await self.report_repo.update_status(
            report_id,
            target_status,
            changed_by="quality_gate",
            reason=" | ".join(decision_reasons) if decision_reasons else verification_decision,
        )

        # 7. Persist AI fields on the report model (written once after processing)
        safety_out = get_agent_output(final_state, "safety")
        visual_out = get_agent_output(final_state, "visual_verification")
        geo_out = get_agent_output(final_state, "geo_validation")
        issue_out = get_agent_output(final_state, "issue_intelligence")
        # Legacy fields for DB columns that exist today
        forensics_out = agent_outputs.get("forensics") or {}

        report.classification_confidence = float(issue_out.get("confidence", 0.0))
        report.moderation_result = dict(safety_out) if safety_out else None
        report.forensics_result = dict(forensics_out) if forensics_out else None
        report.ward = geo_out.get("ward_name")
        report.zone = geo_out.get("zone_name")
        report.ai_tags = issue_out.get("tags") or []

        if forensics_out.get("duplicate_detected"):
            report.is_duplicate = True
            if forensics_out.get("matching_report_id"):
                with contextlib.suppress(ValueError):
                    report.duplicate_of_id = UUID(str(forensics_out["matching_report_id"]))

        self.session.add(report)
        await self.session.commit()

        # 8. Record Phase-1 audit execution (workflow_run_id passed as workflow_id for now)
        # NOTE: audit schema gap — workflow_run_id stored in workflow_id column.
        # Phase-1G will formalize this with a dedicated workflow_run_id column.
        with contextlib.suppress(Exception):
            audit_exec = await self.agent_repo.start_execution(
                report_id=report_id,
                workflow_id=workflow_run_id,
                agent_name="phase1_quality_gate",
                model_used="deterministic_policy_engine",
                input_snapshot={
                    "class_confidence": issue_out.get("confidence"),
                    "geo_matched": geo_out.get("boundary_matched"),
                    "safety_clean": safety_out.get("clean"),
                    "visual_supports": visual_out.get("supports_report"),
                },
            )
            await self.agent_repo.complete_execution(
                execution_id=audit_exec.id,
                status=AgentStatus.COMPLETED,
                confidence=float(trust_score) if trust_score is not None else None,
                output_snapshot={
                    "verification_decision": verification_decision,
                    "decision_reasons": decision_reasons,
                    "trust_score": trust_score,
                },
            )

        logger.info(
            f"[AIPipelineService] Phase-1 audit recorded | report={report_id} "
            f"decision={verification_decision} workflow_run_id={workflow_run_id}"
        )

        return {
            "pipeline_status": pipeline_status,
            "verification_decision": verification_decision,
            "report_id": str(report_id),
            "workflow_run_id": workflow_run_id,
            "trust_score": trust_score,
        }


async def run_ai_pipeline_background(report_id: UUID) -> None:
    """Asynchronous background worker runner with isolated AsyncSession management."""
    from backend.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            service = AIPipelineService(session)
            await service.process_report(report_id)
        except Exception as exc:
            logger.error(
                f"[run_ai_pipeline_background] Worker failed for report={report_id}: {exc}",
                exc_info=True,
            )
