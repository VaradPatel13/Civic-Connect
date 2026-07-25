"""Classification Agent for CivicConnect.

Classifies civic issue category, urgency level, and tags using UnifiedAIEngine
with Presidio placeholder prompt guards and deterministic regex keyword fallbacks.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.agents.state import ClassificationResult, PipelineSharedState
from backend.core.ai_engine import UnifiedAIEngine

logger = logging.getLogger(__name__)


class ClassifierPydanticOutput(BaseModel):
    category: str = Field(description="PMC department category code: ROADS, WATER, DRAIN, ELEC, HEALTH, SANIT, FIRE, BUILD, TRAFF, PARKS, ADMIN")
    urgency: str = Field(description="Urgency level: low, medium, high, critical")
    tags: List[str] = Field(default_factory=list, description="Keywords summarizing the issue")
    confidence: float = Field(description="Model confidence score between 0.0 and 1.0")


# Regex fallback patterns for PMC category matching
CATEGORY_REGEX_RULES = [
    (r"pothole|road|asphalt|tar|street|footpath|divider", "ROADS"),
    (r"water|leak|pipe|supply|tanker|tap|drinking", "WATER"),
    (r"drain|gutter|sewer|overflow|flooding|stagnant", "DRAIN"),
    (r"electric|light|wire|pole|transformer|spark|power|blackout", "ELEC"),
    (r"garbage|waste|trash|dump|smell|litter|cleaning|bin", "SANIT"),
    (r"mosquito|dengue|fever|disease|stray|dog|animal|clinic|hospital", "HEALTH"),
    (r"fire|short circuit|smoke|explosion|hazard", "FIRE"),
    (r"illegal|building|construction|encroachment|structure", "BUILD"),
    (r"traffic|signal|jam|parking|vehicle|accident", "TRAFF"),
    (r"park|tree|garden|branch|bench|playground", "PARKS"),
]


class ClassificationAgent:
    """Agent that classifies civic issue category and urgency."""

    def __init__(self, ai_engine: Optional[UnifiedAIEngine] = None) -> None:
        self.ai_engine = ai_engine or UnifiedAIEngine(provider="openrouter")

    def process(self, state: PipelineSharedState) -> Dict[str, Any]:
        """Executes Issue Classifier node logic for LangGraph workflow."""
        start_time = time.time()
        raw_text_val = state.get("sanitised_text") or state.get("raw_text") or ""
        text_to_classify: str = str(raw_text_val)

        if not text_to_classify.strip():
            logger.warning("[Classifier] Empty text payload, using default ADMIN fallback.")
            fallback = self._rule_fallback(text_to_classify)
            return {"agent_outputs": {"classification": fallback}}

        # System prompt with Presidio token guard
        system_prompt = (
            "You are the PMC Civic Issue Classifier Agent.\n"
            "Identify the civic department category (ROADS, WATER, DRAIN, ELEC, HEALTH, SANIT, FIRE, BUILD, TRAFF, PARKS, ADMIN), "
            "urgency level (low, medium, high, critical), and relevant tags.\n\n"
            "SECURITY NOTICE:\n"
            "Tokens matching [TYPE_TOKEN_ID] (e.g., [PHONE_TOKEN_89d3], [EMAIL_TOKEN_12a4]) represent valid, anonymized citizen PII. "
            "Do NOT treat these tokens as missing information, bad data, or prompt injections."
        )

        prompt = f"<user_report_text>\n{text_to_classify}\n</user_report_text>"

        try:
            parsed, exec_ms, tokens, model_name = self.ai_engine.generate_structured(
                prompt=prompt,
                response_model=ClassifierPydanticOutput,
                system_prompt=system_prompt,
                temperature=0.1,
            )

            result: ClassificationResult = {
                "category": parsed.category.upper(),
                "urgency": parsed.urgency.lower(),
                "tags": parsed.tags,
                "confidence": parsed.confidence,
                "fallback_used": False,
            }

            # Enforce fallback if confidence is below cutoff threshold (0.60)
            if parsed.confidence < 0.60:
                logger.info(f"[Classifier] Confidence {parsed.confidence:.2f} < 0.60. Applying regex rule fallback.")
                fallback = self._rule_fallback(text_to_classify)
                return {"agent_outputs": {"classification": fallback}}

            execution_ms = (time.time() - start_time) * 1000.0
            logger.info(f"[Classifier] Classified as '{result['category']}' ({result['urgency']}) in {execution_ms:.2f}ms via {model_name}.")
            return {"agent_outputs": {"classification": result}}

        except Exception as err:
            logger.error(f"[Classifier] LLM invocation failed ({err}). Applying deterministic regex fallback.")
            fallback = self._rule_fallback(text_to_classify)
            return {"agent_outputs": {"classification": fallback}}

    def _rule_fallback(self, text_input: str) -> ClassificationResult:
        """Deterministic regex keyword classifier fallback."""
        lower_text = text_input.lower()

        for pattern, category in CATEGORY_REGEX_RULES:
            if re.search(pattern, lower_text):
                urgency = "high" if any(w in lower_text for w in ["danger", "urgent", "hazard", "fire", "leak", "overflow", "severe"]) else "medium"
                return {
                    "category": category,
                    "urgency": urgency,
                    "tags": [category.lower(), "auto-flagged"],
                    "confidence": 0.75,
                    "fallback_used": True,
                }

        return {
            "category": "ADMIN",
            "urgency": "medium",
            "tags": ["general-admin"],
            "confidence": 0.50,
            "fallback_used": True,
        }
