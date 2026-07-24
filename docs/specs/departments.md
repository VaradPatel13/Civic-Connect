# Department Specification

> This document defines the department management system for CivicConnect.
>
> It serves as the authoritative specification for department definitions, routing rules, SLA policies, organizational structure, and integration contracts.

---

# Overview

The department system manages the routing of citizen reports to the appropriate Pune Municipal Corporation (PMC) department. Every verified report is assigned to exactly one department based on issue type, geographic ward, and priority level.

Departments are pre-seeded reference data. They are not created by citizens.

---

# Objectives

The department system must provide:

- Accurate report routing based on category and location
- Hierarchical organizational structure
- Category-to-department mapping
- SLA enforcement per priority level
- Escalation paths when SLAs are breached
- Performance tracking per department
- Location-aware assignment using PostGIS

---

# Department Hierarchy

```
Pune Municipal Corporation (PMC)
        │
        ▼
    Departments
        │
        ▼
      Teams
        │
        ▼
   Individuals
```

Departments are the primary routing targets. Teams and individuals are internal to each department and are not managed by this system in the initial release.

---

# Core Departments

The following departments are supported in the initial release:

| Code | Department Name | Primary Categories |
|------|-----------------|--------------------|
| `ROADS` | Roads & Infrastructure | Potholes, road damage, footpaths |
| `WATER` | Water Supply | Water leaks, low pressure, pipe bursts |
| `DRAIN` | Sewerage & Drainage | Drain blockage, sewer overflow |
| `ELEC` | Electrical Works | Streetlight failures, electrical hazards |
| `HEALTH` | Public Health | Disease control, sanitation inspection |
| `SANIT` | Sanitation & Waste | Garbage collection, illegal dumping |
| `FIRE` | Fire Safety | Fire hazards, fire hydrant issues |
| `BUILD` | Building & Land Use | Encroachment, illegal construction |
| `TRAFF` | Traffic & Transport | Signal failures, road markings |
| `PARKS` | Parks & Greenery | Tree hazards, park maintenance |
| `ADMIN` | General Administration | Uncategorized, escalation fallback |

The `ADMIN` department is the fallback when the AI routing agent cannot determine a specific department with sufficient confidence.

---

# Department Attributes

Each department record contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `code` | string | Unique short identifier (e.g., `ROADS`) |
| `name` | string | Full department name |
| `description` | string | Description of responsibilities |
| `contact_email` | string | Official contact email |
| `contact_phone` | string | Official contact phone |
| `operating_hours` | string | Standard operating hours (e.g., `Mon–Fri 09:00–17:00`) |
| `sla_low_days` | integer | SLA for low-priority reports (days) |
| `sla_medium_days` | integer | SLA for medium-priority reports (days) |
| `sla_high_hours` | integer | SLA for high-priority reports (hours) |
| `sla_critical_hours` | integer | SLA for critical-priority reports (hours) |
| `jurisdiction_geometry` | geometry | PostGIS MULTIPOLYGON of operational area |
| `is_active` | boolean | Whether the department is accepting new reports |
| `created_at` | timestamp | Record creation time (UTC) |
| `updated_at` | timestamp | Last modification time (UTC) |

---

# Routing Rules

The Department Router agent assigns a report to a department using the following priority order:

1. **Issue category** — the primary routing signal. Each issue category maps to a default department.
2. **Ward** — some categories may have ward-specific overrides.
3. **Urgency** — critical-priority reports may trigger a different department branch or escalation path.
4. **Department availability** — if the resolved department is inactive, the report routes to `ADMIN`.

Category-to-department mapping is maintained in a routing table seeded in the database. It must not be hardcoded in application logic.

---

# Category-to-Department Mapping (Initial)

| Category | Default Department |
|----------|--------------------|
| Roads | `ROADS` |
| Water Supply | `WATER` |
| Drainage | `DRAIN` |
| Street Lighting | `ELEC` |
| Public Health | `HEALTH` |
| Waste Management | `SANIT` |
| Parks | `PARKS` |
| Encroachment | `BUILD` |
| Traffic Infrastructure | `TRAFF` |
| Other | `ADMIN` |

