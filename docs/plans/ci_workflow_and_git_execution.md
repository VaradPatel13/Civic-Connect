# CI Workflow & Git Execution Plan

## Goal
Implement a robust GitHub Actions CI pipeline and structure all local workspace changes using Trunk-Based Development with clean, conventional commits.

## Tasks

1. **Create GitHub Actions CI Pipeline (`.github/workflows/ci.yml`)**
   - Job 1: `mobile-ci` — Runs `npm ci` and `npx tsc --noEmit` inside `app/`.
   - Job 2: `backend-ci` — Sets up Python, installs requirements, runs `ruff check` and `pytest`.

2. **Git Commit & Branch Execution**
   - Create and commit `feature/mobile-fixes`:
     - Scope: `app/` files, `docs/plans/mobile_app_fix.md`.
     - Commit message: `fix(mobile): resolve metro blocklist, add expo icons, create-report modal and keep-awake guard`.
   - Create and commit `feature/ai-triage-engine`:
     - Scope: `backend/agents/`, `backend/core/ai_engine.py`, `backend/tests/test_ai_pipeline.py`, `docs/plans/ai_pipeline_engine.md`.
     - Commit message: `feat(ai): implement LangGraph agent triage pipeline and test suite`.
   - Create and commit `ci/github-actions`:
     - Scope: `.github/workflows/ci.yml`.
     - Commit message: `ci(workflows): add GitHub Actions automated CI workflow`.
   - Merge feature branches into `main`.

3. **Verification**
   - Run local type checks and pytest to verify all stacks are green.
