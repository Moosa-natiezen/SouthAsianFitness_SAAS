# South Asian Fitness (SAF)

South Asian Fitness is a nutrition and fitness planning platform built around
the food people actually eat. Many mainstream Western food databases are a poor
fit for traditional Desi cooking: a generic entry can miss the oil in a tarka,
ghee absorbed into a dish, fat in a marinade, layered paratha lamination, or the
calorie density of a multi-grain roti. SAF aims to make calorie and macro
tracking, meal planning, and fitness guidance more useful for South Asian
cuisines and budgets.

## What SAF includes

- **Desi-first meal planning:** Personalized meal plans use South Asian dishes
  such as daal, biryani, karahi, roti, chana, and paneer, with portion and
  nutrition targets.
- **The Hidden Fat Rule:** SAF-Engine's prompt specification tells the model
  to account for cooking oil, ghee, and tarka rather than treating a cooked
  dish as a plain ingredient from a generic database. Traditional preparation
  is the default unless a lower-fat version is specified.
- **Dish decomposition and structured output:** The SAF-Engine prompt guides
  component-level estimates for complex dishes and defines a JSON shape for
  dish, portion, calories, macros, and a coaching note. AI meal-plan endpoints
  also return structured meal and daily-total data.
- **AI nutrition and workout tools:** Streaming meal-plan generation and a
  routed agent workflow dispatch nutrition and workout questions to specialized
  workers.
- **Personal targets and plans:** Onboarding captures user preferences and
  restrictions; nutrition targets and budget-aware plans are supported by
  backend services and a South Asian food dataset.
- **At-a-glance metrics:** Dashboard views surface meal and daily calories,
  protein and carbohydrate totals, targets, budget information, and progress.
- **Authentication and resilience:** Email/password and Google sign-in are
  supported. Login requests allow additional time for backend cold starts and
  retry transient network timeouts and 504 responses with backoff.
- **Operational and marketing support:** Sentry integration is available for
  error monitoring. The Next.js app generates its Open Graph social image at
  build/request time, and captures UTM attribution for signup analytics.

Nutrition and macro figures are estimates for general fitness planning; SAF is
not a substitute for medical or clinical nutrition advice.

## Architecture

```text
Browser
  │
  ▼
Next.js App Router (TypeScript, Tailwind CSS)
  │  /api/* same-origin requests
  ▼
FastAPI REST API ─────────────── PostgreSQL
  │                               SQLAlchemy + Alembic
  ├── deterministic meal-plan optimizer
  ├── AI meal-plan streaming and SAF agent workers
  └── authentication, nutrition, progress, foods, billing
```

### Frontend

- Next.js App Router and React with TypeScript
- Tailwind CSS, with a dark interface and honey/amber accent tokens
- Responsive dashboard, onboarding, meal-plan, progress, and account flows
- Sentry, PostHog, and Trigger.dev integrations

In production, Vercel serves the frontend and rewrites `/api/*` requests to the
FastAPI service hosted on Render. The same-origin route keeps browser requests
on the frontend origin. The API client also has explicit timeout and retry
handling for login when the backend is waking from an idle period.

### Backend and SAF-Engine

- Python 3.12+ and FastAPI
- PostgreSQL, SQLAlchemy, Alembic, and pgvector
- OpenAI-backed AI generation, with Langfuse instrumentation
- Nutrition and workout workers coordinated by an intent-routing orchestrator
- A deterministic, constraint-aware meal-plan optimizer that filters foods by
  diet, allergies, restrictions, verification status, and available pricing

The SAF-Engine system prompt lives at
[`prompts/saf_engine_system_prompt.md`](./prompts/saf_engine_system_prompt.md).
It describes the Hidden Fat Rule, component-level decomposition, and the
structured JSON contract. The AI meal-plan endpoint has its own meal-plan JSON
shape. The deterministic optimizer is a separate path and should not be
confused with model-generated estimates.

### Infrastructure and developer tools

- Docker Compose for local PostgreSQL and the full service stack
- `uv` for Python dependency and environment management
- `npm` for frontend dependencies and scripts
- Sentry SDK configuration for frontend and backend error monitoring
- Trigger.dev for background task integration
- Next.js generated Open Graph image and UTM attribution capture for marketing
  workflows

## Tech stack

