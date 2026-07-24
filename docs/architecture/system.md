# System Architecture

> This document describes the overall technical architecture of CivicConnect.
>
> It serves as the primary architectural reference for developers and autonomous coding agents.
>
> Detailed implementation specifications are located under `docs/specs/`.

---

# Overview

CivicConnect is a production-grade civic engagement platform that enables citizens to report municipal issues through a mobile application while using AI agents to validate, classify, enrich, and route reports to the appropriate government department.

The platform follows a layered architecture with event-driven processing for long-running AI workloads.

---

# High-Level Architecture

```
                    Citizens
                        │
                        ▼
          React Native Mobile Application
                        │
                HTTPS / WebSocket
                        │
                        ▼
                  FastAPI Backend
                        │
        ┌───────────────┴────────────────┐
        │                                │
        ▼                                ▼
 PostgreSQL + PostGIS             Redis + Celery
        │                                │
        └───────────────┬────────────────┘
                        │
                        ▼
               LangGraph Supervisor
                        │
      ┌──────────────────────────────────┐
      │ Validation Supervisor            │
      │                                  │
      │  ├── Forensics                   │
      │  ├── Classifier                  │
      │  ├── Geo Validator               │
      │  ├── Moderator                   │
      │  ├── Enhancer                    │
      │  ├── Department Router           │
      │  ├── Notifier                    │
      │  └── Auditor                     │
      └──────────────────────────────────┘
                        │
                        ▼
               External Services

        Cloudinary
        NVIDIA NIM
        OpenRouter
        Firebase Cloud Messaging
        SMS Provider
        Email Provider
```

---

# Architectural Principles

The system is designed around the following principles.

## Separation of Concerns

Each layer has a single responsibility.

- Mobile handles presentation.
- Backend exposes APIs.
- Services contain business logic.
- Agents perform AI reasoning.
- Database stores persistent data.
- Infrastructure integrates external systems.

---

## Layered Architecture

```
Presentation

↓

API

↓

Application

↓

Domain

↓

Infrastructure
```

Each layer depends only on the layer beneath it.

---

## Event-Driven Processing

Heavy operations are executed asynchronously.

Examples

- AI image analysis
- LLM classification
- Notifications
- Email delivery
- SMS delivery
- Audit logging

Redis and Celery coordinate background processing.

---

# Mobile Architecture

Technology

- React Native
- Expo
- expo-router
- Zustand
- React Query
- i18next

Responsibilities

- Authentication
- Report creation
- Report tracking
- Offline support
- Push notifications
- Localization

The mobile application never communicates directly with external services.

All requests pass through the backend API.

---

# Backend Architecture

Technology

- FastAPI
- SQLAlchemy
- Pydantic
- Alembic

Responsibilities

- Authentication
- Authorization
- Validation
- Business logic
- Agent orchestration
- Database access
- API documentation

Business logic must never exist inside API route handlers.

---

# AI Architecture

The AI system uses LangGraph with a Supervisor pattern.

Supervisor

↓

Validation

↓

Parallel execution

- Forensics
- Classification
- Geo Validation
- Moderation

↓

Enhancement

↓

Department Routing

↓

Notification

↓

Audit

Only the Supervisor controls execution order.

Agents never communicate directly.

---

# Database Architecture

Technology

- PostgreSQL
- PostGIS

Database responsibilities

- Citizens
- Reports
- Photos
- Departments
- Wards
- Rewards
- Agent execution history
- Status logs

Every table uses UUID primary keys.

Spatial operations use PostGIS.

---

# Infrastructure Architecture

Infrastructure includes

- Docker
- Redis
- Celery
- Cloudinary
- Firebase Cloud Messaging
- Email provider
- SMS provider

Infrastructure services are accessed only through dedicated service modules.

---

# External Integrations

## Cloudinary

Responsibilities

- Image storage
- Image optimization
- CDN delivery

---

## NVIDIA NIM

Responsibilities

- Language reasoning
- Classification
- Summarization

---

## OpenRouter

Responsibilities

Fallback LLM provider.

---

## Firebase Cloud Messaging

Responsibilities

Push notifications.

---

## SMS Provider

Responsibilities

OTP delivery.

---

## Email Provider

Responsibilities

Transactional emails.

---

# Data Flow

Citizen submits report

↓

FastAPI validates request

↓

Database stores report

↓

Celery creates background task

↓

Supervisor starts pipeline

↓

Validation

↓

Parallel AI agents

↓

Enhancement

↓

Department routing

↓

Notifications

↓

Audit logging

↓

Citizen receives updates

---

# Security Architecture

Authentication

JWT access tokens

JWT refresh tokens

Password hashing

bcrypt

Authorization

Role-based permissions.

Validation

All incoming data is validated using Pydantic.

Secrets

Secrets are never stored in source control.

---

# Error Handling

Every layer must

- return structured errors
- log failures
- preserve audit history
- avoid exposing internal details

Failures in external services must degrade gracefully.

---

# Observability

The platform records

- request latency
- agent latency
- database performance
- retry counts
- failures
- audit events

Future integrations

- Sentry
- Prometheus
- Grafana
- LangSmith

---

# Repository Organization

```
app/

backend/

docs/

tests/

infrastructure/
```

Each directory has a single responsibility.

Cross-layer dependencies should be avoided.

---

# Scalability

The architecture is designed to support

- additional municipalities
- additional languages
- new AI agents
- new notification providers
- horizontal API scaling
- background worker scaling

without major architectural changes.

---

# Design Constraints

The system must prioritize

- maintainability
- reliability
- auditability
- security
- modularity

Performance improvements must never compromise correctness.

---

# Future Extensions

Planned future capabilities include

- Municipal staff portal
- Analytics dashboard
- AI-assisted report resolution
- Citizen reputation system
- Public transparency dashboard
- Multi-city deployment

These features should integrate without requiring major architectural redesign.