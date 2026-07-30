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

    async def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Notifier node logic for LangGraph workflow. Sets pipeline_status=COMPLETED (AI-09)."""
        from backend.agents.state import get_agent_output
        start_time = time.time()
        report_id = str(state.get("report_id") or "UNKNOWN")
        class_dict = get_agent_output(state, "classification")
        routing_dict = get_agent_output(state, "routing")
        geo_dict = get_agent_output(state, "geo_validation")

        category = str(class_dict.get("category", "General"))
        ward_name = str(geo_dict.get("ward_name", "PMC Ward"))
        dept_name = str(routing_dict.get("department_name", "PMC Department"))
        sla_hours = routing_dict.get("sla_target_hours", 72)

        # Formulate citizen push notification title & body
        notification_payload = {
            "title": f"Report #{report_id[:8]} Received",
            "body": f"Your {category} report in {ward_name} has been assigned to {dept_name}. Estimated SLA: {sla_hours} hours.",
            "points_awarded": 15,  # Decorative only — actual points awarded by ReportService
            "status": "DISPATCHED",
        }

        execution_ms = (time.time() - start_time) * 1000.0
        logger.info(f"[Notifier] Created citizen notification in {execution_ms:.2f}ms.")

        return {
            "pipeline_status": "COMPLETED",
            "agent_outputs": {"notification": notification_payload},
        }


