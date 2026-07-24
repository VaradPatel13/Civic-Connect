# API Specification

> This document defines the CivicConnect REST API.
>
> It serves as the authoritative source for all API endpoints, request/response schemas, and authentication.

---

# Overview

The API provides programmatic access to CivicConnect for mobile apps, web clients, and backend services.

All endpoints are RESTful and return JSON.

---

# Base URL

Production: `https://api.civicconnect.in`
Staging: `https://staging-api.civicconnect.in`
Development: `http://localhost:8000`

---

# Authentication

All API requests require a valid JWT access token.

Authorization header required:

```
Authorization: Bearer <access_token>
```

---

# Endpoints

## Authentication

```
POST /auth/login

POST /auth/refresh

POST /auth/logout

POST /auth/register

POST /auth/verify-otp
```

## Users

```
GET /users/me

PATCH /users/me

DELETE /users/me

GET /users/me/preferences

PATCH /users/me/preferences
```

## Reports

```
GET /reports

POST /reports

GET /reports/{id}

PATCH /reports/{id}

DELETE /reports/{id}

GET /reports/{id}/history

GET /reports/{id}/photos
```

## Notifications

```
GET /notifications

GET /notifications/{id}

PATCH /notifications/{id}/read

PATCH /notifications/read-all

DELETE /notifications/{id}
```

## Rewards

```
GET /rewards

GET /rewards/history

POST /rewards/redeem

GET /rewards/balance
```

## Departments

```
GET /departments

GET /departments/{id}

GET /departments/sla
```

## Admin (Protected)

```
GET /admin/reports

PATCH /admin/reports/{id}/status

GET /admin/users

GET /admin/analytics

POST /admin/departments
```

---

# Request/Response Schema

Each endpoint defines:

- Request schema (for POST/PATCH)
- Response schema
- Status codes
- Error responses
- Examples

---

# Error Responses

Standard error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  }
}
```

---

# Rate Limiting

Rate limits (default):

- Auth endpoints: 10 requests/minute
- Standard endpoints: 100 requests/minute
- Bulk endpoints: 10 requests/minute

Rate limit headers provided:

- X-RateLimit-Limit
- X-RateLimit-Remaining
- X-RateLimit-Reset

---

# Versioning

API version: v1

Current version in URL: `/api/v1/`

---

# Documentation Links

- Authentication: docs/specs/auth.md
- Reports: docs/specs/reports.md
- Notifications: docs/specs/notifications.md
- Users: docs/specs/users.md
- Rewards: docs/specs/rewards.md
- Departments: docs/specs/departments.md

---

