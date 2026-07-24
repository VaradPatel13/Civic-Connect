# Unit Testing Specification

> Guidance for writing fast, isolated unit tests in backend and mobile packages.

---

# Backend Unit Testing (Python / pytest)

## Framework & Utilities
- Framework: `pytest` + `pytest-asyncio`
- Mocking: `unittest.mock.AsyncMock` or `pytest-mock`

## Conventions
- Test files located in `tests/unit/backend/` matching source module hierarchy (e.g. `tests/unit/backend/services/test_report_service.py`).
- Test functions must be named `test_<feature>_<expected_behavior>()`.
- Pure functions and business rules tested without DB access.

## Example Pattern

```python
import pytest
from unittest.mock import AsyncMock
from backend.services.report_service import ReportService

@pytest.mark.asyncio
async def test_create_report_validates_payload():
    mock_repo = AsyncMock()
    service = ReportService(repo=mock_repo)
    
    result = await service.validate_category("ROADS")
    assert result is True
```

---

# Mobile Unit Testing (TypeScript / Jest)

## Framework & Utilities
- Framework: `jest` + `@testing-library/react-native`
- Mocks: Mock native modules (Expo Location, MMKV, NetInfo).

## Conventions
- Test files co-located or placed in `tests/unit/mobile/`.
- Test Zustand stores, utility functions, and isolated UI components.
