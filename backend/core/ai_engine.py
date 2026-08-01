"""Universal Provider AI Engine with NVIDIA NIM, OpenRouter, and OpenAI Support.

Handles structured LLM outputs, Pydantic model validation, zero-token json_repair,
and exponential backoff retries across OpenAI, OpenRouter, NVIDIA NIM, and Anthropic providers.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, TypeVar

from pydantic import BaseModel
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from backend.core.circuit_breaker import (
    CircuitBreaker,
    nim_circuit_breaker,
    openrouter_circuit_breaker,
)
from backend.core.config import settings
from backend.core.rate_limiter import RedisTokenBucketLimiter

try:
    import json_repair  # type: ignore
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False

try:
    from openai import AsyncOpenAI, OpenAI
    from openai import (
        AuthenticationError as OpenAIAuthError,
    )
    from openai import (
        BadRequestError as OpenAIBadRequestError,
    )
    from openai import (
        PermissionDeniedError as OpenAIPermissionError,
    )
except ImportError:
    OpenAI = None  # type: ignore
    AsyncOpenAI = None  # type: ignore
    OpenAIAuthError = Exception  # type: ignore
    OpenAIBadRequestError = Exception  # type: ignore
    OpenAIPermissionError = Exception  # type: ignore

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)



class BaseAIEngine:
    """Abstract Base Class for AI Engine Providers."""

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.2,
        image_urls: list[str] | None = None,
    ) -> tuple[T, float, int, str]:
        """Generates structured Pydantic response (async).

        Returns:
            (parsed_model, execution_ms, total_tokens, model_name_used)
        """
        raise NotImplementedError


class UnifiedAIEngine(BaseAIEngine):
    """Multi-provider AI Engine supporting NVIDIA NIM, OpenRouter, and OpenAI APIs."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = (provider or settings.ai_provider).lower()
        self.api_key = api_key or self._resolve_api_key()
        self.base_url = base_url or self._resolve_base_url()
        self.model_name = model or self._resolve_default_model()

        self.rate_limiter = RedisTokenBucketLimiter()
        self.circuit_breaker = self._resolve_circuit_breaker()

        # Use AsyncOpenAI to avoid blocking the event loop (A-01)
        if AsyncOpenAI is not None and self.api_key:
            self.client: Any = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            logger.warning(f"AsyncOpenAI SDK or API Key missing for provider '{self.provider}'. Client uninitialized.")

    def _resolve_circuit_breaker(self) -> CircuitBreaker:
        if self.provider == "nvidia_nim":
            return nim_circuit_breaker
        elif self.provider == "openrouter":
            return openrouter_circuit_breaker
        return CircuitBreaker(name=self.provider, failure_threshold=5, recovery_timeout_seconds=30.0)

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
        retry=retry_if_not_exception_type((
            RuntimeError,
            ValueError,
            OpenAIAuthError,
            OpenAIPermissionError,
            OpenAIBadRequestError,
        )),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=6),
        reraise=True,
    )
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.2,
        image_urls: list[str] | None = None,
    ) -> tuple[T, float, int, str]:
        start_time = time.time()

        if not self.circuit_breaker.allow_execution():
            raise RuntimeError(
                f"Circuit breaker '{self.circuit_breaker.name}' is OPEN due to high failure rate. Fast-failing LLM request."
            )

        # Consume rate limiter token for provider throttling (AI-08)
        rate_key = f"ai_engine:{self.provider}"
        allowed, wait_sec = self.rate_limiter.consume(
            rate_key=rate_key, max_tokens=50, refill_rate=10.0
        )
        if not allowed and wait_sec > 0:
            import asyncio
            logger.info(
                f"[AIEngine] Rate limit throttled for provider '{self.provider}'. "
                f"Pausing for {wait_sec:.2f}s."
            )
            await asyncio.sleep(min(wait_sec, 2.0))

        client = self.client

        if client is None:
            err = RuntimeError(f"AI Engine client for provider '{self.provider}' is not configured.")
            self.circuit_breaker.record_failure(err)
            raise err

        # Construct clean JSON template for LLM prompt
        field_specs = [
            f'  "{name}": "<{field.description or name}>"'
            for name, field in response_model.model_fields.items()
        ]
        json_template = "{\n" + ",\n".join(field_specs) + "\n}"
        json_instruction = (
            f"\n\nReturn ONLY a valid JSON object strictly matching this exact key structure:\n{json_template}\nDo not wrap keys inside a 'properties' object or include any markdown explanations."
        )

        user_prompt_text = prompt + json_instruction

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Multimodal Vision Payload Construction
        valid_image_urls = [
            url for url in (image_urls or [])
            if isinstance(url, str) and (url.startswith("http://") or url.startswith("https://") or url.startswith("data:image/"))
        ]

        if valid_image_urls:
            user_content: list[dict[str, Any]] = [{"type": "text", "text": user_prompt_text}]
            for img_url in valid_image_urls:
                user_content.append({"type": "image_url", "image_url": {"url": img_url}})
            messages.append({"role": "user", "content": user_content})
            logger.info(f"[AIEngine] [{self.provider}] Vision payload created with {len(valid_image_urls)} image(s) for model '{self.model_name}'. Message sample: {messages[-1]}")
        else:
            messages.append({"role": "user", "content": user_prompt_text})
            logger.info(f"[AIEngine] [{self.provider}] Text-only payload created for model '{self.model_name}'.")

        extra_headers: dict[str, str] = {}
        if self.provider == "openrouter":
            extra_headers["HTTP-Referer"] = "https://civicconnect.org"
            extra_headers["X-Title"] = "CivicConnect AI Engine"

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        # Attempt API call with response_format, fallback without response_format if provider rejects it
        try:
            try:
                response = await client.chat.completions.create(
                    response_format={"type": "json_object"}, **kwargs
                )
            except Exception as api_err:
                logger.warning(f"[AIEngine] response_format or vision payload rejected ({api_err}), attempting fallback request format.")
                if valid_image_urls:
                    messages_fallback: list[dict[str, Any]] = []
                    if system_prompt:
                        messages_fallback.append({"role": "system", "content": system_prompt})
                    messages_fallback.append({"role": "user", "content": f"{user_prompt_text}\n\nAttached Media URLs:\n" + "\n".join(valid_image_urls)})
                    kwargs["messages"] = messages_fallback

                response = await client.chat.completions.create(**kwargs)
            self.circuit_breaker.record_success()
        except Exception as exc:
            self.circuit_breaker.record_failure(exc)
            raise


        raw_content = response.choices[0].message.content or "{}"
        total_tokens = response.usage.total_tokens if response.usage else 0
        execution_ms = (time.time() - start_time) * 1000.0

        # Fast zero-token JSON parse & repair
        parsed_dict = self._parse_json_robust(raw_content)

        # Robust unwrap if LLM wrapped response inside 'properties', 'data', 'result', etc.
        model_keys = set(response_model.model_fields.keys())
        if isinstance(parsed_dict, dict):
            for wrapper_key in ("properties", "data", "result", "response", "output"):
                sub = parsed_dict.get(wrapper_key)
                if isinstance(sub, dict) and any(k in sub for k in model_keys):
                    parsed_dict = sub
                    break

        parsed_model = response_model.model_validate(parsed_dict)

        return parsed_model, execution_ms, total_tokens, self.model_name

    def _parse_json_robust(self, raw_text: str) -> dict[str, Any]:
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
            raise ValueError(f"Could not parse valid JSON from AI model response: {clean_text[:200]}") from err
