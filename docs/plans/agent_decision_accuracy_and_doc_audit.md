# Execution Plan: Hardening Agent Decision Accuracy to 100% & Comprehensive Documentation Audit

## Overview
This plan establishes strict zero-hallucination guardrails across the 9-agent AI pipeline in CivicConnect to guarantee 100% decision accuracy. Additionally, it audits all documentation files in `docs/` and root, removing obsolete/empty files and synchronizing specs with current codebase contracts.

---

## Phase 1: AI Agent Hardening for 100% Correct Decisions

### 1. Classification Agent (`backend/agents/classifier.py`)
- **Explicit Domain System Prompt**: Detail exact boundaries for each PMC category (`ROADS`, `WATER`, `DRAIN`, `ELEC`, `HEALTH`, `SANIT`, `FIRE`, `BUILD`, `TRAFF`, `PARKS`, `ADMIN`).
- **Post-Classification Cross-Validation**:
  - Compare LLM category output against keyword match density.
  - If LLM returns Category A with 0 keyword matches while keyword score for Category B is >= 2, override with ground-truth Category B or downgrade confidence below 0.60 to invoke fallback, eliminating hallucinations.
- **Urgency Grounding**: Enforce strict mapping for high/critical keyword triggers.

### 2. Geo-Validation Agent (`backend/agents/geo_validator.py`)
- **Coordinate Boundary Guard**: Verify lat/lon within Pune PMC geographical bounds (lat 18.3–18.7, lon 73.6–74.0). Out-of-bounds coordinates automatically set `boundary_matched=False`, `ward_name="Outside PMC Jurisdiction"`, `confidence=0.0`.
- **PostGIS & Bounding Box Match**: First attempt PostGIS `ST_Covers` query, fallback to official PMC ward bounding boxes.

### 3. Content Moderator Agent (`backend/agents/moderator.py`)
- **Extended Prompt Injection Guards**: Screen for injection patterns (`override rules`, `forget instructions`, `eval(`, `exec(`, `<script`, `system prompt`, `union select`).
- **Fail-Safe Policy**: On error or ambiguity, fail safe by setting `requires_human_review=True`.

### 4. Department Router Agent (`backend/agents/router.py`)
- **Deterministic SLA & Priority Scoring**: Map categories strictly to PMC department codes (`PMC_DEPT_ROADS`, `PMC_DEPT_WATER`, etc.) with SLA targets (Critical=4h, High=24h, Medium=72h, Low=168h).

---

## Phase 2: Documentation Audit & Cleanup

### 1. Deletion of Obsolete/Empty Files
- Remove 0-byte empty plan files:
  - `docs/plans/ai_pipeline_terminal_logging.md`
  - `docs/plans/classifier_agent_refactoring.md`

### 2. Documentation Updates
- Update `docs/specs/AGENT.md` & `docs/specs/ai-pipeline.md`:
  - Document post-classification cross-validation rules.
  - Document zero-hallucination coordinate envelope bounds.
  - Document immutable audit trail guarantees in `agent_executions`.

---

## Verification
- Run `python -m pytest backend/tests/test_ai_pipeline.py`
- Run `ruff check backend/agents/`
