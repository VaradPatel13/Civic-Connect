# Security Architecture

> This document defines the security architecture and compliance policies for CivicConnect.

---

# Principles

1. **Defense in Depth**: Security controls applied at network, app, data, and agent layers.
2. **Least Privilege**: Minimal permissions for API keys, DB roles, and user roles.
3. **Data Protection & Privacy**: PII encrypted at rest and sanitized in logs.
4. **Zero Trust Integration**: All requests authenticated via JWT and authorization checks.

---

# Threat Model & Mitigations

| Threat | Risk Level | Mitigation Strategy |
|--------|------------|---------------------|
| AI Injection / Prompt Hacking | High | Strict Pydantic parsing, guardrail agents, isolated agent state. |
| Fake / Manipulated Images | High | Forensics agent checks metadata, hashes, and AI artifact signatures. |
| Spam & Moderation Abuse | Medium | Moderation agent + rate limiting on API endpoints. |
| Unauthorized Access | Critical | Short-lived JWT access tokens + refresh token rotation + RBAC dependencies. |
| Data Interception | Critical | HTTPS everywhere, TLS 1.3 enforced for DB/Redis connections. |
| Direct DB Exposure | High | DB strictly isolated inside Docker network; zero public access. |

---

# Authentication & Authorization

- **JWT Auth**: Access tokens (15m expiration, algorithm HS256/RS256) + Refresh tokens (7d).
- **Password Policy**: Hashed via `bcrypt` (work factor 12). Plaintext never logged or stored.
- **RBAC**: Dependency injection enforcing `Citizen`, `Department Officer`, `Moderator`, `Admin`.

---

# Data Security & Encryption

- **In-Transit**: TLS 1.3 for all HTTP/WS endpoints and internal Redis/PostgreSQL channels.
- **At-Rest**: PostgreSQL column-level encryption (`pgcrypto`) for PII like mobile numbers.
- **Secrets Management**: Loaded exclusively via `.env` / Environment variables into Pydantic Settings.

---

# Logging & Audit Integrity

- **PII Scrubbing**: Regex scrubbers on logging output to sanitize passwords, OTPs, and tokens.
- **Immutable Audit Trail**: `agent_executions` and `status_logs` tables append-only.

---

# Compliance & Privacy Controls

- GDPR / Digital Personal Data Protection (DPDP) ready.
- Right to account deletion / anonymization API support.
