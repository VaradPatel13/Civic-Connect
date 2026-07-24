# Execution Plan: Database Migration & Alembic Setup

## Objective
Execute database migrations for CivicConnect using Alembic, fixing `backend/migrations/env.py` execution handler, ensuring proper model metadata registration, dynamic setting of DB connection strings from `backend.core.config`, and verifying schema state.

---

## 1. Audit & Research Findings
- **Issue in `env.py`**: `backend/migrations/env.py` defines `run_migrations_online()`, but never calls it when Alembic executes `env.py`. As a result, running `alembic upgrade head` completes silently without running any database operations.
- **Config integration**: `env.py` should dynamically load `settings.database_url` from `backend.core.config.settings` so that `.env` and environment overrides are respected.
- **Offline mode**: `run_migrations_offline()` is missing from `env.py`.

---

## 2. Plan of Action

### Step 1: Update `backend/migrations/env.py`
- Import `settings` from `backend.core.config`.
- Set `config.set_main_option("sqlalchemy.url", settings.database_url)`.
- Implement `run_migrations_offline()` and `run_migrations_online()`.
- Add top-level call:
  ```python
  if context.is_offline_mode():
      run_migrations_offline()
  else:
      run_migrations_online()
  ```

### Step 2: Database Connection & Migration Execution
- Run `python -m alembic upgrade head`.
- Verify migration status with `python -m alembic current`.

### Step 3: Quality Gates & Verification
- Run `ruff check backend/migrations/`
- Run `mypy --strict backend/migrations/env.py` (or static analysis check).

---

## 3. Verification Criteria
- [ ] `env.py` correctly triggers online/offline migrations.
- [ ] Alembic migration `dd3c5874a143_initial_schema` executes or reports correct revision.
- [ ] Code passes linting and type checking.
