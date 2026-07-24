# User Specification

> This document defines the user management system for CivicConnect.
>
> It serves as the authoritative specification for citizen and administrative user flows, authentication, authorization, profile management, privacy, and testing requirements.

---

# Overview

The user system manages citizen profiles, authentication state, and access control across all platform features.

Multiple user types exist with distinct permissions. The primary user type is the citizen. Administrative and departmental roles are introduced to support platform management and report resolution workflows.

---

# Objectives

The user system must provide:

- Secure, verifiable citizen authentication
- Profile management for personal and preference data
- Role-based access control (RBAC) at every endpoint
- Multi-factor verification via OTP
- Privacy protection and data minimization
- Complete audit trail of user actions

---

# User Types

## Citizen

The primary platform user. A citizen is a verified Pune resident.

**Capabilities:**

- Submit civic reports
- Track own report status
- Receive push, SMS, and email notifications
- Earn and redeem reward points
- View own profile and history
- Update personal preferences

**Constraints:**

- Cannot view other citizens' reports
- Cannot modify verified or assigned reports
- Cannot access administrative functions

---

## Administrator

A PMC staff member with full system access.

**Capabilities:**

- Full read/write access to all reports
- User account management (activate, deactivate)
- Department configuration
- Reward policy management
- Analytics and performance dashboards
- Audit log access

---

## Department Officer

A PMC departmental staff member responsible for resolving assigned reports.

**Capabilities:**

- View reports assigned to their department
- Update report status
- Add resolution notes and evidence images
- Communicate with citizens via the platform
- Escalate or reassign reports (if permitted)

**Constraints:**

- Cannot view reports outside their department
- Cannot manage user accounts

---

## Moderator

A content reviewer responsible for flagging inappropriate submissions.

**Capabilities:**

- View all submitted reports
- Flag reports for review
- Manage policy violations
- Escalate to administrator

---

# Permissions Matrix

| Action | Citizen | Officer | Moderator | Admin |
|--------|---------|---------|-----------|-------|
| Submit report | ✅ | ❌ | ❌ | ✅ |
| View own reports | ✅ | ❌ | ❌ | ✅ |
| View all reports | ❌ | ✅ (dept) | ✅ | ✅ |
| Update report status | ❌ | ✅ (dept) | ❌ | ✅ |
| View own profile | ✅ | ✅ | ✅ | ✅ |
| Edit own profile | ✅ | ✅ | ✅ | ✅ |
| Manage users | ❌ | ❌ | ❌ | ✅ |
| Access audit logs | ❌ | ❌ | ❌ | ✅ |
| View analytics | ❌ | ❌ | ❌ | ✅ |
| Flag content | ❌ | ❌ | ✅ | ✅ |
| View reward history | ✅ | ❌ | ❌ | ✅ |

---

# Authentication

Refer to `docs/specs/auth.md` for the complete authentication specification.

Summary of supported methods:

| Method | Status |
|--------|--------|
| Phone number + password | ✅ Supported |
| OTP verification (SMS) | ✅ Supported |
| Email + password | Planned |
| Social login | Future |
| Government SSO | Future |
| Biometric (mobile) | Future |

JWT access tokens are used for all API requests.

- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days (rolling)

---

# Citizen Profile

Each citizen account contains:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | ✅ | Primary key |
| `name` | string | ✅ | Full name |
| `phone` | string | ✅ | Unique, used for login and OTP |
| `email` | string | ❌ | Optional, unique if provided |
| `password_hash` | string | ✅ | bcrypt hash, never exposed |
| `preferred_language` | enum | ✅ | `en`, `hi`, `mr` |
| `points` | integer | ✅ | Reward points balance, ≥ 0 |
| `is_active` | boolean | ✅ | Account activation status |
| `is_verified` | boolean | ✅ | OTP verification status |
| `push_token` | string | ❌ | FCM push notification token |
| `notification_preferences` | JSONB | ❌ | Channel and event preferences |
| `created_at` | timestamp | ✅ | UTC |
| `updated_at` | timestamp | ✅ | UTC |

---

# Registration Flow

```
Citizen enters name, phone, password
        │
        ▼
Backend validates input
        │
        ▼
Check phone uniqueness
        │
        ▼
Create unverified account
        │
        ▼
Generate and send OTP (SMS)
        │
        ▼
Citizen submits OTP
        │
        ▼
Verify OTP
        │
        ▼
Mark account as verified
        │
        ▼
Issue JWT access token + refresh token
        │
        ▼
Return citizen profile
```

An unverified account cannot submit reports or access protected endpoints.

---

# Password Policy

Minimum requirements:

- Minimum 8 characters
- At least one uppercase letter (A–Z)
- At least one lowercase letter (a–z)
- At least one numeric character (0–9)
- At least one special character (`!@#$%^&*`)

Password storage:

