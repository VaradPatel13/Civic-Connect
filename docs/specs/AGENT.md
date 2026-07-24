# AGENTS.md

# CivicConnect Multi-Agent System

> This document defines the architecture and contracts for the CivicConnect AI pipeline.
>
> It is the source of truth for every AI agent in the system.

---

# Purpose

The CivicConnect AI pipeline validates, enriches, classifies, routes, and audits citizen reports.

Goals

- Reliable
- Explainable
- Auditable
- Fault tolerant
- Government compliant

---

# Pipeline Version

Current Version

v1

Breaking changes require a version update.

---

# Architecture

```
Citizen Report

↓

Validation Supervisor

↓

Parallel Execution

├── Forensics
├── Classifier
├── Geo Validator
└── Moderator

↓

Enhancer

↓

Department Router

↓

Notifier

↓

Audit Recorder
```

Only the Supervisor controls execution.

Agents never invoke other agents directly.

---

# Design Principles

Every agent must be

- Stateless
- Deterministic where possible
- Independently testable
- Replaceable
- Observable

Agents communicate only through shared state.

---

# Shared State Contract

The supervisor owns the shared state.

Agents may read from it.

Agents may only modify their own output section.

Shared state contains

```
report

citizen

photos

validation

forensics

classification

geo_validation

moderation

enhancement

routing

notification

audit

metadata
```

Agents must never modify another agent's output.

---

# Agent Contracts

## 1 Validation Supervisor

Purpose

Validate incoming reports.

Input

- report
- citizen

Output

```
validation

valid

missing_fields

warnings
```

Failure

Reject invalid requests.

---

## 2 Forensics Agent

Purpose

Analyze uploaded photos.

Input

photos

Output

```
authentic

confidence

reason

regions
```

Confidence

0.70+

Fallback

Accept with warning.

---

## 3 Classification Agent

Purpose

Determine issue type.

Output

```
issue_type

urgency

tags

confidence
```

Confidence

0.60+

Fallback

Keyword classifier.

---

## 4 Geo Validator

Purpose

Validate coordinates.

Output

```
ward

zone

boundary

confidence
```

Fallback

Unknown ward.

Never invent locations.

---

## 5 Moderator

Purpose

Detect

- spam
- abuse
- profanity
- malicious content

Output

```
clean

flags

toxicity
```

Confidence

0.80+

Fallback

Manual review.

---

## 6 Enhancer

Purpose

Generate

- English translation
- summary
- department notes

Never modify original text.

---

## 7 Department Router

Purpose

Assign report.

Output

```
department

priority

sla
```

Fallback

General department.

---

## 8 Notifier

Purpose

Notify

- citizen
- department

Must never modify report state.

---

## 9 Audit Recorder

Purpose

Persist every decision.

Audit cannot be skipped.

---

# Agent Permissions

| Agent | Read | Write |
|--------|------|-------|
| Validation | report | validation |
| Forensics | photos | forensics |
| Classifier | report | classification |
| Geo | report | geo_validation |
| Moderator | report | moderation |
| Enhancer | report | enhancement |
| Router | classification | routing |
| Notifier | routing | notification |
| Auditor | everything | audit |

Agents never modify another agent's data.

---

# Confidence Rules

| Agent | Threshold |
|---------|----------|
| Forensics | 0.70 |
| Classifier | 0.60 |
| Moderator | 0.80 |
| Geo | Boundary validation |

Below threshold

Do not silently continue.

Use fallback or request review.

---

# Retry Policy

| Component | Retries |
|------------|---------|
| LLM | 3 |
| Cloudinary | 2 |
| Redis | 3 |
| Notifications | Queue retry |
| Database | Transaction policy |

---

# Failure Policy

Every failure must

- record error
- record execution time
- preserve partial outputs
- return structured result

Never crash the pipeline.

---

# Audit Requirements

Every execution stores

- report_id
- agent_name
- model_used
- execution_time
- confidence
- input_snapshot
- output_snapshot
- status
- error_snapshot
- created_at

Audit history is immutable.

---

# Human Review Rules

Manual review required when

- confidence below threshold
- suspected fraud
- unknown ward
- multiple department matches
- moderation failure
- policy violation

---

# Performance Budget

| Agent | Budget |
|---------|--------|
| Validation | <50ms |
| Geo | <150ms |
| Classifier | <2s |
| Forensics | <5s |
| Moderator | <2s |
| Router | <500ms |
| Notifier | <500ms |
| Auditor | <100ms |

---

# Security

Agents must never

- expose secrets
- expose JWT tokens
- expose passwords
- expose API keys
- expose personal information

PII must never appear in logs.

---

# Observability

Every execution records

- latency
- retries
- failures
- confidence
- model used

All metrics must be traceable.

---

# Testing Requirements

Every agent requires

- Unit tests
- Failure tests
- Timeout tests
- Fallback tests
- Integration tests

---

# Agent Independence

Agents

MUST NOT

- import another agent
- call another agent
- bypass supervisor
- modify shared state outside their section

Only the supervisor coordinates execution.

---

# Definition of Done

An agent is complete only if

- contract implemented
- fallback implemented
- tests pass
- audit logging implemented
- documentation updated
- performance budget satisfied

---

# Future Compatibility

New agents

Must

- follow shared state contract
- define permissions
- define fallback
- define confidence
- define tests
- define audit behavior

No breaking changes without version update.