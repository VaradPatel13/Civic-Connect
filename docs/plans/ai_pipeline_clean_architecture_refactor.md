# Production Clean Architecture Refactoring Plan for CivicConnect AI Pipeline

## Overview
This plan outlines the production-grade refactoring of the CivicConnect multi-agent AI pipeline into a Clean Architecture system designed for municipal-scale operation (millions of citizens).

---

## 1. Architectural Gap Analysis (Current vs Target)

### What Needs Refinement:
1. **Pure Agent Separation**: Ensure zero database, SQL, or HTTP handlers inside agent classes. All IO must occur strictly through repository interfaces and service orchestration.
2. **Quality Gate Decision Node**: Add an explicit confidence evaluation gate (`QualityGate`) after parallel validation (Moderation, Forensics, Classification, Geo Validation). If confidence scores fall below threshold (< 0.70/0.80), transition report to `PENDING_MANUAL_REVIEW`.
3. **Domain & Workflow Layers**: Introduce `/backend/domain` (DTOs, Value Objects, Domain Events) and `/backend/workflows` (LangGraph state graphs, node execution graphs) to isolate orchestrator logic from service & API handlers.
4. **Granular Database Models**: Add dedicated models and tables for `classification_results`, `geo_validations`, `image_analyses`, `enhancements`, `report_events`, and `department_assignments`.
5. **Immutable Event Trail**: Write immutable `ReportEvent` logs on every report status change (`SUBMITTED`, `PROCESSING`, `PENDING_MANUAL_REVIEW`, `VERIFIED`, `ASSIGNED`, `REJECTED`).

---

## 2. Target Directory & Layer Mapping

```
backend/
├── api/             # FastAPI Endpoint Controllers
├── core/            # Config, Security, Database Engine, Unified AI Client
├── database/        # Session Factories & Migration Hooks
├── domain/          # Pure Domain Entities, Value Objects & Event Definitions
├── models/          # SQLAlchemy 2.0 ORM Models with Constraints & Indexes
├── schemas/         # Pydantic v2 DTO Input/Output Contracts
├── repositories/    # Async Repository Pattern for DB Access
├── agents/          # Pure AI Logic Agents (No DB/HTTP)
├── workflows/       # LangGraph Orchestration & Node Definitions
├── services/        # Business Logic & Pipeline Orchestration Services
├── events/          # Domain Event Handlers & Notification Dispatchers
└── tests/           # Unit & Integration Test Suite
```

---

## 3. Step-by-Step Execution Plan

### Step 3.1: Create Domain & Workflow Directories
- Create `backend/domain/` (events, entities).
- Create `backend/workflows/` (LangGraph graph definition).

### Step 3.2: Enhance Database Models & Repositories
- Update `backend/models/reports.py` and `agent_executions.py` to support `PENDING_MANUAL_REVIEW` status.
- Add/verify models for `ReportEvent` for immutable status change tracking.

### Step 3.3: Implement Quality Gate & Pure Agents
- Refactor `AIPipelineService` to enforce Quality Gate rules:
  - Moderate Check: If clean == False -> `REJECTED`
  - Confidence Check: If classification confidence < 0.60 or geo match == False -> `PENDING_MANUAL_REVIEW`
  - Otherwise -> Proceed to Enhancement, Routing, Notification, and Audit Recording.

### Step 3.4: Comprehensive Real-Time Terminal Logging
- Print step-by-step audit logs for all 9 pipeline steps in standard ASCII format.

### Step 3.5: Quality Verification
- Run `python -m ruff check backend/services/ai_pipeline_service.py` to guarantee zero lint or type errors.
- Test end-to-end processing with sample reports.
