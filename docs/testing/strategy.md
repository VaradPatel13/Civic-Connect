# Testing Strategy

> This document defines the testing strategy, standards, tools, and coverage requirements for CivicConnect.

---

# Test Pyramid

```
       /\
      /  \     E2E Tests (Playwright / Expo Maestro) - 10%
     /----\
    /      \   Integration Tests (pytest + AsyncClient + Test DB) - 30%
   /--------\
  /          \ Unit Tests (pytest + Jest + Mocks) - 60%
 /------------\
```

---

# Testing Principles

1. **Automation First**: Every feature must include tests before PR merge.
2. **Deterministic Execution**: Tests must not rely on external networks; mock third-party APIs (Cloudinary, SMS, LLMs).
3. **Isolated Test Database**: Integration tests run against a dedicated PostGIS test container cleaned between runs.
4. **Fast Feedback**: Unit test suite must execute in under 30 seconds.

---

# Coverage Requirements

- **Overall Statement Coverage**: Minimum 85%
- **Core Business Services**: Minimum 95%
- **AI Agent Graph Nodes**: Minimum 90% (using mock LLM outputs)
- **API Endpoints**: Minimum 90% path coverage

---

# CI Pipeline Integration

All pull requests trigger automated GitHub Actions that run:
1. `ruff check` & `mypy` (Backend static checks)
2. `eslint` & `tsc --noEmit` (Frontend static checks)
3. `pytest tests/unit` & `pytest tests/integration`
4. Coverage report generation & enforcement
