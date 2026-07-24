# 🤖 Autonomous Coding Guidelines for CivicConnect

This document adapts the giskard-oss autonomous coding conventions for CivicConnect's specific requirements.

## Setup

Run once before making changes:

```bash
# Activate project environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Verify setup
python -c "import models; print('OK')"
```

## Planning Flow

### 1. Plan Mode Required
- **MUST** enter plan mode for any non-trivial task (3+ steps)
- Brainstorm → Design → Spec → Plan
- Save specs to `docs/specs/` and plans to `docs/plans/`

### 2. Task Tracking
- Create `docs/todo.md` before implementation
- Mark items complete as you go
- Add review/results section before any push

Example todo.md structure:
```markdown
# CivicConnect Agent Pipeline Implementation

## Tasks
- [x] Create agent state model
- [ ] Implement forensics agent
- [ ] Set confidence thresholds
- [ ] Write unit tests

## Results
- Forensics agent passes all edge cases (fake photos, missing files)
- Confidence threshold: >0.7, fallback accepts unverified
```

## Stop Conditions

**DO NOT** proceed when:

1. **Ambiguity** — Requirements unclear or contradictory
2. **Missing context** — Critical data files not provided
3. **Unclear acceptance criteria** — No defined success metrics

**Instead:** Post ONE clarifying comment and STOP.

### Example Clarifying Comment:

> Clarification needed: Should the forensics agent accept reports without photos, or reject them immediately?
>
> Context: The current spec says "Photos → {authentic, confidence}" but doesn't specify photo requirement.
>
> Options:
> - **Reject** if no photos (stricter, fewer fake reports)
> - **Accept** without forensics check (better UX, need mitigation)

## Coding Standards

### Code Quality Rules

1. **Type Safety First**
   - Python: Type hints on all functions
   - No `# type: ignore` unless documented
   - Use `Any` only with comment explaining why

2. **Error Handling**
   - Every async operation must have try/except
   - Log errors to agent_executions table
   - Never raise raw exceptions to API

3. **File Organization**
   ```
   backend/
   ├── agents/           # LangGraph pipeline
   │   ├── state.py      # Typed state
   │   ├── supervisor.py # Main graph
   │   ├── forensics.py
   │   ├── classifier.py
   │   └── ...
   ├── models/           # SQLAlchemy
   ├── schemas/          # Pydantic
   ├── api/              # FastAPI routes
   ├── services/         # Business logic
   ├── tasks/            # Celery
   └── core/             # Config, security
   ```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase` (Agent, Report, Citizen)
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Variables**: `camelCase`

### Agent-Specific Rules

When writing agent code:

1. **State Machine Pattern**
   ```python
   class AgentState(dict):
       """LangGraph state with type hints."""
       report: Report
       agent_outputs: dict[str, Any]
       current_agent: str
   ```

2. **Confidence Logging**
   ```python
   def forensics_agent(images: list[str]) -> ForensicResult:
       result = cnn_analyze(images)
       log_agent_execution(
           agent_name="forensics",
           input={"images": images[:2]},  # Truncate for safety
           output=result.model_dump(),
           confidence=result.confidence,
           status="success" if result.confidence > 0.7 else "low_confidence"
       )
       return result
   ```

3. **Fallback Chain**
   ```python
   def classifier_agent(report: Report) -> Classification:
       try:
           return llm_classify(report)
       except Exception as e:
           log_error(e)
           return keyword_fallback(report.description)  # Always have fallback
   ```

## Test Commands

```bash
# Format code
make format

# Run checks
make check

# Run unit tests for specific package
make test-unit PACKAGE=agents

# Run integration tests
make test-integration

# Run all tests
make test
```

## Git Commit Hygiene

Use conventional commit messages:

| Type | When | Example |
|------|------|---------|
| `feat:` | New feature | `feat(agents): add forensics confidence threshold` |
| `fix:` | Bug fix | `fix(auth): validate phone number format` |
| `refactor:` | Code cleanup | `refactor(pipeline): extract supervisor state` |
| `docs:` | Documentation | `docs: add agent pipeline diagram` |
| `test:` | Tests | `test: add integration test for report flow` |
| `chore:` | Maintenance | `chore: update dependencies` |

**End commit titles with:** `🤖🤖🤖🤖` when making autonomous changes

## Review Process

### 1. Self-Review Before Push
- [ ] Tests pass (`make test`)
- [ ] Violations (`make check`)
- [ ] Secrets not exposed
- [ ] Type checker clean (`mypy`)

### 2. Code Review Checklist
- [ ] Correctness: Logic matches spec
- [ ] Style: Matches project conventions
- [ ] Tests: New code covered
- [ ] Performance: No N+1 queries
- [ ] Security: No CSRF, XSS, injection

## Messaging Patterns

When you need human input:

1. **ONE comment** with specific questions
2. **Wait for response** before proceeding
3. **If no response**: Remain stopped, document why

Example:

> Wait for confirmation on confidence threshold for forensics agent.
>
> Option A: >0.7 (strict, fewer false reports)
> Option B: >0.5 (lenient, better UX)
>
> Suggestion: Option A aligns with gov use case. Please confirm.

## Domain-Specific Adaptations

Based on CivicConnect requirements:

1. **Week Format**: `Ward A`, `Kothrud` etc. (PMC naming)
2. **Languages**: `mr`, `hi`, `en` (Marathi primary)
3. **Issue Types**: pothole, garbage, drainage, water_leak, etc.
4. **Departments**: Road, Drainage, Water, Solid_Waste, Street_Light, Garden, Building, Health, Fire, Disaster
5. **Phone Format**: Must be E.164 (`+91XXXXXXXXXX`)

## Features to Build

### Priority Order

1. **Auth Layer** (already started)
   - JWT + OTP
   - Device token storage
   - Profile endpoints

2. **Database Layer**
   - Models + Alembic migrations
   - PostGIS extensions
   - Seed data (wards, departments)

3. **Agent Pipeline**
   - State model
   - Validation supervisor
   - Forensics agent
   - Classifier agent
   - Geo-validator
   - Moderator
   - Enhancer
   - Router
   - Notifier
   - Auditor

4. **API Endpoints**
   - Reports CRUD
   - Agent triggers
   - Status tracking

5. **Mobile App**
   - Login screens
   - Report form
   - Status dashboard

### Confidence Thresholds (CivicConnect-Specific)

- **Forensics**: >0.7 (fake photo detection critical for gov trust)
- **Classifier**: >0.6 (routing accuracy matters)
- **Moderator**: >0.8 (content quality gate)
- **Geo-Validator**: PostGIS exact match (no fallback for location)

## Learning Loop

After **any correction**:

1. **Document the rule** in code comments or templates
2. **Update AGENT.md** if pattern applies broadly
3. **Add test** for edge case
4. **Verify** rule prevents future mistakes

Example after OCR failure:

```python
# AGENT.md update:
# "Image analysis must handle missing EXIF data - PIL throws OSError"

def forensics_agent(image_path: str):
    try:
        exif = get_exif(image_path)  # Can fail on screenshots
    except OSError:
        log_warning(f"No EXIF for {image_path}, using filename only")
        exif = {"source": "unknown"}
```

## Resources

- [AGENTS.md](./specs/AGENT.md) - Agent pipeline specs
- [CLAUDE.md](../CLAUDE.md) - Project overview
- [Project Structure](../project.md) - File organization
- [English Spec](english-spec.md) - Full requirements

---

**Remember**: Simplicity before complexity. Government systems must be debuggable, auditable, and reliable.