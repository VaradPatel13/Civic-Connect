# Integration Testing Specification

> Specification for testing component interactions, FastAPI endpoints, and database interactions.

---

# Scope

Integration tests verify:
- API endpoint routes (`backend/api/*`)
- Async SQLAlchemy repository queries against PostGIS
- Celery background task invocation
- LangGraph workflow execution with mock LLM providers

---

# Test Setup & Database Isolation

- Test runner spins up a PostGIS container or connects to a dedicated `civic_connect_test` database.
- `httpx.AsyncClient` used to send requests to FastAPI app instance.
- Database transactions rolled back or tables truncated after each test function.

---

# Example API Integration Test

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_submit_report_authenticated(async_client: AsyncClient, auth_headers: dict):
    payload = {
        "issue_type": "Pothole",
        "description": "Large pothole on MG Road near PMC building",
        "latitude": 18.5204,
        "longitude": 73.8567,
    }
    response = await async_client.post("/api/v1/reports", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert "id" in data
```