| Area | Technologies |
| --- | --- |
| Web application | Next.js, React, TypeScript, Tailwind CSS |
| API | Python, FastAPI, Pydantic |
| Data | PostgreSQL, SQLAlchemy, Alembic, pgvector |
| AI | OpenAI, SAF-Engine prompt pipeline, Langfuse |
| Background jobs | Trigger.dev |
| Monitoring and analytics | Sentry, PostHog |
| Local services | Docker Compose |
| Package management | `npm`, `uv` |

## Get started locally

### Requirements

- Node.js 20+ and npm
- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
- Docker Desktop (or Docker Engine with Compose)

### 1. Configure local environment

From the repository root, create the backend environment file:

```powershell
Copy-Item .env.example .env
```

Set `SECRET_KEY` and `CSRF_SECRET_KEY` to unique random values of at least 32
characters in `.env`. The example values are placeholders; never use them in
production or commit real environment files.

For local frontend-to-backend requests, create the frontend environment file:

```powershell
Copy-Item frontend\.env.example frontend\.env.local
```

Set this in `frontend\.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Install dependencies

From the repository root:

```powershell
Set-Location backend
uv sync
Set-Location ..\frontend
npm ci
Set-Location ..
```

### 3. Start PostgreSQL

The Compose database service reads its credentials from the root `.env`:

```powershell
docker compose up db -d
```

### 4. Apply database migrations

Run from `backend/`. The root `.env` supplies the local database URL:

```powershell
Set-Location backend
uv run alembic upgrade head
```

### 5. Run the API and frontend

In one terminal, from `backend/`:

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal, from `frontend/`:

```powershell
npm run dev
```

Open:

- Frontend: <http://localhost:3000>
- API health: <http://localhost:8000/api/health>
- Interactive API docs: <http://localhost:8000/docs>

The backend seeds reference and food data during startup when needed. The
interactive API documentation is intended for development; it is disabled in
production.

### Run services with Docker Compose

To build and start all containers:

```powershell
docker compose up --build
```

Apply migrations inside the running backend container:

```powershell
docker compose exec backend uv run alembic upgrade head
```

The Compose backend uses the `db` service hostname. When running the backend
directly on the host, `DATABASE_URL` in the root `.env` should use
`localhost`.

## Configuration

Use `.env.example` and `frontend/.env.example` as templates. Do not commit
`.env`, `.env.local`, credentials, API keys, or production secrets.

| Variable | Service | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Backend | SQLAlchemy PostgreSQL connection URL |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Compose | Local database credentials |
| `SECRET_KEY`, `CSRF_SECRET_KEY` | Backend | Session and CSRF signing keys |
| `ENVIRONMENT`, `DEBUG` | Backend | Runtime environment and debug behavior |
| `CORS_ORIGINS` | Backend | Comma-separated allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | Frontend | API base URL; use localhost for local development |
| `OPENAI_API_KEY` | Backend | Enables OpenAI-backed generation |
| `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN` | Backend / frontend | Optional error monitoring |
| `TRIGGER_PROJECT_ID`, `TRIGGER_BACKEND_URL` | Frontend tasks | Background-task project and API URL |
| `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` | Frontend | Optional product analytics |

Additional integrations (for example Google sign-in, billing, or WhatsApp)
require their corresponding provider credentials. Configure them only when
working on those features.

## Repository layout

```text
backend/      FastAPI application, migrations, tests, and food data
frontend/     Next.js application, components, and frontend tests
prompts/      SAF-Engine system prompt specification
docs/         Project and engineering documentation
scripts/      Developer utilities
docker-compose.yml
.env.example
```

## Useful commands

From `frontend/`:

```powershell
npm run dev
npm run lint
npm test
npm run build
```

From `backend/`:

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uv run pytest
uv run alembic upgrade head
```

## Deployment notes

- The frontend is configured for Vercel; `/api/*` is rewritten to the
  production Render API in `frontend/vercel.json`.
- Configure production database credentials, signing keys, CORS origins, and
  provider credentials in the hosting platforms' secret managers.
- Leave `NEXT_PUBLIC_API_URL` unset in production when using the Vercel rewrite.
- Disable debug mode and keep API docs unavailable in production.
- Run Alembic migrations as a deployment step before serving traffic.
