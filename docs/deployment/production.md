# Production Deployment Guide

> Production deployment guidelines, zero-downtime strategy, and operational security.

---

# Architecture Overview

Production is deployed across isolated availability zones with high availability enabled for database and Redis services.

```
Internet → Cloudflare WAF → Load Balancer → FastAPI App Nodes (Auto-Scaling)
                                              │
                                     ┌────────┴────────┐
                                     ▼                 ▼
                              RDS PostGIS        ElastiCache Redis
                                                       │
                                                       ▼
                                                Celery Workers
```

---

# Zero-Downtime Deployment Strategy

1. **Database Schema Migrations**: All Alembic migrations in production must be strictly **backward compatible** (add columns as nullable, multi-phase column deprecation).
2. **Rolling Code Deployment**: App nodes are updated sequentially behind the load balancer.
3. **Health Checks**: Target health endpoint `/health` must verify DB connectivity and Redis status before serving traffic.

---

# Secrets & Environment Configuration

- Secrets managed through HashiCorp Vault / Doppler.
- Plaintext secrets must never be stored in server instance storage or container images.
