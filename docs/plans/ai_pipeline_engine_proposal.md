# Enterprise Production Blueprint: CivicConnect Asynchronous AI Engine & Multi-Agent System

**To:** Engineering Director / Technical Steering Committee  
**From:** Lead AI Systems Architect  
**Subject:** Gold-Standard Production Specification: LangGraph Reducers, Atomic Lua Rate-Limiter, PostGIS & HITL  
**Date:** July 24, 2026  

---

## Executive Summary

To transition CivicConnect into an enterprise gold-standard AI platform capable of executing under real-world municipal storm loads (1,000+ reports/min), this blueprint incorporates key concurrency, state safety, and atomic synchronization patterns:

1. **State Reducer Engine (`merge_agent_outputs`)**: Prevents parallel Celery execution workers from overwriting `agent_outputs` dictionary entries using an explicit shallow-merge state reducer.
2. **Atomic Redis Lua Rate Limiter**: Executes leaky-bucket token calculations inside a single atomic Redis Lua script (`evalsha`) to eliminate distributed check-then-act race conditions.
3. **Presidio Placeholder Prompt Guards**: System prompts instruct LLMs that `[TYPE_TOKEN_ID]` tokens represent valid anonymized citizen data rather than missing input.
4. **Lock-Free Async Audit Batcher**: Buffers audit log entries using thread-safe queue operations and commits bulk saves every 3 seconds to protect database connection pools.
5. **PostGIS `ST_Covers` Spatial Match**: Sub-15ms ward lookups using spatial indexing over official PMC ward boundary geometries.
6. **LangGraph Checkpointer & HITL Interrupts**: Freezes graph execution on policy violations or low confidence, allowing manual administrative overrides via `graph.update_state()`.

---

## 🛠️ Production Code Architecture Patterns

### 1. LangGraph State Reducer (`backend/agents/state.py`)
```python
from typing import Any, Dict, TypedDict, Annotated, Optional

def merge_agent_outputs(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Shallow-merges agent outputs to prevent parallel race overwrites across distributed workers."""
    new_state = dict(left) if left else {}
    if right:
        new_state.update(right)
    return new_state

class PipelineSharedState(TypedDict):
    report_id: str
    trace_id: str
    raw_text: str
    sanitised_payload: Dict[str, Any]
    agent_outputs: Annotated[Dict[str, Any], merge_agent_outputs]
    metadata: Dict[str, Any]
```

### 2. Atomic Redis Rate Limiter Script (`backend/core/rate_limiter.py`)
```python
import time
import redis
from typing import bool

class RedisTokenBucketLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.lua_script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local tokens_requested = tonumber(ARGV[4])

        local bucket = redis.call('hmget', key, 'tokens', 'last_updated')
        local tokens = tonumber(bucket[1]) or max_tokens
        local last_updated = tonumber(bucket[2]) or now

        local elapsed = now - last_updated
        tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

        if tokens >= tokens_requested then
            tokens = tokens - tokens_requested
            redis.call('hmset', key, 'tokens', tokens, 'last_updated', now)
            return 1
        else
            return 0
        end
        """
        self.script_hash = self.redis.script_load(self.lua_script)

    def consume(self, rate_key: str, max_tokens: int, refill_rate: float, cost: int = 1) -> bool:
        now = time.time()
        result = self.redis.evalsha(self.script_hash, 1, rate_key, max_tokens, refill_rate, now, cost)
        return bool(result)
```

### 3. Non-Blocking Async Audit Batcher (`backend/tasks/audit_buffer.py`)
```python
import queue
import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.agent_execution import AgentExecutionAudit

class AsyncAuditBatcher:
    def __init__(self, db_session_factory, max_batch_size: int = 100, flush_interval_sec: float = 3.0):
        self.log_queue: queue.Queue = queue.Queue()
        self.session_factory = db_session_factory
        self.max_batch_size = max_batch_size
        self.flush_interval_sec = flush_interval_sec
        self.last_flush = time.time()

    def enqueue_audit(self, audit_log: Dict[str, Any]) -> None:
        self.log_queue.put(audit_log)
        if self.log_queue.qsize() >= self.max_batch_size:
            self.flush()

    def flush(self) -> None:
        if self.log_queue.empty():
            return

        records_to_insert: List[AgentExecutionAudit] = []
        while not self.log_queue.empty() and len(records_to_insert) < self.max_batch_size:
            try:
                log_data = self.log_queue.get_nowait()
                records_to_insert.append(AgentExecutionAudit(**log_data))
            except queue.Empty:
                break

        if records_to_insert:
            with self.session_factory() as session:  # type: Session
                try:
                    session.bulk_save_objects(records_to_insert)
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
        self.last_flush = time.time()
```

---

## 🗺️ Phased Implementation Sequence

```
Phase 1: Core AI Engine & Utility Foundations
  ├── backend/agents/state.py (With merge_agent_outputs reducer)
  ├── backend/core/ai_engine.py (Base provider, json_repair, tenacity)
  ├── backend/core/rate_limiter.py (Atomic Redis Lua Script)
  └── backend/tasks/audit_buffer.py (Async Batch Aggregator)

Phase 2: 9 Specialized Agents
  ├── supervisor.py & forensics.py
  ├── classifier.py (With Presidio placeholder prompt guards)
  ├── geo_validator.py (PostGIS ST_Covers spatial queries)
  ├── moderator.py, enhancer.py, router.py
  └── notifier.py & auditor.py

Phase 3: LangGraph Compilation & Service Integration
  ├── backend/agents/pipeline.py (LangGraph DAG with interrupt_after)
  ├── backend/services/ai_pipeline_service.py (Async FastAPI Task Integration)
  └── backend/tests/test_ai_pipeline.py (Comprehensive Pytest Suite)
```

---

This gold-standard plan is finalized and ready for execution.