- Stored as bcrypt hash only
- Plain-text password is never persisted or logged
- Password comparison uses constant-time hash comparison

Password reset flow is defined in `docs/specs/auth.md`.

---

# Session Management

The system supports multiple concurrent devices per citizen.

Each session record stores:

| Field | Description |
|-------|-------------|
| `id` | UUID session identifier |
| `citizen_id` | Owning citizen |
| `refresh_token_hash` | Hashed refresh token |
| `device_id` | Client-provided device identifier |
| `platform` | `ios`, `android`, or `web` |
| `app_version` | Application version string |
| `last_active_at` | Last activity timestamp |
| `created_at` | Session creation timestamp |
| `revoked_at` | Revocation timestamp (null if active) |

Session operations:

- **Logout single device** — revoke specific session
- **Logout all devices** — revoke all sessions for the citizen
- **Idle timeout** — sessions inactive beyond the configured threshold are revoked automatically

---

# Authorization

Authorization is enforced at every protected endpoint using a dependency injection pattern in FastAPI.

Rules:

- Every protected endpoint declares the required role
- Role is extracted from the JWT access token payload
- Mismatched roles return `403 Forbidden`
- Missing or invalid tokens return `401 Unauthorized`

Role hierarchy for admin override:

```
Admin > Moderator > Officer > Citizen
```

Admins can perform any action any lower role can perform.

---

# User Preferences

Configurable settings per citizen:

| Preference | Type | Default | Description |
|------------|------|---------|-------------|
| `preferred_language` | enum | `en` | UI and notification language |
| `notification_push` | boolean | `true` | Enable push notifications |
| `notification_sms` | boolean | `true` | Enable SMS notifications |
| `notification_email` | boolean | `false` | Enable email notifications |
| `location_tracking` | boolean | `true` | Allow background location access |
| `marketing_opt_in` | boolean | `false` | Opt into platform updates |

Preference updates take effect immediately.

---

# Privacy Controls

CivicConnect enforces the following data protection requirements:

| Requirement | Implementation |
|-------------|----------------|
| Data minimization | Only collect data needed for core function |
| PII protection | `phone`, `email`, `password_hash` never exposed in API responses |
| Right to deletion | Account deactivation with data anonymization on request |
| Data export | Export citizen data in machine-readable format on request |
| Audit trail | All data access and modification is logged |

Citizen personal information is never shared with external services except:

- OTP SMS delivery (phone number only)
- Push notification delivery (FCM push token only)

---

# Audit Requirements

The following user actions are logged:

| Event | Logged Fields |
|-------|--------------|
| Registration | `citizen_id`, timestamp, IP |
| OTP request | `citizen_id`, timestamp, channel |
| OTP verification | `citizen_id`, timestamp, outcome |
| Login | `citizen_id`, timestamp, IP, device, outcome |
| Logout | `citizen_id`, timestamp, session |
| Failed login | timestamp, IP, device, attempt count |
| Profile update | `citizen_id`, timestamp, changed fields |
| Report submission | `citizen_id`, `report_id`, timestamp |
| Points transaction | `citizen_id`, delta, reason, timestamp |
| Admin action | `admin_id`, `target_id`, action, timestamp |

Audit records are immutable and retained for the platform's operational lifetime.

---

# Performance Targets

| Operation | Target |
|-----------|--------|
| User lookup by ID | < 20 ms |
| User lookup by phone | < 30 ms |
| Authentication (login) | < 200 ms |
| Profile update | < 100 ms |
| Token validation | < 10 ms |

---

# API Endpoints

```
GET    /users/me

PATCH  /users/me

GET    /users/me/reports

GET    /users/me/rewards

PATCH  /users/me/preferences

DELETE /users/me

GET    /admin/users                (admin only)

GET    /admin/users/{id}           (admin only)

PATCH  /admin/users/{id}/status    (admin only)
```

Detailed request and response schemas are defined in the API documentation.

---

# Testing Requirements

The user system must include tests for:

- Registration with valid and invalid data
- Duplicate phone and email rejection
- OTP generation, validation, and expiry
- Login success and failure scenarios
- JWT issuance and validation
- Refresh token rotation
- Session revocation (single and all devices)
- Role-based access enforcement at every endpoint
- Profile update validation
- Password policy enforcement
- Audit record creation for each event
- PII non-exposure in API responses

---

# Future Enhancements

| Feature | Notes |
|---------|-------|
| Biometric login | Via Expo LocalAuthentication |
| Social login | Google, Apple Sign In |
| Government identity | Aadhaar-linked verification |
| Multi-factor authentication | TOTP support |
| Citizen reputation score | Based on report quality and resolution |
| Profile photo | Cloudinary-hosted avatar |
| Public activity profile | Opt-in transparency page |

All future enhancements must remain backward compatible with the existing authentication and authorization system.
