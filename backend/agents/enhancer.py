"""Report Enhancer Agent for CivicConnect.

Generates concise executive summaries, Marathi-to-English translations, and administrative
action notes for PMC municipal officers.

Specs: docs/specs/ai-pipeline.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from backend.agents.state import EnhancementResult, PipelineSharedState
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine

logger = logging.getLogger(__name__)


class EnhancerPydanticOutput(BaseModel):
    ai_summary: str = Field(description="Concise 1-2 sentence executive summary for officers")
    translated_text_en: str = Field(description="English translation of Marathi/Hindi report text")
    dept_notes: str = Field(description="Actionable administrative recommendations for PMC field workers")


class EnhancementAgent:
    """Agent that translates and generates executive summaries for PMC municipal staff."""

    def __init__(self, ai_engine: BaseAIEngine | UnifiedAIEngine | Any | None = None) -> None:
        self.ai_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(provider="openrouter")

    async def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Report Enhancer node logic for LangGraph workflow."""
        from backend.agents.state import get_agent_output
        start_time = time.time()
        text_content: str = str(state.get("sanitised_text") or state.get("raw_text") or "")
        classification_dict = get_agent_output(state, "classification")

        category: str = str(classification_dict.get("category", "ADMIN"))
        urgency: str = str(classification_dict.get("urgency", "medium"))

        system_prompt = (
            "You are the PMC Report Enhancer Agent.\n"
            "Translate Marathi/Hindi civic reports to clear English, write a 1-sentence executive summary, "
            "and suggest actionable field repair steps for municipal teams."
        )

        prompt = (
            f"Category: {category}\nUrgency: {urgency}\nReport Text:\n{text_content}"
        )

        try:
            parsed, exec_ms, tokens, model_name = await self.ai_engine.generate_structured(
                prompt=prompt,
                response_model=EnhancerPydanticOutput,
                system_prompt=system_prompt,
                temperature=0.2,
            )

            result: EnhancementResult = {
                "ai_summary": parsed.ai_summary,
                "translated_text_en": parsed.translated_text_en,
                "dept_notes": parsed.dept_notes,
            }

            execution_ms = (time.time() - start_time) * 1000.0
            logger.info(f"[Enhancer] Report enhanced in {execution_ms:.2f}ms via {model_name}.")
            return {"agent_outputs": {"enhancement": result}}

        except Exception as err:
            logger.warning(f"[Enhancer] Enhancement LLM failed ({err}). Using fallback translation/summary.")
            fallback: EnhancementResult = {
                "ai_summary": f"{category} issue reported with {urgency} urgency.",
                "translated_text_en": text_content,
                "dept_notes": "Inspect reported location and assess field repair requirements.",
            }
            return {"agent_outputs": {"enhancement": fallback}}

