"""Notification & Citizen Rewards Agent for CivicConnect.

Dispatches citizen alerts, formats SMS/Push notifications, and awards civic engagement points.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from backend.agents.state import PipelineSharedState

logger = logging.getLogger(__name__)


class NotificationAgent:
    """Agent that formats notifications and manages citizen reward points."""

    def process(self, state: PipelineSharedState) -> Dict[str, Any]:
        """Executes Notifier node logic for LangGraph workflow."""
        start_time = time.time()
        report_id = state.get("report_id", "UNKNOWN")
        agent_outputs = state.get("agent_outputs", {})

        classification = agent_outputs.get("classification", {})
        routing = agent_outputs.get("routing", {})
        geo_val = agent_outputs.get("geo_validation", {})

        category = classification.get("category", "General")
        ward_name = geo_val.get("ward_name", "PMC Ward")
        dept_name = routing.get("department_name", "PMC Department")
        sla_hours = routing.get("sla_target_hours", 72)

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
