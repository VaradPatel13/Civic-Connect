"""LangGraph Multi-Agent Pipeline Orchestration for CivicConnect.

Coordinates all 9 specialized agents using static parallel super-step fan-out,
isolated sub-state reducers, and specialized per-agent LLM model bindings (e.g., NVIDIA NIM).

Specs: docs/specs/ai-pipeline.md, docs/plans/ai_pipeline_engine_proposal.md
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.classifier import ClassificationAgent
from backend.agents.enhancer import EnhancementAgent
from backend.agents.forensics import ForensicsAgent
from backend.agents.geo_validator import GeoValidationAgent
from backend.agents.moderator import ModerationAgent
from backend.agents.notifier import NotificationAgent
from backend.agents.router import RouterAgent
from backend.agents.state import PipelineSharedState
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine
from backend.core.config import settings

logger = logging.getLogger(__name__)


# ── Supervisor Node ─────────────────────────────────────────────────────────
def supervisor_node(state: PipelineSharedState) -> dict[str, Any]:
    """Validation Supervisor node: initializes trace, sanitizes text, formats payload."""
    report_id = state.get("report_id") or str(uuid.uuid4())
    trace_id = state.get("trace_id") or str(uuid.uuid4())
    raw_payload = state.get("raw_payload", {})

    raw_text_val = raw_payload.get("description") or state.get("raw_text") or ""
    sanitised_text: str = str(raw_text_val).strip()

    logger.info(f"[SupervisorNode] Initializing pipeline run for report {report_id} (trace_id={trace_id}).")

    return {
        "report_id": report_id,
        "trace_id": trace_id,
        "sanitised_text": sanitised_text,
        "pipeline_status": "PROCESSING",
        "agent_outputs": {
            "supervisor": {
                "status": "VALIDATED",
                "timestamp": time.time(),
            }
        },
    }


# ── Agent Node Wrapper Instances ───────────────────────────────────────────
def create_civic_pipeline_graph(
    ai_engine: BaseAIEngine | UnifiedAIEngine | Any | None = None,
    db_session_factory: Any | None = None,
) -> Any:
    """Compiles the LangGraph StateGraph workflow with per-agent specialized model bindings."""

    provider = settings.ai_provider.lower()

    forensics_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_forensics or settings.ai_model or None,
    )
    classifier_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_classifier or settings.ai_model or None,
    )
    moderator_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_moderator or settings.ai_model or None,
    )
    enhancer_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_enhancer or settings.ai_model or None,
    )
    router_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(
        provider=provider,
        model=settings.nim_model_router or settings.ai_model or None,
    )

    # Instantiate agents with their respective specialized models
    forensics_agent = ForensicsAgent(ai_engine=forensics_engine)
    classifier_agent = ClassificationAgent(ai_engine=classifier_engine)
    geo_agent = GeoValidationAgent(db_session_factory=db_session_factory)
    moderator_agent = ModerationAgent(ai_engine=moderator_engine)
    enhancer_agent = EnhancementAgent(ai_engine=enhancer_engine)
    router_agent = RouterAgent(ai_engine=router_engine)
    notifier_agent = NotificationAgent()

    # Define StateGraph
    workflow: Any = StateGraph(PipelineSharedState)  # type: ignore

    # 1. Add Supervisor Node
    workflow.add_node("supervisor", supervisor_node)

    # 2. Add Parallel Execution Nodes (Layer 1 Super-step)
    workflow.add_node("forensics", forensics_agent.process)
    workflow.add_node("classifier", classifier_agent.process)
    workflow.add_node("geo_validator", geo_agent.process)
    workflow.add_node("moderator", moderator_agent.process)

    # 3. Add Downstream Sequential Nodes (Layer 2 & Layer 3)
    workflow.add_node("enhancer", enhancer_agent.process)
    workflow.add_node("router", router_agent.process)
    workflow.add_node("notifier", notifier_agent.process)

    # ── Define Edge Dependencies ───────────────────────────────────────────
    workflow.add_edge(START, "supervisor")

    # Supervisor -> Fan-out in parallel
    workflow.add_edge("supervisor", "forensics")
    workflow.add_edge("supervisor", "classifier")
    workflow.add_edge("supervisor", "geo_validator")
    workflow.add_edge("supervisor", "moderator")

    # Fan-in from parallel nodes -> enhancer
    workflow.add_edge("forensics", "enhancer")
    workflow.add_edge("classifier", "enhancer")
    workflow.add_edge("geo_validator", "enhancer")
    workflow.add_edge("moderator", "enhancer")

    # Downstream execution flow
    workflow.add_edge("enhancer", "router")
    workflow.add_edge("router", "notifier")
    workflow.add_edge("notifier", END)

    # Compile executable graph
    app = workflow.compile()
    logger.info(f"[PipelineGraph] LangGraph workflow compiled using provider '{provider}' with per-agent specialized model bindings.")
    return app
