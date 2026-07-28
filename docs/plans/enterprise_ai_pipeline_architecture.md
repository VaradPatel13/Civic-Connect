# Enterprise Multi-Agent AI Pipeline Specification & Refactoring Plan (10/10 Rating Target)

## Overview
This specification addresses all 10 enterprise gaps identified in the Senior Technical Review. It elevates the CivicConnect multi-agent AI pipeline from a prototype to a fault-tolerant, idempotent, observable, production-grade architecture capable of processing millions of civic reports across municipal jurisdictions.

---

## 1. Architectural Architecture & Component Blueprint

```
                          ┌────────────────────────┐
                          │  Citizen / Mobile App  │
                          └───────────┬────────────┘
                                      │ (HTTP/REST + Idempotency Key)
                                      ▼
                          ┌────────────────────────┐
                          │      API Gateway       │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │ Validation Supervisor  │
                          └───────────┬────────────┘
                                      │  (Init Workflow State & Idempotency Check)
                                      ▼
                          ┌────────────────────────┐
                          │ Workflow State Store   │
                          │   (PostgreSQL / Redis) │
                          └───────────┬────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │      Parallel Fan-Out (with Timeouts)        │
              ▼                                               ▼
   ┌────────────────────┐                           ┌────────────────────┐
   │  Moderation Agent  │                           │   Forensics Agent  │
   └──────────┬─────────┘                           └─────────┬──────────┘
              │                                               │
              ▼                                               ▼
   ┌────────────────────┐                           ┌────────────────────┐
   │ Classification Agt │                           │ Geo Validator Agt  │
   └──────────┬─────────┘                           └─────────┬──────────┘
              └───────────────────────┬───────────────────────┘
                                      │  (Cross-Cutting Audit after EVERY step)
                                      ▼
                          ┌────────────────────────┐
                          │  Result Aggregator &   │
                          │      Quality Gate      │
                          └───────────┬────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                │ Low Confidence / Unmatched Ward?          │
                ▼                                           ▼
      [Yes] ┌──────────────────────┐              [No] ┌──────────────────────┐
            │ PENDING_MANUAL_REVIEW│                   │  Enhancement Agent   │
            └──────────┬───────────┘                   └──────────┬───────────┘
                       │ (Human Officer Review)                   │
                       └───────────────────►──────────────────────┤
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │  Department Router   │
                                                       └──────────┬───────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │ Notification Service │
                                                       └──────────┬───────────┘
                                                                  │
                                                                  ▼
                                                       ┌──────────────────────┐
                                                       │ Immutable Event Log  │
                                                       └──────────────────────┘
```

---

## 2. Core Technical Solutions (Addressing All 10 Gaps)

### Gap 1: Persistent Workflow State & Resiliency (`workflow_states` table)
- **Problem**: Backend server restarts mid-workflow leave reports stranded in `PROCESSING` status with no state recovery mechanism.
- **Solution**: Create a `workflow_states` table storing `workflow_id`, `trace_id`, `report_id`, `current_step`, `failed_step`, `retry_count`, `state_payload` (JSONB).
- **Recovery**: Add a `resume_interrupted_workflows()` cron/background worker that queries stale `PROCESSING` workflow states (>5 mins) and resumes from the last completed node.

### Gap 2: Idempotency & Deduplication (`IdempotencyService`)
- **Problem**: Multiple taps on "Submit" or task queue retries create duplicate DB reports and waste expensive LLM tokens.
- **Solution**: Compute SHA-256 hash of `(citizen_id, title, description, latitude, longitude)`. Cache in Redis/PostgreSQL for 10 minutes. If duplicate detected, return existing `report_id`.

### Gap 3: Exponential Backoff Retries & Dead Letter Queue (DLQ)
- **Problem**: Transient LLM network hiccups fail the entire pipeline.
- **Solution**: Wrap LLM invocations in a retry decorator (`max_retries=3`, `backoff_factor=2.0`). Route persistent failures to a Dead Letter Queue table (`dlq_tasks`) for manual inspection.

### Gap 4: Per-Agent Timeouts & Fallback Strategies
- **Problem**: LLM provider hanging indefinitely blocks background worker threads.
- **Solution**: Enforce `asyncio.wait_for(agent.process(...), timeout=15.0)` per agent. If timed out, log `AgentStatus.TIMEOUT` and load rule-based fallback predictions.

### Gap 5: Human Review Loop & Resume Endpoint
- **Problem**: Reports in `PENDING_MANUAL_REVIEW` are stranded with no formal workflow to re-enter processing after officer review.
- **Solution**: Implement `POST /api/v1/reports/{id}/review` endpoint allowing municipal officers to override category/ward and resume pipeline execution starting at the Enhancement & Routing phase.

### Gap 6: Circuit Breaker Pattern (`CircuitBreaker`)
- **Problem**: Outages in NVIDIA NIM / OpenRouter trigger repeated 30s connection timeouts across thousands of citizen reports.
- **Solution**: Implement a 3-state Circuit Breaker (`CLOSED`, `OPEN`, `HALF-OPEN`). If failure rate exceeds 50% over 10 calls, trip to `OPEN` state for 60 seconds and direct traffic to local heuristic models or secondary provider (e.g. Gemini).

### Gap 7: Distributed Tracing & OpenTelemetry (`trace_id`, `span_id`)
- **Problem**: Logs lack context correlation across API, task queue, and agent executions.
- **Solution**: Inject `trace_id` and unique `span_id` into all structured logger outputs, HTTP response headers (`X-Trace-ID`), and database audit entries.

### Gap 8: Enhanced Cost & Telemetry Schema (`agent_executions`)
- **Problem**: Lack of granular token tracking makes financial budgeting and performance tuning impossible.
- **Solution**: Add `tokens_prompt`, `tokens_completion`, `estimated_cost`, `temperature`, `input_hash`, and `output_hash` to `agent_executions` table schema.

### Gap 9: Real-time Prometheus Metrics (`backend/core/metrics.py`)
- **Problem**: Logging without metric aggregation prevents operational dashboard monitoring.
- **Solution**: Expose `/metrics` endpoint with Prometheus counters and histograms:
  - `civic_reports_submitted_total`
  - `civic_agent_execution_latency_seconds`
  - `civic_llm_token_usage_total`
  - `civic_quality_gate_review_total`

### Gap 10: Cross-Cutting Immediate Audit Logger
- **Problem**: Audit log was previously written only as a batch or final step.
- **Solution**: Refactor pipeline execution so that **immediately after every agent finishes**, its audit record is committed to PostgreSQL in an independent sub-transaction.

---

## 3. Implementation Roadmap

1. **Schema Enhancements**: Update `backend/models/agent_executions.py` with cost/token telemetry fields.
2. **Circuit Breaker & Retry Helper**: Create `backend/core/circuit_breaker.py`.
3. **Workflow State Manager**: Create `backend/services/workflow_state_service.py`.
4. **Quality Gate & Officer Review API**: Create `POST /api/v1/reports/{id}/review` in `backend/api/v1/endpoints/reports.py`.
5. **Quality Verification**: Execute `python -m ruff check backend/` and test full multi-agent pipeline workflow.
