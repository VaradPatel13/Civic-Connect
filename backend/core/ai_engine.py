"""Universal Provider AI Engine with NVIDIA NIM, OpenRouter, and OpenAI Support.

Handles structured LLM outputs, Pydantic model validation, zero-token json_repair,
and exponential backoff retries across OpenAI, OpenRouter, NVIDIA NIM, and Anthropic providers.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings

try:
    import json_repair  # type: ignore
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseAIEngine:
    """Abstract Base Class for AI Engine Providers."""

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> tuple[T, float, int, str]:
        """Generates structured Pydantic response.

        Returns:
            (parsed_model, execution_ms, total_tokens, model_name_used)
        """
        raise NotImplementedError


class UnifiedAIEngine(BaseAIEngine):
    """Multi-provider AI Engine supporting NVIDIA NIM, OpenRouter, and OpenAI APIs."""

    def __init__(
        self,
        provider: Optional[str] = None,  # "openrouter", "nvidia_nim", "openai"
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.provider = (provider or settings.ai_provider).lower()
        self.api_key = api_key or self._resolve_api_key()
        self.base_url = base_url or self._resolve_base_url()
        self.model_name = model or self._resolve_default_model()

        if OpenAI is not None and self.api_key:
            self.client: Any = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            logger.warning(f"OpenAI SDK or API Key missing for provider '{self.provider}'. Client uninitialized.")

    def _resolve_api_key(self) -> str:
        if self.provider == "nvidia_nim":
            return (
                os.getenv("NVIDIA_API_KEY")
                or os.getenv("NVIDIA_NIM_API_KEY")
                or settings.nvidia_api_key
                or ""
            )
        elif self.provider == "openrouter":
            return os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key or ""
        return os.getenv("OPENAI_API_KEY") or settings.openai_api_key or ""

    def _resolve_base_url(self) -> str:
        if self.provider == "nvidia_nim":
            return "https://integrate.api.nvidia.com/v1"
        elif self.provider == "openrouter":
            return "https://openrouter.ai/api/v1"
        return "https://api.openai.com/v1"

    def _resolve_default_model(self) -> str:
        if self.provider == "nvidia_nim":
            return "meta/llama-3.1-70b-instruct"
        elif self.provider == "openrouter":
            return "anthropic/claude-3.5-sonnet"
        return "gpt-4o-mini"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        reraise=True,
    )
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> tuple[T, float, int, str]:
        start_time = time.time()

        client = self.client
        if client is None:
            raise RuntimeError(f"AI Engine client for provider '{self.provider}' is not configured.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Append schema requirements to force JSON output
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        json_instruction = (
            f"\n\nReturn ONLY a valid JSON object strictly matching this schema:\n{schema_json}"
        )
        messages[-1]["content"] += json_instruction

        extra_headers: Dict[str, str] = {}
        if self.provider == "openrouter":
            extra_headers["HTTP-Referer"] = "https://civicconnect.org"
            extra_headers["X-Title"] = "CivicConnect AI Engine"

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        # Attempt API call with response_format, fallback without response_format if provider rejects it
        try:
            response = client.chat.completions.create(
                response_format={"type": "json_object"}, **kwargs
            )
        except Exception as api_err:
            logger.warning(f"[AIEngine] response_format not supported by provider ({api_err}), trying without json_object mode.")
            response = client.chat.completions.create(**kwargs)

        raw_content = response.choices[0].message.content or "{}"
        total_tokens = response.usage.total_tokens if response.usage else 0
        execution_ms = (time.time() - start_time) * 1000.0

        # Fast zero-token JSON parse & repair
        parsed_dict = self._parse_json_robust(raw_content)
        parsed_model = response_model.model_validate(parsed_dict)

        return parsed_model, execution_ms, total_tokens, self.model_name

    def _parse_json_robust(self, raw_text: str) -> Dict[str, Any]:
        """Attempts standard json.loads(), falling back to zero-token json_repair."""
        clean_text = raw_text.strip()

        # Handle markdown ```json codeblock wrapping
        if clean_text.startswith("```"):
            lines = clean_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_text = "\n".join(lines).strip()

        try:
            return json.loads(clean_text)  # type: ignore
        except json.JSONDecodeError as err:
            logger.warning(f"[AIEngine] Standard JSON decode failed ({err}). Attempting zero-token json_repair.")
            if HAS_JSON_REPAIR:
                try:
                    repaired = json_repair.repair_json(clean_text, return_objects=True)
                    if isinstance(repaired, dict):
                        return repaired
                except Exception as repair_err:
                    logger.error(f"[AIEngine] json_repair failed: {repair_err}")
            raise ValueError(f"Could not parse valid JSON from AI model response: {clean_text[:200]}")
