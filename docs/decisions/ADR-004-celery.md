# ADR-004: Selection of Celery + Redis for Background Processing

- **Status**: Accepted
- **Date**: 2026-07-23
- **Deciders**: Backend & Infrastructure Team

---

# Context

Report processing, AI pipeline invocation, SMS OTP delivery, and push notifications are long-running tasks. The FastAPI web server must return HTTP responses immediately (<500ms) without blocking on asynchronous AI execution or notification external APIs.

# Considered Options

1. **FastAPI BackgroundTasks**: Simple in-process background tasks, but lacks task persistence, worker scaling, retry policies, and monitoring across server restarts.
2. **ARQ / Asyncio Workers**: Lightweight async task queue, but has fewer ecosystem integrations and worker management tools.
3. **Celery + Redis Broker**: Robust distributed task queue standard in Python with rich retry mechanisms, dead-letter routing, and task monitoring (Flower).

# Decision

We selected **Celery with Redis** as the task queue infrastructure.

# Rationale

- **Decoupled Architecture**: Web API nodes remain lightweight while dedicated Celery workers execute AI agent workloads.
- **Robust Retry Policies**: Exponential backoff for network-flaky SMS and push notification API calls.
- **Scheduled / Periodic Tasks**: Native Celery Beat support for periodic SLA breach checking and OTP cleanup.
- **Proven Scalability**: Worker instances scale horizontally independently of API instances.

# Consequences

- **Positive**: Guaranteed background task execution, task monitoring, clean separation of API and heavy worker processes.
- **Negative**: Additional infrastructure components (Redis container and Celery processes).
