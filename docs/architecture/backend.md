# Backend Architecture

> This document describes the architectural design of the CivicConnect backend.
>
> It is the authoritative reference for the FastAPI application structure, layered design, request lifecycle, background processing, and service contracts.

---

# Overview

The CivicConnect backend is a FastAPI application that serves as the central coordination point between citizens, the AI pipeline, the database, and external services.

It is designed around strict layered architecture, asynchronous I/O, and event-driven background processing.

---

# Technology Stack

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Database driver | asyncpg |
| Schema validation | Pydantic v2 |
| Migrations | Alembic |
| Background tasks | Celery |
| Message broker | Redis |
| AI orchestration | LangGraph |
| Password hashing | bcrypt |
| Authentication | JWT (python-jose) |
| Image storage | Cloudinary SDK |
| Push notifications | Firebase Admin SDK |

---

# Repository Structure

```
backend/
├── api/                    # Route handlers (HTTP endpoints)
│   ├── auth.py
│   ├── reports.py
│   ├── users.py
│   ├── departments.py
│   ├── notifications.py
│   └── rewards.py
│
├── agents/                 # LangGraph pipeline
│   ├── graph.py            # Supervisor workflow definition
│   ├── state.py            # Shared workflow state schema
│   ├── nodes/              # Individual agent nodes
│   │   ├── validation.py
│   │   ├── forensics.py
│   │   ├── classification.py
│   │   ├── geo_validation.py
│   │   ├── moderation.py
│   │   ├── enhancement.py
│   │   ├── routing.py
│   │   ├── notification.py
│   │   └── audit.py
│   └── tools/              # Agent tool implementations
│
├── models/                 # SQLAlchemy ORM models
│   ├── base.py
│   ├── citizen.py
│   ├── report.py
│   ├── department.py
│   ├── ward.py
│   ├── photo.py
│   ├── assignment.py
│   ├── status_log.py
│   ├── agent_execution.py
│   ├── otp_code.py
│   └── reward.py
│
├── schemas/                # Pydantic request/response schemas
│   ├── auth.py
│   ├── report.py
│   ├── user.py
│   ├── department.py
│   └── common.py
│
├── services/               # Business logic
│   ├── auth_service.py
│   ├── report_service.py
│   ├── user_service.py
│   ├── department_service.py
│   ├── media_service.py
│   ├── notification_service.py
│   └── reward_service.py
│
├── tasks/                  # Celery background workers
│   ├── worker.py
│   ├── process_report.py
│   ├── send_notification.py
│   └── cleanup.py
│
├── core/                   # Shared infrastructure
│   ├── config.py           # Settings via pydantic-settings
│   ├── database.py         # Async SQLAlchemy session factory
│   ├── security.py         # JWT and password utilities
│   ├── dependencies.py     # FastAPI dependency injection
│   ├── logging.py          # Structured logging configuration
│   └── exceptions.py       # Custom exception hierarchy
│
├── migrations/             # Alembic migration scripts
│   └── versions/
│
└── main.py                 # Application factory
```

---

# Layered Architecture

The backend enforces strict layering. Each layer has a single responsibility and dependencies flow downward only.

```
HTTP Request
     │
     ▼
 API Layer          ← Route handlers only. No business logic.
     │
     ▼
Service Layer       ← Business logic. No HTTP knowledge.
     │
     ▼
 Data Layer         ← SQLAlchemy queries only. No business logic.
     │
     ▼
 PostgreSQL
```

**Invariants:**

- Route handlers never access the database directly
- Services never import FastAPI types
- Models never contain business logic
- Pydantic schemas are not SQLAlchemy models

---

# Request Lifecycle

## Standard API Request

```
Client sends HTTPS request
        │
        ▼
FastAPI router matches endpoint
        │
        ▼
Middleware executes (CORS, logging, rate limiting)
        │
        ▼
Dependency injection resolves (DB session, current user)
        │
        ▼
Pydantic validates request body
        │
        ▼
Route handler delegates to service
        │
        ▼
Service executes business logic
        │
        ▼
Data layer executes async query
        │
        ▼
Response assembled and serialized
        │
        ▼
Client receives JSON response
```

## Report Submission Lifecycle

```
POST /reports
        │
        ▼
Validate citizen authentication
        │
        ▼
Validate Pydantic request schema
        │
        ▼
ReportService.create()
        │
        ▼
Store report in PostgreSQL (status: pending)
        │
        ▼
Upload images to Cloudinary
        │
        ▼
Enqueue Celery task: process_report
        │
        ▼
Return 201 Created with report ID
        │
     (async)
        │
        ▼
Celery worker picks up task
        │
        ▼
LangGraph supervisor executes
        │
        ▼
AI pipeline updates report in DB
        │
        ▼
Citizen receives push notification
```

