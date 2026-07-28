"""Classification Agent for CivicConnect.

Classifies civic issue category, urgency level, and tags using UnifiedAIEngine
with Presidio placeholder prompt guards, strict taxonomy validation, and precompiled scoring-based regex fallbacks.

Specs: docs/specs/ai-pipeline.md, docs/specs/departments.md, docs/specs/AGENT.md
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.agents.state import ClassificationResult, PipelineSharedState
from backend.core.ai_engine import BaseAIEngine, UnifiedAIEngine

logger = logging.getLogger(__name__)

# Canonical PMC department categories (Single Source of Truth)
PMC_CATEGORIES: set[str] = {
    "ROADS",
    "WATER",
    "DRAIN",
    "ELEC",
    "HEALTH",
    "SANIT",
    "FIRE",
    "BUILD",
    "TRAFF",
    "PARKS",
    "ADMIN",
}

VALID_URGENCIES: set[str] = {"low", "medium", "high", "critical"}


class ClassifierPydanticOutput(BaseModel):
    category: str = Field(description="PMC department category code: ROADS, WATER, DRAIN, ELEC, HEALTH, SANIT, FIRE, BUILD, TRAFF, PARKS, ADMIN")
    urgency: str = Field(description="Urgency level: low, medium, high, critical")
    tags: list[str] = Field(default_factory=list, description="Keywords summarizing the issue")
    confidence: float = Field(description="Model confidence score between 0.0 and 1.0")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cat = v.strip().upper()
        if cat not in PMC_CATEGORIES:
            raise ValueError(f"Invalid category '{cat}'. Allowed categories: {sorted(PMC_CATEGORIES)}")
        return cat

    @field_validator("urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        urg = v.strip().lower()
        if urg not in VALID_URGENCIES:
            raise ValueError(f"Invalid urgency '{urg}'. Allowed urgencies: {sorted(VALID_URGENCIES)}")
        return urg

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags_to_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            items = [v]
        elif isinstance(v, list):
            items = v
        else:
            return []

        cleaned: list[str] = []
        for item in items:
            if isinstance(item, str):
                s = item.strip().lower()
                if s and not s.isdigit() and s not in cleaned:
                    cleaned.append(s)
        return cleaned


# Single Source of Truth keyword mappings for PMC category scoring fallback
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "ROADS": [
        "pothole", "potholes", "road", "roads", "asphalt", "tar", "street", "footpath",
        "sidewalk", "divider", "median", "speed breaker", "road crack", "road damage",
        "bridge", "flyover", "culvert", "vandalism", "broken bench", "broken sign",
        "damaged property", "public property", "signboard", "hoarding", "banner", "billboard"
    ],
    "WATER": [
        "water", "leak", "leaking", "pipeline", "pipe", "burst", "water supply", "tanker",
        "tap", "drinking water", "water shortage", "low pressure", "water quality",
        "contaminated water", "water bill", "water pollution", "contamination", "dirty water"
    ],
    "DRAIN": [
        "drain", "gutter", "sewer", "manhole", "overflow", "blocked drain", "clogged",
        "flooding", "stagnant water", "storm drain", "stormwater", "stp", "sewage treatment",
        "effluent", "wastewater", "heavy rain", "rainwater", "waterlogging", "flood", "monsoon"
    ],
    "ELEC": [
        "electric", "electricity", "street light", "streetlight", "lamp", "lamp post",
        "light pole", "illumination", "wire", "cable", "pole", "transformer", "spark",
        "power", "blackout", "voltage", "outage", "fuse", "internet", "wifi", "fiber",
        "telecom", "network", "mobile tower"
    ],
    "HEALTH": [
        "mosquito", "dengue", "malaria", "fever", "disease", "clinic", "hospital", "health",
        "sanitary", "infection", "medical", "vaccination", "stray", "dog", "cat", "cow",
        "buffalo", "pig", "monkey", "animal", "snake", "wildlife", "dead animal", "carcass",
        "cemetery", "graveyard", "crematorium", "toilet", "washroom", "restroom", "urinal",
        "public toilet", "air pollution", "smoke", "emission", "noise", "loudspeaker", "horn"
    ],
    "SANIT": [
        "garbage", "waste", "trash", "dump", "dumping", "smell", "odor", "litter",
        "cleaning", "bin", "dustbin", "solid waste", "unclean", "sweeping"
    ],
    "FIRE": [
        "fire", "short circuit", "smoke", "explosion", "hazard", "flammable", "gas leak",
        "emergency", "earthquake", "cyclone", "storm", "landslide", "disaster", "relief"
    ],
    "BUILD": [
        "illegal building", "building", "construction", "encroachment", "unauthorized",
        "structure", "demolition", "collapse", "vendor", "hawker", "street vendor",
        "cart", "stall", "housing", "apartment", "society", "residential", "flat"
    ],
    "TRAFF": [
        "traffic", "signal", "jam", "parking", "vehicle", "accident", "congestion",
        "wrong parking", "traffic light", "speeding", "bus", "metro", "train", "auto",
        "rickshaw", "transport", "bus stop", "station", "cctv", "camera", "surveillance"
    ],
    "PARKS": [
        "park", "tree", "garden", "branch", "bench", "playground", "grass", "lawn",
        "pruning", "greenery", "stadium", "sports", "ground", "gym", "court"
    ],
    "ADMIN": [
        "office", "municipal office", "staff", "employee", "official", "corruption",
        "bribe", "delay", "tax", "property tax", "bill payment", "assessment", "license",
        "permit", "certificate", "birth certificate", "death certificate", "trade license",
        "market", "bazaar", "school", "college", "education", "complaint", "grievance",
        "issue", "problem", "help"
    ],
}


def _compile_keywords(keywords: list[str]) -> re.Pattern[str]:
    """Compiles list of keywords into single word-boundary regex pattern, sorted by length descending."""
    sorted_kw = sorted(keywords, key=len, reverse=True)
    pattern = r"\b(" + "|".join(re.escape(k) for k in sorted_kw) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


# Precompiled category regex patterns
COMPILED_CATEGORY_PATTERNS: dict[str, re.Pattern[str]] = {
    category: _compile_keywords(keywords)
    for category, keywords in CATEGORY_KEYWORDS.items()
}

# Word boundary regex pattern for high/critical urgency keyword detection
HIGH_CRITICAL_URGENCY_PATTERN: re.Pattern[str] = re.compile(
    r"\b(danger|urgent|hazard|emergency|burst|collapse|fire|explosion|gas leak|flooding|outage|accident|severe|short circuit)\b",
    re.IGNORECASE,
)


class ClassificationAgent:
    """Agent that classifies civic issue category and urgency using AI with precompiled regex scoring fallback."""

    def __init__(self, ai_engine: BaseAIEngine | UnifiedAIEngine | Any | None = None) -> None:
        self.ai_engine: BaseAIEngine | Any = ai_engine or UnifiedAIEngine(provider="openrouter")

    def _normalize_text(self, text: str) -> str:
        """Normalizes input text by removing punctuation noise and stripping whitespace."""
        if not text:
            return ""
        lowered = text.lower()
        cleaned = re.sub(r"[^\w\s]", " ", lowered)
        return re.sub(r"\s+", " ", cleaned).strip()

    def process(self, state: PipelineSharedState) -> dict[str, Any]:
        """Executes Issue Classifier node logic for LangGraph workflow."""
        start_time = time.time()
        raw_text_val = state.get("sanitised_text") or state.get("raw_text") or ""
        text_to_classify: str = str(raw_text_val)

        if not text_to_classify.strip():
            logger.warning("[Classifier] Empty text payload, using default ADMIN fallback.")
            fallback = self._rule_fallback(text_to_classify)
            return {"agent_outputs": {"classification": fallback}}

        system_prompt = (
            "You are the PMC Civic Issue Classifier Agent.\n"
            "Identify the civic department category (ROADS, WATER, DRAIN, ELEC, HEALTH, SANIT, FIRE, BUILD, TRAFF, PARKS, ADMIN), "
            "urgency level (low, medium, high, critical), and relevant tags summarizing the issue.\n\n"
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

            category = parsed.category.upper()
            urgency = parsed.urgency.lower()

            if category not in PMC_CATEGORIES or urgency not in VALID_URGENCIES:
                logger.warning(
                    f"[Classifier] AI returned invalid output category='{category}' or urgency='{urgency}'. "
                    "Applying regex fallback."
                )
                fallback = self._rule_fallback(text_to_classify)
                return {"agent_outputs": {"classification": fallback}}

            if parsed.confidence < 0.60:
                logger.info(f"[Classifier] Confidence {parsed.confidence:.2f} < 0.60. Applying regex rule fallback.")
                fallback = self._rule_fallback(text_to_classify)
                return {"agent_outputs": {"classification": fallback}}

            result: ClassificationResult = {
                "category": category,
                "urgency": urgency,
                "tags": parsed.tags,
                "confidence": parsed.confidence,
                "fallback_used": False,
            }

            execution_ms = (time.time() - start_time) * 1000.0
            logger.info(f"[Classifier] Classified as '{result['category']}' ({result['urgency']}) in {execution_ms:.2f}ms via {model_name}.")
            return {"agent_outputs": {"classification": result}}

        except Exception as err:
            logger.error(f"[Classifier] LLM invocation failed ({err}). Applying deterministic regex fallback.")
            fallback = self._rule_fallback(text_to_classify)
            return {"agent_outputs": {"classification": fallback}}

    def _rule_fallback(self, text_input: str) -> ClassificationResult:
        """Deterministic regex keyword classifier fallback using scoring and tag extraction."""
        normalized_text = self._normalize_text(text_input)

        if not normalized_text:
            return {
                "category": "ADMIN",
                "urgency": "medium",
                "tags": ["general-admin"],
                "confidence": 0.50,
                "fallback_used": True,
            }

        matched_keywords_set: set[str] = set()
        category_scores: dict[str, int] = {}

        for category, pattern in COMPILED_CATEGORY_PATTERNS.items():
            if category == "ADMIN":
                continue
            matches = pattern.findall(normalized_text)
            if matches:
                category_scores[category] = len(matches)
                for match in matches:
                    matched_keywords_set.add(match.lower())

        if category_scores:
            # Pick category with highest match count
            best_category = max(category_scores.keys(), key=lambda c: category_scores[c])
            tags = list(matched_keywords_set) if matched_keywords_set else [best_category.lower()]
        else:
            best_category = "ADMIN"
            tags = ["general-admin"]

        is_urgent = bool(HIGH_CRITICAL_URGENCY_PATTERN.search(normalized_text))
        urgency = "high" if is_urgent else "medium"

        return {
            "category": best_category,
            "urgency": urgency,
            "tags": tags,
            "confidence": 0.75 if best_category != "ADMIN" else 0.50,
            "fallback_used": True,
        }
