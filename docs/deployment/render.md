# Render Deployment Guide for CivicConnect Backend

> Complete step-by-step guide for deploying the CivicConnect FastAPI backend, PostgreSQL (with PostGIS), and Redis onto Render.

---

## Architecture Overview on Render

```
                                  ┌───────────────────────────────┐
                                  │      Render Web Service       │
Mobile / Web Frontend ──HTTPS───► │   FastAPI Backend (Uvicorn)   │
                                  │    Health Check: /health      │
                                  └──────────────┬────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
          ┌───────────────────────────┐                     ┌───────────────────────────┐
          │  Render Managed Postgres  │                     │   Render Key-Value Store  │
          │    (PostGIS Extension)    │                     │          (Redis)          │
          └───────────────────────────┘                     └───────────────────────────┘
```

---

## Method 1: Infrastructure as Code via Render Blueprint (Recommended)

CivicConnect includes a pre-configured `render.yaml` Blueprint file at the repository root.

### Step 1: Push Repository to GitHub
Ensure all recent changes are pushed to your GitHub repository:
```bash
git add .
git commit -m "feat: add render deployment setup"
git push origin main
```

### Step 2: Create New Blueprint Project on Render
1. Log into your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub account and select your **CivicConnect** repository.
4. Render will detect `render.yaml` and automatically provision:
   - **`civicconnect-api`** (FastAPI Web Service)
   - **`civicconnect-db`** (PostgreSQL Database)
   - **`civicconnect-redis`** (Redis Key-Value Cache)
5. Click **Apply**.

---

## Method 2: Manual Web Service Setup

If you prefer provisioning components manually in the Render UI:

### 1. Provision PostgreSQL Database
1. Go to Render Dashboard -> **New +** -> **PostgreSQL**.
2. Name: `civicconnect-db`
3. Database: `civicconnect`
4. User: `civic_user`
5. Click **Create Database**.
6. Copy the **Internal Database URL** (e.g. `postgres://civic_user:pass@dpg-xxx:5432/civicconnect`).

### 2. Enable PostGIS Extension
Connect to your database via Render Web Shell or local `psql` using the **External Database URL**, then execute:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 3. Provision Redis Instance
1. Go to Render Dashboard -> **New +** -> **Redis / Key-Value**.
2. Name: `civicconnect-redis`
3. Click **Create Redis**.
4. Copy the **Internal Redis URL** (e.g. `redis://red-xxx:6379`).

### 4. Provision FastAPI Web Service
1. Go to Render Dashboard -> **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Settings:
   - **Name**: `civicconnect-api`
   - **Environment**: `Python`
   - **Build Command**: `./scripts/render_build.sh`
   - **Pre-deploy Command**: `alembic upgrade head`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

---

## Environment Variables Configuration

Set the following Environment Variables under Web Service -> **Environment**:

| Variable Name | Example / Description | Auto-Configured in Blueprint? |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://civic_user:...@dpg-xxx:5432/civicconnect` | Yes |
| `REDIS_URL` | `redis://red-xxx:6379` | Yes |
| `JWT_SECRET` | `your-secure-random-secret` | Yes (Auto-generated) |
| `JWT_ALGORITHM` | `HS256` | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Yes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Yes |
| `AI_PROVIDER` | `nvidia_nim` (or `openai` / `openrouter`) | Yes |
| `NVIDIA_API_KEY` | `nvapi-xxxxxxxxxxxx` | No (Set manually) |
| `CLOUDINARY_URL` | `cloudinary://api_key:secret@cloud_name` | No (Set manually) |

> [!NOTE]
> `backend/core/config.py` automatically converts standard `postgres://` or `postgresql://` connection strings into `postgresql+asyncpg://` to prevent driver scheme errors.

---

## Verification & Monitoring

### 1. Health Check
Once deployment finishes, open your service URL in a browser or test via curl:
```bash
curl https://civicconnect-api.onrender.com/health
```
Expected output:
```json
{
  "status": "healthy",
  "service": "CivicConnect"
}
```

### 2. Swagger API Documentation
Access the interactive OpenAPI interface at:
`https://civicconnect-api.onrender.com/docs`

### 3. Connect Mobile Application
In your mobile project configuration (`.env`):
```env
EXPO_PUBLIC_API_URL=https://civicconnect-api.onrender.com/api/v1
```
