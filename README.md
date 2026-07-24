# CivicConnect

> AI-powered civic issue reporting platform for the Pune Municipal Corporation (PMC).

CivicConnect enables citizens to report civic issues such as potholes, garbage, water leaks, drainage problems, and streetlight failures through a mobile application. An AI-powered backend validates reports, classifies issues, routes them to the correct municipal department, and provides end-to-end status tracking.

---

# Project Status

**Current Phase**

Repository Setup

Current Milestone

✅ Repository Skeleton

Next Milestone

Project Configuration

---

# Vision

CivicConnect aims to improve communication between citizens and municipal departments by providing:

- AI-assisted report validation
- Intelligent department routing
- Real-time report tracking
- Transparent audit history
- Offline-first mobile experience
- Multi-language support (Marathi, Hindi, English)

---

# Architecture

```
React Native (Expo)

↓

FastAPI Backend

↓

LangGraph Agent Pipeline

↓

PostgreSQL + PostGIS

↓

Redis + Celery

↓

Cloudinary / FCM / External Services
```

Complete architecture documentation is available in:

```
docs/architecture/
```

---

# Technology Stack

## Mobile

- React Native
- Expo
- expo-router
- Zustand
- React Query
- i18next

## Backend

- FastAPI
- SQLAlchemy
- Pydantic v2
- Alembic

## AI

- LangGraph
- NVIDIA NIM
- OpenRouter

## Database

- PostgreSQL
- PostGIS

## Infrastructure

- Redis
- Celery
- Docker
- GitHub Actions

---

# Repository Structure

```
civic-connect/

app/
backend/
tests/
docs/
infrastructure/

README.md
CLAUDE.md
AGENTS.md
PLAN.md
```

Detailed architecture:

```
docs/architecture/system.md
```

---

# Documentation

| File | Purpose |
|------|----------|
| README.md | Project overview |
| CLAUDE.md | Autonomous development rules |
| AGENTS.md | AI pipeline contracts |
| PLAN.md | Project roadmap |
| docs/specs | Technical specifications |
| docs/architecture | System architecture |
| docs/decisions | Architecture Decision Records |

---

# Development Workflow

Every feature follows the same lifecycle.

```
Understand

↓

Plan

↓

Design

↓

Implement

↓

Test

↓

Review

↓

Merge
```

No implementation should begin without an approved plan.

---

# Milestones

## Milestone 1

Repository Skeleton

Status

Complete

---

## Milestone 2

Project Configuration

- Python project
- React Native project
- Formatting
- Linting
- Type checking
- Environment configuration

---

## Milestone 3

Database

- PostgreSQL
- SQLAlchemy
- Alembic
- PostGIS

---

## Milestone 4

Infrastructure

- Docker
- Local development
- Redis
- Celery

---

## Milestone 5

CI/CD

GitHub Actions

---

## Milestone 6

Backend API

---

## Milestone 7

Mobile Application

---

## Milestone 8

AI Agent Pipeline

---

# Core Principles

The project prioritizes:

- Maintainability
- Reliability
- Simplicity
- Auditability
- Security
- Performance

Every architectural decision should support these principles.

---

# Contributing

Before contributing:

1. Read `CLAUDE.md`
2. Read `AGENTS.md`
3. Review the relevant specification in `docs/specs`
4. Review related architecture documents
5. Create a development plan

---

# Coding Standards

- Python 3.12+
- TypeScript Strict Mode
- Ruff
- MyPy
- ESLint
- Prettier

All checks must pass before code review.

---

# Testing

The project includes:

- Unit Tests
- Integration Tests
- End-to-End Tests

Bug fixes must include regression tests.

---

# Security

Security requirements include:

- JWT authentication
- Secure password hashing
- Input validation
- Audit logging
- Principle of least privilege

Sensitive information must never be committed to the repository.

---

# License

Private Repository

Confidential – CivicConnect

Unauthorized distribution or reproduction is prohibited.