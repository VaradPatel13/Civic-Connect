# Database Specification

> This document defines the database architecture for CivicConnect.
>
> It is the authoritative specification for SQLAlchemy models, Alembic migrations, and database-related decisions.

---

# Overview

Database Engine

- PostgreSQL 16+

Extensions

- PostGIS
- pgcrypto
- uuid-ossp (optional)

ORM

- SQLAlchemy 2.x

Migration Tool

- Alembic

Primary Key Strategy

- UUID v4

Timezone

- UTC

Character Encoding

- UTF-8

---

# Design Principles

The database must be:

- Normalized
- Auditable
- Geospatially aware
- Scalable
- Backward compatible

Every schema change must be introduced through Alembic migrations.

---

# Naming Conventions

Tables

snake_case plural

Examples

```
citizens
reports
photos
departments
```

Columns

snake_case

Examples

```
created_at
updated_at
phone_number
preferred_language
```

Foreign Keys

```
citizen_id
report_id
department_id
```

Indexes

```
idx_reports_status

idx_reports_created_at

idx_agent_execution_report
```

---

# Common Columns

Every primary table should include

```
id

created_at

updated_at
```

Soft-delete tables additionally include

```
deleted_at
```

---

# UUID Strategy

Every entity uses

```
UUID PRIMARY KEY
```

Advantages

- Globally unique
- Safe for distributed systems
- Difficult to enumerate
- Suitable for future multi-city deployments

---

# Tables

## citizens

Purpose

Citizen accounts.

Key fields

- phone
- email
- password_hash
- display_name
- preferred_language
- points
- is_active

Relationships

- reports
- rewards
- otp_codes

---

## otp_codes

Purpose

OTP verification.

Relationships

Many OTP records belong to one citizen.

Rules

- Expire automatically
- Never reused
- One-time verification

---

## wards

Purpose

PMC administrative boundaries.

Spatial Data

```
MULTIPOLYGON
```

Contains

- ward_name
- ward_number
- zone

---

## departments

Purpose

Municipal departments.

Contains

- department_name
- category
- contact_email
- contact_phone
- jurisdiction_geometry

---

## reports

Purpose

Citizen issue reports.

Contains

- issue_type
- description
- translated_description
- summary
- language
- status
- urgency
- location
- ward
- timestamps

Relationships

- citizen
- photos
- assignments
- status_logs
- agent_executions

---

## photos

Purpose

Store uploaded report photos.

Contains

- cloudinary_url
- public_id
- forensic_score
- original_hash

One report may contain multiple photos.

---

## assignments

Purpose

Track department assignment.

Contains

- report
- department
- assigned_at
- resolved_at
- assigned_by

---

## status_logs

Purpose

Immutable status history.

Examples

Pending

↓

Verified

↓

Assigned

↓

Resolved

Never overwrite status history.

---

## rewards

Purpose

Citizen reward points.

Contains

- points
- reason
- report

---

## agent_executions

Purpose

Complete audit trail.

Every AI decision generates one execution record.

Contains

- report
- agent
- confidence
- execution_time
- input_snapshot
- output_snapshot
- status
- error_snapshot

Audit history is immutable.

---

# Relationships

Citizen

↓

Reports

↓

Photos

↓

Assignments

↓

Status Logs

↓

Agent Executions

↓

Rewards

---

# Geospatial Strategy

PostGIS stores

- Ward boundaries
- Department boundaries
- Citizen report locations

Spatial operations include

- ST_Contains
- ST_Intersects
- Distance calculations

All coordinates use

```
EPSG:4326
```

---

# Status Lifecycle

```
pending

↓

processing

↓

verified

↓

assigned

↓

in_progress

↓

resolved
```

Alternative

```
rejected
```

Status transitions must be validated by the application.

---

# Index Strategy

Indexes should exist for

- report status
- report creation date
- citizen phone
- citizen email
- report location
- ward lookup
- agent executions
- assignment status

Additional indexes should be introduced only when justified by query analysis.

---

# Constraints

Examples

Phone numbers unique.

Emails unique.

Points cannot be negative.

Confidence values

```
0.0 <= confidence <= 1.0
```

Foreign keys must enforce referential integrity.

---

# Soft Delete Policy

Core transactional tables

Do NOT use soft deletes.

Reference tables

May support soft deletion when necessary.

Audit tables

Never delete records.

---

# Audit Requirements

Every important action must be traceable.

Audit includes

- authentication
- report submission
- status updates
- assignments
- AI decisions

Audit history must never be modified.

---

# Migration Strategy

Every schema change requires

1. Updated specification
2. Alembic migration
3. Review
4. Testing

Schema changes must be backward compatible whenever possible.

---

# Backup Strategy

Production database requires

- Daily backups
- WAL archiving
- Point-in-time recovery

Backup procedures must be tested periodically.

---

# Performance Goals

Typical API query

<100 ms

Geospatial query

<300 ms

Agent execution insert

<50 ms

Indexes should support these targets.

---

# Security

Sensitive fields

- password_hash
- refresh tokens
- OTP codes

Must never be exposed through public APIs.

Database access follows the principle of least privilege.

---

# Future Extensions

Database design should support

- Multiple municipalities
- Department dashboards
- Citizen reputation
- Analytics
- Public reporting
- AI model history

without requiring major schema redesign.
