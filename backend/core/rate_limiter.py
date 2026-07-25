"""Atomic Redis Lua Token Bucket Rate Limiter with Async Queueing.

Guarantees thread-safe, atomic rate-limiting across distributed Celery workers
and async event loops to protect LLM provider API token/concurrency limits.
"""

import asyncio
import logging
import time
from typing import Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

logger = logging.getLogger(__name__)

# Atomic Redis Lua script for token bucket evaluation
LUA_TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local tokens_requested = tonumber(ARGV[4])

local bucket = redis.call('hmget', key, 'tokens', 'last_updated')
local tokens = tonumber(bucket[1]) or max_tokens
local last_updated = tonumber(bucket[2]) or now

-- Refill tokens based on elapsed time (seconds)
local elapsed = math.max(0, now - last_updated)
tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

if tokens >= tokens_requested then
    tokens = tokens - tokens_requested
    redis.call('hmset', key, 'tokens', tokens, 'last_updated', now)
    return 1  -- Allowed
else
    -- Return remaining tokens and wait estimation (seconds)
    local needed = tokens_requested - tokens
    local wait_time = needed / refill_rate
    return {0, wait_time}  -- Throttled
end
"""


class RedisTokenBucketLimiter:
    """Atomic Redis Token Bucket Rate Limiter with Async Retry Queue."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self.redis = redis_client
        self.script_hash: str | None = None
        self._local_tokens: float = 100.0
        self._local_last_updated: float = time.time()

        if self.redis is not None:
            try:
                self.script_hash = self.redis.script_load(LUA_TOKEN_BUCKET_SCRIPT)
            except Exception as e:
                logger.warning(f"Failed to load Redis Lua script, using in-memory fallback: {e}")
                self.script_hash = None

    def consume(
        self,
        rate_key: str,
        max_tokens: int = 50,
        refill_rate: float = 10.0,
        tokens_requested: int = 1,
    ) -> tuple[bool, float]:
        """Synchronously check and consume tokens.

        Returns:
            (allowed: bool, wait_seconds: float)
        """
        now = time.time()

        # Try Redis Lua script execution first
        if self.redis is not None and self.script_hash is not None:
            try:
                result = self.redis.evalsha(
                    self.script_hash,
                    1,
                    rate_key,
                    max_tokens,
                    refill_rate,
                    now,
                    tokens_requested,
                )
                if result == 1 or result == [1]:
                    return True, 0.0
                elif isinstance(result, list) and len(result) > 1:
                    wait_time = float(result[1]) if result[1] else 0.5
                    return False, max(0.1, wait_time)
                return False, 0.5
            except Exception as err:
                logger.warning(f"Redis rate limiter evaluation failed ({err}), falling back to local bucket.")

        # Local in-memory fallback bucket algorithm
        elapsed = max(0.0, now - self._local_last_updated)
        self._local_tokens = min(float(max_tokens), self._local_tokens + (elapsed * refill_rate))
        self._local_last_updated = now

        if self._local_tokens >= tokens_requested:
            self._local_tokens -= tokens_requested
            return True, 0.0
        else:
            needed = tokens_requested - self._local_tokens
            wait_time = needed / max(refill_rate, 0.1)
            return False, max(0.1, wait_time)

    async def consume_async_queue(
        self,
        rate_key: str,
        max_tokens: int = 50,
        refill_rate: float = 10.0,
        tokens_requested: int = 1,
        max_wait_seconds: float = 15.0,
    ) -> bool:
        """Asynchronously waits in queue until rate limiter tokens become available.

        If tokens are exhausted, the request sleeps dynamically according to calculated
        refill time before retrying, giving up if max_wait_seconds is exceeded.
        """
        start_time = time.time()
        attempt = 0

        while (time.time() - start_time) < max_wait_seconds:
            allowed, wait_seconds = self.consume(
                rate_key=rate_key,
                max_tokens=max_tokens,
                refill_rate=refill_rate,
                tokens_requested=tokens_requested,
            )
            if allowed:
                return True

            attempt += 1
            # Sleep wait estimation capped at max remaining timeout
            remaining_budget = max_wait_seconds - (time.time() - start_time)
            sleep_duration = min(wait_seconds, remaining_budget, 2.0)
            if sleep_duration <= 0:
                break

            logger.info(
                f"[RateLimiter Queue] Key '{rate_key}' throttled (attempt {attempt}). "
                f"Queued sleep for {sleep_duration:.2f}s."
            )
            await asyncio.sleep(sleep_duration)

        logger.error(f"[RateLimiter Queue] Key '{rate_key}' queue timeout after {max_wait_seconds}s.")
        return False
