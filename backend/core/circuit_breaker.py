"""Circuit Breaker Pattern implementation for AI LLM Providers.

Prevents cascading system failures and endless connection timeouts when NVIDIA NIM
or OpenRouter inference API endpoints experience outages.

States:
- CLOSED: Normal operational state. All calls pass through to primary LLM provider.
- OPEN: Failure rate exceeded threshold. Calls fail fast or drop back to local rules.
- HALF-OPEN: Testing recovery after cooldown window expires.
"""

from __future__ import annotations

import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Manages failure rates and circuit trip states for external AI providers."""

    def __init__(
        self,
        name: str = "llm_provider",
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0

    def allow_execution(self) -> bool:
        """Determines if a request should be allowed through to the LLM provider."""
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.recovery_timeout_seconds:
                logger.info(f"[CircuitBreaker:{self.name}] Cooldown window elapsed. Transitioning OPEN -> HALF-OPEN.")
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        """Records a successful LLM inference call."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"[CircuitBreaker:{self.name}] Successful call in HALF-OPEN. Resetting to CLOSED.")
            self.state = CircuitState.CLOSED
            self.failure_count = 0

    def record_failure(self, error: Exception) -> None:
        """Records a failed LLM inference call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"[CircuitBreaker:{self.name}] Failure #{self.failure_count}: {error}")

        if self.failure_count >= self.failure_threshold and self.state == CircuitState.CLOSED:
            self.state = CircuitState.OPEN
            logger.error(f"[CircuitBreaker:{self.name}] Failure threshold reached! Circuit tripped to OPEN.")


# Global Circuit Breakers for primary providers
nim_circuit_breaker = CircuitBreaker(name="nvidia_nim", failure_threshold=3, recovery_timeout_seconds=30.0)
openrouter_circuit_breaker = CircuitBreaker(name="openrouter", failure_threshold=5, recovery_timeout_seconds=45.0)