---

# Asynchronous Design

All I/O operations are non-blocking.

| Component | Async Pattern |
|-----------|--------------|
| Database queries | `async with AsyncSession` |
| HTTP calls to external APIs | `httpx.AsyncClient` |
| Image uploads | `asyncio.to_thread` (Cloudinary SDK is sync) |
| Background tasks | Celery with Redis broker |
| WebSocket connections | FastAPI WebSocket |

The Celery worker runs in a separate process. It uses its own synchronous database connections via psycopg2.

---

# Dependency Injection

FastAPI dependencies are defined in `core/dependencies.py`:

| Dependency | Description |
|------------|-------------|
| `get_db` | Yields an async SQLAlchemy session |
| `get_current_citizen` | Validates JWT and returns active citizen |
| `get_current_admin` | Validates JWT and asserts admin role |
| `get_current_officer` | Validates JWT and asserts officer role |
| `require_verified` | Asserts the citizen's account is OTP-verified |

Dependencies are composed using FastAPI's `Depends()` system.

---

# Error Handling

The backend uses a custom exception hierarchy defined in `core/exceptions.py`:

```
CivicConnectException
├── AuthenticationError       → 401
├── AuthorizationError        → 403
├── NotFoundError             → 404
├── ValidationError           → 422
├── ConflictError             → 409
├── RateLimitError            → 429
├── ServiceUnavailableError   → 503
└── InternalError             → 500
```

All exceptions return a consistent JSON structure:

```json
{
  "error": "NOT_FOUND",
  "message": "Report not found",
  "detail": null
}
```

Internal error details are never exposed to clients.

---

# Configuration

Application configuration is managed via `core/config.py` using `pydantic-settings`.

Configuration is loaded from environment variables. No hard-coded values are permitted in application code.

Key configuration groups:

| Group | Variables |
|-------|-----------|
| Database | `DATABASE_URL` |
| Redis | `REDIS_URL` |
| JWT | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Cloudinary | `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` |
| Firebase | `FIREBASE_CREDENTIALS_PATH` |
| AI | `NVIDIA_NIM_API_KEY`, `OPENROUTER_API_KEY` |
| OTP | `OTP_EXPIRY_MINUTES`, `OTP_MAX_ATTEMPTS` |

Configuration must never be committed to source control.

---

# Middleware

| Middleware | Purpose |
|------------|---------|
| CORS | Allow frontend origins |
| Request logging | Log every request and response code |
| Rate limiting | Per-IP and per-user limits on auth endpoints |
| Request ID | Attach a unique trace ID to every request |

---

# WebSocket Support

Real-time report status updates are delivered via WebSocket.

```
WS /ws/reports/{report_id}
```

Connection authentication uses a short-lived WebSocket token derived from the JWT access token.

---

# Background Task Architecture

Celery workers process:

| Task | Trigger |
|------|---------|
| `process_report` | Report submission |
| `send_push_notification` | Report status change |
| `send_sms` | OTP delivery, report updates |
| `send_email` | Transactional emails |
| `cleanup_expired_otps` | Scheduled, every hour |
| `audit_sla_breaches` | Scheduled, every 15 minutes |

Workers are defined in `tasks/worker.py`. Each task is isolated and must not depend on HTTP request state.

---

# Observability

| Signal | Tool |
|--------|------|
| Structured logs | Python `logging` with JSON formatter |
| Error tracking | Sentry (future) |
| Metrics | Prometheus (future) |
| AI tracing | LangSmith (future) |
| Request tracing | OpenTelemetry (future) |

Every request log includes: request ID, method, path, status code, response time, citizen ID (if authenticated).

---

# Security

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT Bearer token |
| Authorization | Role-based dependency injection |
| Password storage | bcrypt with configurable cost factor |
| Input validation | Pydantic v2 strict mode |
| SQL injection | SQLAlchemy ORM (parameterized queries) |
| Secret management | Environment variables, never in code |
| HTTPS | Enforced at infrastructure level |
| Rate limiting | Per-endpoint limits on sensitive routes |

---

# References

- [Authentication Specification](../specs/auth.md)
- [Report Specification](../specs/reports.md)
- [User Specification](../specs/users.md)
- [Department Specification](../specs/departments.md)
- [Database Specification](../specs/database.md)
- [AI Pipeline Specification](../specs/ai-pipeline.md)
- [API Specification](../specs/api.md)
- [Security Architecture](./security.md)
