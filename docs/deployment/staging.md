# Staging Deployment Guide

> Setup and deployment instructions for the CivicConnect staging environment.

---

# Overview

Staging mirrors the production environment and is used for pre-release validation, load testing, and client demonstrations.

---

# Staging Environment Topology

- **API & Workers**: Deployed via Docker Compose or ECS staging cluster.
- **Database**: AWS RDS PostgreSQL with PostGIS extension.
- **Cache**: AWS ElastiCache Redis.
- **Domain**: `https://staging-api.civicconnect.pmc.gov.in`

---

# Automated CI/CD Deployment

Staging deployments occur automatically when code is merged into the `develop` branch.

```yaml
# GitHub Actions Trigger
on:
  push:
    branches: [ develop ]
```

Steps executed:
1. Build & tag Docker images with commit SHA.
2. Run database migration (`alembic upgrade head`).
3. Deploy API services & Celery workers.
4. Run health check `/health` to confirm deployment stability.