---

# SLA Definitions

Standard SLA response targets by priority level:

| Priority | Target Response |
|----------|-----------------|
| Low | 7 calendar days |
| Medium | 3 calendar days |
| High | 24 hours |
| Critical | 4 hours |

SLA timers start from the moment of department assignment, not report submission.

SLA breach triggers an escalation event. See the Escalation Rules section below.

---

# Department Capacity

Each department tracks operational capacity metrics:

- Active report count (assigned, in-progress)
- Weekly resolution capacity (configurable per department)
- Staff allocation (out of scope for v1)
- Backlog count

Capacity data is used for observability and analytics. It does not affect routing in the initial release.

---

# Location Mapping

Departments are mapped to geographic areas using PostGIS:

- **Ward boundaries** — each ward maps to one or more departments
- **Department jurisdiction geometry** — a MULTIPOLYGON defining the department's operational area
- **Nearest department routing** — when no exact ward match exists, the system routes to the nearest matching department

PostGIS spatial operations used:

- `ST_Contains` — check if a report location falls within a ward boundary
- `ST_Intersects` — determine department jurisdiction overlap
- `ST_Distance` — fallback nearest-department routing

All spatial data uses `EPSG:4326` (WGS 84).

---

# Escalation Rules

## Escalation Paths

```
Department
    │
    ▼
Section Head
    │
    ▼
Department Supervisor
    │
    ▼
PMC General Administration
```

## Escalation Triggers

| Trigger | Action |
|---------|--------|
| SLA breach | Escalate to section head and log event |
| Report complexity flag | Notify supervisor |
| Priority increase | Re-evaluate routing |
| Department inactive | Reassign to `ADMIN` |
| Duplicate of unresolved report | Link reports, notify department |

Escalation events must be recorded in the audit log.

---

# Audit Requirements

Every department assignment records:

| Field | Description |
|-------|-------------|
| `report_id` | The assigned report |
| `department_id` | The target department |
| `assigned_at` | Timestamp of assignment |
| `routing_reason` | AI agent decision rationale |
| `confidence` | Routing confidence score (0.0–1.0) |
| `assigned_by` | Agent name or `system` |
| `escalated` | Whether the report was escalated |
| `escalation_reason` | Reason for escalation (if applicable) |

Assignment records are immutable. Re-routing creates a new assignment record.

---

# Performance Monitoring

Metrics tracked per department:

| Metric | Description |
|--------|-------------|
| Assignment accuracy | % of reports correctly routed (validated by manual review sample) |
| Average response time | Time from assignment to first status update |
| Resolution rate | % of reports resolved within SLA |
| SLA breach rate | % of reports breaching SLA targets |
| Citizen satisfaction | Post-resolution feedback score (future) |

These metrics feed the observability dashboard.

---

# Integration Points

| Integration | Purpose |
|-------------|---------|
| Department Router agent | Primary consumer of routing rules |
| Geo Validation agent | Provides ward and zone context |
| Notification service | Delivers assignment notifications to citizens |
| Audit Recorder | Persists assignment events |
| Admin dashboard | Displays department load and performance (future) |

---

# API Endpoints

```
GET    /departments

GET    /departments/{id}

GET    /departments/{id}/reports

GET    /departments/{id}/stats
```

Department records are read-only through the public API.
Administrative endpoints for department management require administrator role.

---

# Testing Requirements

Department system tests must cover:

- Category-to-department mapping
- Ward-based routing
- Fallback to `ADMIN` when no match
- Inactive department handling
- Escalation trigger logic
- SLA threshold calculations
- Geospatial routing queries
- Audit record creation on assignment

---

# Future Enhancements

Planned capabilities not in scope for the initial release:

- Department officer portal (web dashboard)
- Officer-level assignment within a department
- Real-time workload balancing
- Automated SLA breach notifications to department heads
- Cross-department collaboration for complex issues
- Ward-level performance heat maps

Future features must not require changes to the core routing contract.
