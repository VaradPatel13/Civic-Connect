# Local Deployment Guide

> Instructions for setting up and running the CivicConnect development environment locally.

---

# Prerequisites

- Docker Desktop & Docker Compose v2+
- Python 3.12+
- Node.js 20+ & `npm` / `npx`
- Expo Go app or Android/iOS Emulator

---

# Step-by-Step Setup

## 1. Clone Repository & Setup Environment

```bash
cp .env.example .env
```

Ensure `.env` contains local development defaults.

## 2. Start Infrastructure Containers

```bash
docker-compose up -d postgres redis
```

This starts:
- PostgreSQL 16 + PostGIS on `localhost:5432`
- Redis on `localhost:6379`

## 3. Run Database Migrations & Seeds

```bash
# Python environment active
alembic upgrade head
python -m backend.seeds.departments
```

## 4. Run Backend API & Celery Worker

```bash
# Terminal 1: FastAPI API server
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Celery worker
celery -A backend.tasks.worker worker --loglevel=info
```

## 5. Run Mobile App

```bash
cd app
npm install
npx expo start
```

Scan QR code with Expo Go or press `a` / `i` for Android / iOS emulator.
