# Implementation Plan - Production Background AI Pipeline Execution

The goal is to connect the true LangGraph 9-agent AI processing pipeline (`create_civic_pipeline_graph`) to report submission via a resilient background worker system (FastAPI `BackgroundTasks` with isolated async session management).

## Architectural Principles & Layer Separation

1. **API Layer (`backend/api/reports.py`)**:
   - On `POST /api/v1/reports/`, persist the report to DB with `status = PENDING`.
   - Dispatch `process_report_background(report.id)` via FastAPI `BackgroundTasks`.
   - Immediately return `201 Created` with report details (< 50 ms latency).

2. **Service Layer (`backend/services/ai_pipeline_service.py`)**:
   - Runs in isolated async background session (`AsyncSessionLocal()`).
   - Invokes `create_civic_pipeline_graph().ainvoke(...)` with `PipelineSharedState`.
   - Executes parallel multi-agent pipeline:
     - **Supervisor**: Initial validation & state setup.
     - **Parallel Step**: Forensics, Classifier, Geo Validator, Moderator.
     - **Sequential Step**: Enhancement, Router, Notifier.
   - Updates report status (`PROCESSING` -> `ASSIGNED` or `REJECTED`), updates department assignment, urgency, and category.
   - Writes immutable execution logs to `agent_executions` table.

3. **Resilience & Fallback Handling**:
   - Wrap worker execution in `try / except` blocks.
   - Ensure failures trigger fallback department routing (`General Administration`) and set report status to `ASSIGNED` with audit warning, ensuring no submitted report is left stuck in `PENDING`.

## Proposed Code Changes

### 1. `backend/services/ai_pipeline_service.py`
- Refactor `AIPipelineService` to bridge `create_civic_pipeline_graph` execution state with SQLAlchemy models and repositories.
- Add background task entry point `run_ai_pipeline_background(report_id: UUID)`.

### 2. `backend/api/reports.py`
- Inject `BackgroundTasks` into `create_report`.
- Call `background_tasks.add_task(run_ai_pipeline_background, report.id)`.

### 3. `backend/tests/test_ai_pipeline.py` & `backend/tests/test_reports.py`
- Verify async background pipeline execution and database state updates in test suite.

## Verification & Audit Strategy
- Run `ruff check backend/`
- Run `python -m pytest backend/tests`
- Run `npx tsc --noEmit`
