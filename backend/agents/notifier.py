"""Notification & Citizen Rewards Agent for CivicConnect.

Dispatches citizen alerts, formats SMS/Push notifications, and awards civic engagement points.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import time
from typing import Any

from backend.agents.state import PipelineSharedState

logger = logging.getLogger(__name__)


class NotificationAgent:
    """Agent that formats notifications and manages citizen reward points."""

    def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Notifier node logic for LangGraph workflow."""
        start_time = time.time()
        report_id = str(state.get("report_id") or "UNKNOWN")
        agent_outputs = state.get("agent_outputs") or {}
        agent_dict = agent_outputs if isinstance(agent_outputs, dict) else {}

        classification = agent_dict.get("classification") if isinstance(agent_dict, dict) else {}
        class_dict = classification if isinstance(classification, dict) else {}
        routing = agent_dict.get("routing") if isinstance(agent_dict, dict) else {}
        routing_dict = routing if isinstance(routing, dict) else {}
        geo_val = agent_dict.get("geo_validation") if isinstance(agent_dict, dict) else {}
        geo_dict = geo_val if isinstance(geo_val, dict) else {}

        category = str(class_dict.get("category", "General"))
        ward_name = str(geo_dict.get("ward_name", "PMC Ward"))
        dept_name = str(routing_dict.get("department_name", "PMC Department"))
        sla_hours = routing_dict.get("sla_target_hours", 72)

        # Formulate citizen push notification title & body
        notification_payload = {
            "title": f"Report #{report_id[:8]} Received",
            "body": f"Your {category} report in {ward_name} has been assigned to {dept_name}. Estimated SLA: {sla_hours} hours.",
            "points_awarded": 15,  # Award 15 Civic Points for submitting a valid verified report
            "status": "DISPATCHED",
        }

        execution_ms = (time.time() - start_time) * 1000.0
        logger.info(f"[Notifier] Created citizen notification and awarded 15 points in {execution_ms:.2f}ms.")

        return {"agent_outputs": {"notification": notification_payload}}
