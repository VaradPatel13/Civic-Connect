# Infrastructure

This directory contains Docker Compose configuration for local development infrastructure.

## Services

- PostgreSQL: `postgis/postgis:13-3.2` on port `5432`
  - User: `app`
  - Password: `app`
  - Database: `civicconnect`
- Redis: `redis:7-alpine` on port `6379`

## Usage

From this directory:

```bash
docker compose up -d
```

Validate health:

```bash
docker compose ps
docker compose run --rm postgres pg_isready -U app -d civicconnect
docker