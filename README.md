# Collaborative Document Editor

A Google Docs–style real-time collaborative rich-text editor built with FastAPI, React, Quill, and Yjs.

## Demo Accounts
<!-- Filled in Stage 2 -->
*Coming in Stage 2*

## Tech Stack

[Full tech stack analysis →](docs/tech-stack-analysis.md)

## Local Development Setup

### Prerequisites

- Docker Desktop (with WSL2 backend on Windows)
- Node.js LTS (≥ 20)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — install via `pip install uv` or `scoop install uv` (Windows)

Verify prerequisites:
```powershell
docker --version
node --version     # ≥ 20
python --version   # ≥ 3.11
where.exe uv       # should resolve
```

### 1. Clone & Environment Setup

```powershell
git clone <repo-url>
cd "Ajaia Recruitment Test - Document Editor"
cp .env.example .env
```

### 2. Start Infrastructure

```powershell
docker compose up -d
docker compose ps   # all services should show "healthy"
```

### 3. Start Backend

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.app:create_app --factory --reload
```

Backend runs on `http://localhost:8000`. Swagger docs at `/docs`.

### 4. Start Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Running Tests

```powershell
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && npm run test:ci
```

## Project Structure

```
.
├── backend/          # FastAPI application
│   └── app/
│       ├── app.py
│       └── features/ # Feature-oriented: core/, auth/, documents/, ...
├── frontend/         # Vite + React + TypeScript
│   └── src/
│       ├── features/ # Feature-oriented: auth/, editor/, sharing/, ...
│       ├── lib/      # Shared utilities
│       ├── components/ # Generic UI primitives
│       └── types/    # Shared TypeScript types
├── alembic/          # Database migrations (repo root)
├── valkey/           # Valkey config files
├── minio/            # MinIO config files
├── infra/            # Docker + Terraform configuration
│   ├── docker/
│   └── terraform/
├── docs/             # Project documentation
│   ├── design/
│   └── dev-plans/
└── scripts/          # Utility scripts
```

## Development Plans

[Stage-by-stage development plans →](docs/dev-plans/)

## Coding Agent Setup

[Setting up coding agents for this repo →](docs/AGENT-SETUP.md)

## Supported File Types & Known Limitations
<!-- Filled in Stage 5 -->
*Coming in Stage 5*

## Deployment
<!-- Filled in Stage 6 -->
*Coming in Stage 6*

## License

MIT
