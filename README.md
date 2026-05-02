# Collaborative Document Editor

A Google Docs–style real-time collaborative rich-text editor built with FastAPI, React, Quill, and Yjs.

**Current Stage**: 3 — Single-User Rich-Text Editor (feature-complete). Multi-user collaboration arrives in Stage 4.

## Features

### Authentication & Sessions
- Session-cookie based auth with Valkey-backed sessions (HttpOnly, SameSite)
- Login, logout, current-user (`/me`) endpoints with CSRF double-submit protection
- Login rate limiting: 5 attempts per 5 minutes per IP+identifier
- Five seeded demo accounts for local development

### Document Management
- Create, list, rename, and soft-delete documents
- Owner-focused RBAC: users can only access their own documents
- Server-side Yjs content sanitization and audit logging

### Rich-Text Editor
- Full Quill 2 editor with formatting: bold, italic, underline, strikethrough
- Headings: H1, H2, H3, and paragraph via dropdown
- Bulleted and numbered lists
- Link insertion with URL validation and remove-link support
- Undo/Redo via Yjs UndoManager (Ctrl+Z / Ctrl+Shift+Z)
- Clear formatting (strip all inline and block formatting)
- Auto-save after 1.5 s of idle time with visible save-status indicator
- Unsaved-changes guard: browser warns before navigating away with pending edits
- Content persists across page refresh

## Upcoming

| Stage | Description |
|-------|-------------|
| **Stage 4** | Real-time multi-user collaboration (WebSocket/Yjs relay), sharing permissions |
| **Stage 5** | Image uploads, attachments, Markdown/DOCX import |
| **Stage 6** | Production deployment (Terraform, Railway), CI/CD, runbooks |

Detailed development plans in [Features_to_develop/](Features_to_develop/).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) + SQLAlchemy 2.0 async |
| Frontend | Vite + React 19 + TypeScript + Tailwind CSS |
| Editor | Quill 2 + Yjs CRDT (`y-quill`, `y-py` vendored) |
| Database | PostgreSQL 17+ |
| Cache / Sessions | Valkey |
| Object Storage | MinIO (S3-compatible) |
| Auth | HttpOnly session cookies + Valkey + CSRF |

[Full tech stack analysis →](tech-stack-analysis.md) · [Dependency map →](dependency-map.md)

## Demo Accounts

Five demo accounts are seeded automatically when you run `alembic upgrade head`. All use the same password:

| Email | Username | Display Name | Password |
|---|---|---|---|
| alice@example.com | alice | Alice | Password123! |
| bob@example.com | bob | Bob | Password123! |
| carol@example.com | carol | Carol | Password123! |
| dan@example.com | dan | Dan | Password123! |
| erin@example.com | erin | Erin | Password123! |

> These accounts are for local development only. Do not use in production.

## Local Development Setup

### Prerequisites

- Docker Desktop — for Valkey + MinIO
- PostgreSQL 17+ installed locally
- Node.js LTS (≥ 20)
- Python 3.11+
- Rust toolchain — needed to build the vendored `y-py` crate
- [uv](https://docs.astral.sh/uv/) — Python package manager

Verify:

```powershell
docker --version
node --version       # ≥ 20
python --version     # ≥ 3.11
rustc --version      # needed for y-py
uv --version
```

### 1. Environment

```powershell
cp .env.example backend\.env
```

Edit `backend\.env` with your PostgreSQL credentials:

```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/YOUR_DATABASE
```

### 2. Start Infrastructure

```powershell
docker compose up -d
docker compose ps    # valkey + minio should show "healthy"
```

### 3. Backend

```powershell
cd backend
uv sync              # also builds vendored y-py from vendor/ypy/
cd ..
# Run migrations from repo root (alembic.ini lives here)
# Windows:
backend\.venv\Scripts\alembic upgrade head
# macOS / Linux:
backend/.venv/bin/alembic upgrade head
cd backend
uv run uvicorn app.app:create_app --factory --reload
```

Backend runs on `http://localhost:8000`. API docs at `/docs`.

### 4. Frontend

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
├── backend/              # FastAPI application
│   └── app/features/     # Feature-oriented: core/, auth/, documents/
├── frontend/             # Vite + React + TypeScript
│   └── src/
│       ├── features/     # Feature-oriented: auth/, editor/, dashboard/
│       ├── lib/          # Shared utilities (api/, hooks/)
│       ├── components/   # Generic UI primitives (ui/)
│       └── types/        # Shared TypeScript types
├── vendor/               # Vendored y-py (path dependency, built by uv sync)
├── alembic/              # Database migrations
├── infra/                # Docker + Terraform configuration
├── scripts/              # Utility and integration test scripts
├── docs/                 # Project documentation
└── Features_to_develop/  # Stage-by-stage development plans

