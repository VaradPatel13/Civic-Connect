"""Department Router Agent for CivicConnect.

Routes reports to specific PMC municipal departments (ROADS, WATER, DRAIN, etc.),
assigning SLA targets and priority resolution scores based on category and urgency.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.agents.state import PipelineSharedState, RoutingResult
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine

logger = logging.getLogger(__name__)


# PMC SLA mapping dictionary (hours)
PMC_SLA_MAP = {
    "critical": 4,
    "high": 24,
    "medium": 72,
    "low": 168,
}

# Category to Department Code mapping
PMC_DEPT_CODES = {
    "ROADS": ("PMC_DEPT_ROADS", "Roads & Infrastructure Department"),
    "WATER": ("PMC_DEPT_WATER", "Water Supply Department"),
    "DRAIN": ("PMC_DEPT_DRAIN", "Drainage & Sewerage Department"),
    "ELEC": ("PMC_DEPT_ELEC", "Electrical & Streetlighting Department"),
    "HEALTH": ("PMC_DEPT_HEALTH", "Public Health Department"),
    "SANIT": ("PMC_DEPT_SANIT", "Solid Waste Management Department"),
    "FIRE": ("PMC_DEPT_FIRE", "Fire Brigade & Disaster Management"),
    "BUILD": ("PMC_DEPT_BUILD", "Building & Encroachment Department"),
    "TRAFF": ("PMC_DEPT_TRAFF", "Traffic Planning & Management"),
    "PARKS": ("PMC_DEPT_PARKS", "Parks & Garden Department"),
    "ADMIN": ("PMC_DEPT_ADMIN", "PMC General Administration"),
}


class RouterAgent:
    """Agent that routes reports to primary PMC departments and sets SLA targets."""

    def __init__(self, ai_engine: BaseAIEngine | UnifiedAIEngine | Any | None = None) -> None:
        self.ai_engine: BaseAIEngine | Any | None = ai_engine

    def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Department Router node logic for LangGraph workflow."""
        start_time = time.time()
        agent_outputs = state.get("agent_outputs") or {}
        agent_dict = agent_outputs if isinstance(agent_outputs, dict) else {}
        classification = agent_dict.get("classification") if isinstance(agent_dict, dict) else {}
        classification_dict = classification if isinstance(classification, dict) else {}

        category = str(classification_dict.get("category", "ADMIN")).upper()
        urgency = str(classification_dict.get("urgency", "medium")).lower()

        dept_info = PMC_DEPT_CODES.get(category, PMC_DEPT_CODES["ADMIN"])
        dept_code, dept_name = dept_info

        sla_hours = PMC_SLA_MAP.get(urgency, 72)

        # Calculate priority score (1 to 100)
        priority_base = {"critical": 90, "high": 70, "medium": 40, "low": 20}.get(urgency, 40)
        geo_val = agent_dict.get("geo_validation") if isinstance(agent_dict, dict) else {}
        geo_dict = geo_val if isinstance(geo_val, dict) else {}
        if geo_dict.get("boundary_matched"):
            priority_base += 5

        result: RoutingResult = {
            "department_id": f"dept-{category.lower()}",
            "department_code": dept_code,
            "department_name": dept_name,
            "sla_target_hours": sla_hours,
            "priority_score": min(100, priority_base),
        }

        execution_ms = (time.time() - start_time) * 1000.0
        logger.info(f"[Router] Routed to '{dept_name}' (SLA={sla_hours}h, Priority={result['priority_score']}) in {execution_ms:.2f}ms.")
        return {"agent_outputs": {"routing": result}}
