# AGENTS.md — Collaborative Document Editor

## Project overview

Collaborative Document Editor — a Google Docs-style real-time collaborative rich-text editor. Backend: FastAPI + PostgreSQL + Valkey + MinIO. Frontend: Vite + React + TypeScript + Quill + Yjs.

## Tech stack

Full analysis: [tech-stack-analysis.md](tech-stack-analysis.md) (30 components across 6 stages).  
Cross-stage dependency graph: [dependency-map.md](dependency-map.md).

## Repo layout

```
.
├── backend/          # FastAPI application
│   └── app/
│       ├── app.py    # App factory, CORS, middleware, exception handlers
│       └── features/ # Feature-oriented: core/, auth/, documents/, ...
├── frontend/         # Vite + React + TypeScript
│   └── src/
│       ├── features/ # Feature-oriented: auth/, editor/, sharing/, ...
│       ├── lib/      # Shared utilities (api/, hooks/)
│       ├── components/ # Generic UI primitives (ui/)
│       └── types/    # Shared TypeScript types
├── alembic/          # Database migrations (repo root)
├── valkey/           # Valkey config files
├── minio/            # MinIO config files
├── infra/            # Docker + Terraform configuration
├── docs/             # Project documentation
└── scripts/          # Utility scripts
```

## Conventions

**Backend** (FastAPI): Feature-oriented under `app/features/`. Every feature has `routes/`, `services/`, `repositories/`, `schemas.py`, `models.py`, `tests/`.

**Frontend** (Vite + React): Feature-oriented under `src/features/`. Each feature has `api.ts`, `components/`, `hooks/`, `types.ts`, `tests/`.

**Code style**: Backend `ruff` + `mypy`. Frontend `eslint` + `prettier`.

**Commits**: [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`.

## Error envelope contract

All API errors follow this shape:

```json
{"error": {"code": "NOT_FOUND", "message": "Description", "details": {}, "request_id": "uuid"}}
```

Reference: `backend/app/features/core/errors.py`

## Testing requirements

- **Backend**: `pytest` + `pytest-asyncio` + `httpx` AsyncClient
- **Frontend**: `Vitest` + `@testing-library/react` for critical components (editor, auth, sharing)
- **TDD encouraged** — write tests before implementation

## Hooks

- **pre-commit**: `ruff` + `mypy` on `backend/`, `eslint` on `frontend/`
- **pre-push**: Full test suite (backend + frontend)
- **agent-rules**: `scripts/check_agent_rules.py` enforces content equivalence across Claude.md, AGENTS.md, and .cursorrules

## Agent orchestration pattern

- **OpenCode** self-orchestrates as the primary agent — reads task plans, dispatches parallel work, tracks completion across stages S1–S6
- **OpenAI Codex** handles review and rescue invocations — Codex reviews completed tasks and intervenes when tests fail or errors surface
- After implementation, request review via `requesting-code-review` skill
- **CockroachDB is NOT used** — we use PostgreSQL

## MCPs available

- **Figma**: Design tokens in S3 (configured in `opencode.json`)
- **Graphify**: Code-graph queries

## Stage gate awareness

Agents must declare which stage gate they're working in (S1–S6). Cannot work across multiple stages in one task. See `Features_to_develop/` for per-stage development plans.
