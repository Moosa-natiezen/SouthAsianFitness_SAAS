# South Asian Fitness SaaS

Foundation for a personalized, budget-friendly South Asian diet and fitness planning product.

This repository currently includes the local development stack only: a Next.js frontend, a FastAPI backend, and PostgreSQL. Product features are not implemented yet.

## Stack

- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- Backend: Python + FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Local services: Docker Compose
- Python packages: `uv`
- Node packages: `npm`

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Docker Desktop (or another Docker Engine + Compose setup)
- Git

## First-time setup

From the repository root:

```powershell
copy .env.example .env
copy frontend\.env.example frontend\.env.local
```

Install backend dependencies:

```powershell
cd backend
uv sync
cd ..
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Run locally (recommended)

1. Start PostgreSQL:

```powershell
docker compose up db -d
```

2. Start the API (from `backend/`):

```powershell
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Start the frontend (from `frontend/`):

```powershell
cd frontend
npm run dev
```

- Frontend: http://localhost:3000
- API health: http://localhost:8000/api/health
- API docs (non-production): http://localhost:8000/docs

The home page calls `GET /api/health` and shows whether the API and database are reachable.

## Run the full stack in Docker

```powershell
docker compose up --build
```

The backend container overrides `DATABASE_URL` so PostgreSQL is reached at hostname `db`. Keep host-local `.env` pointed at `localhost` for running uvicorn on your machine.

## Environment variables

Never commit `.env` files. Use `.env.example` as the template.

| Variable | Used by | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | backend | `development` or `production` |
| `DEBUG` | backend | Verbose errors and logging |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Compose | Database credentials |
| `DATABASE_URL` | backend | SQLAlchemy URL (`postgresql+psycopg://...`) |
| `CORS_ORIGINS` | backend | Comma-separated allowed origins |
| `NEXT_PUBLIC_API_URL` | frontend | Public API base URL |

## Project layout

```
frontend/     Next.js app
backend/      FastAPI app
docker-compose.yml
.env.example
```

## Deploy notes

- Frontend Dockerfile builds a Next.js standalone image (`output: "standalone"`).
- Backend Dockerfile installs dependencies with `uv` and runs uvicorn.
- Set `ENVIRONMENT=production`, `DEBUG=false`, a strong `POSTGRES_PASSWORD`, and production `CORS_ORIGINS` / `NEXT_PUBLIC_API_URL` before deploying.
- Do not expose `/docs` in production; it is disabled when `ENVIRONMENT=production`.
