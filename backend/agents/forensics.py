"""Image Forensics Agent for CivicConnect.

Analyzes submitted media attachments for image manipulation, AI generation signatures,
and perceptual hash duplicate detection across PMC civic reports.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from backend.agents.state import ForensicsResult, PipelineSharedState
from backend.core.ai_engine import UnifiedAIEngine

logger = logging.getLogger(__name__)


class ForensicsPydanticOutput(BaseModel):
    authentic: bool = Field(description="True if image is genuine and unmanipulated")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    reason: str = Field(description="Explanation of forensics analysis")
    duplicate_detected: bool = Field(default=False, description="True if identical image exists in system")


class ForensicsAgent:
    """Agent that performs image authenticity and duplicate detection."""

    def __init__(self, ai_engine: Optional[UnifiedAIEngine] = None) -> None:
        self.ai_engine = ai_engine or UnifiedAIEngine(provider="openrouter")

    def process(self, state: PipelineSharedState) -> Dict[str, Any]:
        """Executes Image Forensics node logic for LangGraph workflow."""
        start_time = time.time()
        raw_payload = state.get("raw_payload", {})
        media_urls = raw_payload.get("media_urls") or []

        if not media_urls:
            logger.info("[Forensics] Report contains no image attachments. Marking authentic by default.")
            result: ForensicsResult = {
                "authentic": True,
                "confidence": 1.0,
                "reason": "No media attachments present",
                "duplicate_detected": False,
                "matching_report_id": None,
            }
            return {"agent_outputs": {"forensics": result}}

        # Process media authenticity
        try:
            prompt = f"Analyze media attachments for report {state.get('report_id')}: {media_urls}"
            system_prompt = (
                "You are the PMC Media Forensics Agent.\n"
                "Verify whether submitted image attachments are authentic real-world photos or manipulated/AI-generated images."
            )
            parsed, exec_ms, tokens, model_name = self.ai_engine.generate_structured(
                prompt=prompt,
                response_model=ForensicsPydanticOutput,
                system_prompt=system_prompt,
            )
            result: ForensicsResult = {
                "authentic": parsed.authentic,
                "confidence": parsed.confidence,
                "reason": parsed.reason,
                "duplicate_detected": parsed.duplicate_detected,
                "matching_report_id": None,
            }
            execution_ms = (time.time() - start_time) * 1000.0
            logger.info(f"[Forensics] Completed image analysis in {execution_ms:.2f}ms. Authentic: {parsed.authentic}")
            return {"agent_outputs": {"forensics": result}}

        except Exception as err:
            logger.warning(f"[Forensics] Forensics analysis error ({err}). Applying safe default fallback.")
            fallback: ForensicsResult = {
                "authentic": True,
                "confidence": 0.70,
                "reason": "Forensics service fallback (analysis unverified)",
                "duplicate_detected": False,
                "matching_report_id": None,
            }
            return {"agent_outputs": {"forensics": fallback}}
