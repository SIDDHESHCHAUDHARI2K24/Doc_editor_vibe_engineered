# Tech Stack Analysis — Collaborative Document Editor

**Project**: Google Docs–style real-time collaborative rich-text editor
**Audience**: Coding agents (Claude Code, OpenCode, OpenAI Codex, Cursor) executing the staged dev plans.
**Cross-references**: `dependency-map.md`, `stage-N-development-plan.md`

---

## Stack Components

| # | Technology | Role | Stage(s) introduced |
|---|---|---|---|
| 1 | **FastAPI** (async) | HTTP framework — REST endpoints, WebSocket endpoints, Pydantic v2 validation, auto OpenAPI docs, dependency injection | 1 |
| 2 | **uv** | Python package manager — lockfile, fast resolver, replaces pip+venv | 1 |
| 3 | **PostgreSQL** | Primary persistent store — users, sessions (optional), documents, document permissions, attachments metadata, audit log. Yjs document state stored as `BYTEA` | 1 |
| 4 | **asyncpg** (via SQLAlchemy 2.0 async) | Async PostgreSQL driver — used by FastAPI workers and by the boilerplate's existing `core` feature | 1 |
| 5 | **Alembic** | DB migrations — `alembic/` directory at repo root, autogenerate from SQLAlchemy metadata | 1 |
| 6 | **Valkey** | (a) Session store, (b) Yjs update pub/sub fan-out across FastAPI instances, (c) awareness/cursor relay channel, (d) rate-limit token buckets | 1 (infra), 2 (sessions), 4 (pub/sub + rate limits) |
| 7 | **MinIO** | **Local-dev only** — S3-compatible object storage for attachments and Yjs snapshots during development | 1 (infra), 4 (snapshots), 5 (attachments) |
| 8 | **Railway Buckets** | **Production object storage** — S3-compatible managed primitive on Railway, replaces MinIO in deployed env. Same SDK code, only env vars differ | 6 |
| 9 | **Vite + React** | Frontend framework — fast HMR dev server, React 18+ for UI, TypeScript | 1 |
| 10 | **Quill (v2)** | Rich-text editor library — Delta document model, customizable toolbar | 3 |
| 11 | **Yjs** | CRDT library — drives collaborative editing, binary encoded document state, integrates with Quill via `y-quill` | 3 (data model only), 4 (live sync) |
| 12 | **y-quill** | Quill ↔ Yjs binding — applies Yjs updates to Quill and vice versa | 3 |
| 13 | **y-websocket** (client) | WebSocket transport for Yjs sync protocol — paired with our custom FastAPI server-side relay (we are NOT running the standard Node.js `y-websocket` server) | 4 |
| 14 | **y-py** | Python bindings for Yjs — used server-side to apply incoming updates, hold authoritative doc state, persist to Postgres | 4 |
| 15 | **boto3 / aiobotocore** | S3-compatible client used against MinIO locally and Railway Buckets in prod | 4 (snapshots), 5 (attachments) |
| 16 | **pytest** + **pytest-asyncio** | Backend tests — endpoint tests, repo tests, WebSocket tests via `httpx` AsyncClient and `websockets` test client | 2 |
| 17 | **Vitest** + **@testing-library/react** | Frontend unit tests — critical components (editor, share dialog, auth) | 3 |
| 18 | **Pydantic v2** | Request/response validation, settings management (`pydantic-settings`) | 1 |
| 19 | **bleach** | Server-side HTML sanitization — applied to any rich content imported from `.docx`/`.md`/`.html` before conversion to Delta | 5 |
| 20 | **python-docx**, **markdown** (or `markdown-it-py`) | File-import parsers — `.docx` → text+styles, `.md` → HTML → Delta | 5 |
| 21 | **filetype** (python) | Magic-byte detection for upload validation — refuses files whose declared MIME doesn't match actual bytes | 5 |
| 22 | **structlog** | Structured JSON logging with correlation IDs (`request_id`, `user_id`, `doc_id`) | 1 |
| 23 | **slowapi** (or custom Valkey-backed token bucket) | Rate limiting on auth, sharing, upload endpoints | 2 (auth), 4 (sharing), 5 (uploads) |
| 24 | **Docker / Docker Compose** | Local orchestration of Postgres + Valkey + MinIO; production Dockerfiles for FastAPI and frontend | 1 (local), 6 (prod images) |
| 25 | **Terraform** + `terraform-community-providers/railway` | Infrastructure-as-code for Railway deployment in Stage 6 | 6 |
| 26 | **Figma MCP** | Design-token + component lookup against the Figma WYSIWYG kit during frontend implementation | 1 (setup), 3 (used heavily) |
| 27 | **Graphify** ([safishamsi/graphify](https://github.com/safishamsi/graphify)) | Repo-as-knowledge-graph MCP — gives agents queryable view of code + schemas + docs | 1 |
| 28 | **obra/superpowers skills** | Repo-level coding agent skills — TDD, brainstorming, executing-plans, requesting-code-review, etc. | 1 |

---

## Coverage Assessment

For each major capability, the table below identifies which stack component(s) handle it.

| Capability | Component(s) |
|---|---|
| User authentication | FastAPI session middleware (boilerplate) + Valkey session store + bcrypt-hashed passwords in Postgres `users` table |
| Document CRUD | FastAPI REST + asyncpg + Postgres `documents` table |
| Rich-text formatting (bold/italic/underline/headings/lists) | Quill v2 toolbar + Quill Delta document model |
| Persistence of formatted content across reloads | Yjs document state encoded as binary, stored in Postgres `documents.yjs_state` (BYTEA) |
| Real-time multi-user editing (CRDT merging) | Yjs (client) + y-quill + y-websocket (transport) + y-py (server-side application) |
| Cross-instance update fan-out | Valkey pub/sub channel `doc:{document_id}` |
| Live presence/cursor (awareness) | Yjs awareness protocol + Valkey channel `aware:{document_id}` (ephemeral, not persisted) |
| Sharing (owner / editor / viewer) | Postgres `document_permissions` table + RBAC dependency in FastAPI |
| Sharing UX (search by username/email) | FastAPI `/users/lookup` endpoint + frontend share dialog |
| File import (.txt / .md / .docx → new doc) | Frontend upload widget → FastAPI `/documents/import` → `python-docx` / `markdown` → HTML → Delta → seed Yjs doc |
| Attachments | Frontend → presigned-URL flow → MinIO (local) / Railway Buckets (prod); metadata in Postgres `attachments` |
| Snapshots / future-versioning foundation | FastAPI background task on disconnect + 5-min timer → write Yjs binary snapshot to object storage `snapshots/{doc_id}/{ts}.bin` |
| Validation | Pydantic v2 schemas on every endpoint |
| RBAC enforcement | Centralized FastAPI dependency `require_doc_role(min_role)` |
| Sanitization (rich content) | `bleach` HTML allowlist + Delta op attribute allowlist |
| Rate limiting | Valkey-backed sliding window or token bucket (custom or `slowapi`) |
| Error contract | Custom exception hierarchy + global exception handler returning `{ "error": { "code", "message", "details" } }` |
| Audit logging | Postgres `audit_log` table written on share grant/revoke/role-change/delete |
| Structured logging | `structlog` JSON with correlation IDs |
| File upload safety | `filetype` magic-byte check + size cap + MIME allowlist + UTF-8 validation for text |
| WebSocket auth | Session cookie validated on WS handshake + per-message permission re-check on every Yjs update |
| Local development orchestration | Docker Compose (Postgres + Valkey + MinIO); FastAPI + Vite run natively on Windows |
| Production deployment | Terraform → Railway (managed Postgres + Redis + Buckets) + Dockerized FastAPI service + Dockerized static frontend service |

---

## Gaps Identified

### G1 — CRDT Library Choice (closed by recommendation)

**Gap**: User specified Quill but did not pick a CRDT. Real collaborative editing needs one.
**Recommendation**: **Yjs**. It is the de-facto choice for Quill-based collaborative editors, has a maintained Quill binding (`y-quill`), and has Python bindings (`y-py`) for server-side authority. Alternative `automerge` lacks a maintained Quill binding.
**Locked.**

### G2 — Server-Side WebSocket Relay for Yjs (closed by design)

**Gap**: The standard Yjs WebSocket server is a Node.js binary (`y-websocket`). Running it alongside FastAPI adds operational overhead.
**Recommendation**: Implement a thin FastAPI WebSocket endpoint that speaks the Yjs sync protocol using `y-py`. This keeps a single Python process, simplifies auth (sessions checked in FastAPI middleware), and makes per-message permission re-checks trivial. Trade-off: we re-implement a small binary protocol — well-documented in the Yjs source.
**Risk flag**: medium — protocol implementation is non-trivial; suite of integration tests with two real `y-websocket` clients required in Stage 4.
**Locked.**

### G3 — Email Verification / Password Reset (out of scope)

**Gap**: Production-grade auth would have email verification and password reset. Brief allows seeded users + lightweight flow.
**Decision**: Out of scope. Seeded users, hashed passwords, login form only. Flag for future Stage 6+ if needed.
**Locked.**

### G4 — Sharing Notification Channel (deferred)

**Gap**: When user A shares a doc with user B, B has no out-of-band notification. They only see it under "Shared with me" on next dashboard load.
**Decision**: Deferred. In-app polling for new shared docs every N seconds on the dashboard is sufficient for the demo and avoids an SMTP integration.
**Locked.**

### G5 — Snapshot Trigger Strategy (recommendation)

**Gap**: When are Yjs snapshots written to object storage?
**Recommendation**:
1. **On last-collaborator-disconnect** — FastAPI tracks connection count per doc; when it hits zero, write final snapshot.
2. **On 5-min timer while document has active edits** — in-memory dirty-flag, debounced.
3. **Never on every keystroke** — would burn object-storage operations.

**Locked, implemented in Stage 4.**

### G6 — `.docx` Import Fidelity (accepted lossy)

**Gap**: Converting `.docx` to Quill Delta is inherently lossy. Tables, images embedded in docx, footnotes, complex styles will not survive cleanly.
**Decision**: Accept lossy conversion. The README must clearly state the supported subset (paragraphs, headings 1–3, bold/italic/underline, bulleted/numbered lists). Anything else either renders as plain paragraph text or is dropped.
**Risk flag**: medium — set realistic test fixtures in Stage 5.
**Locked.**

### G7 — Frontend Auth State (assumption)

**Gap**: How does the frontend know who is logged in?
**Assumption**: Session cookie set by backend (HttpOnly, SameSite=Lax). Frontend has a `/me` endpoint it calls on load to populate user state in a React context. No JWT, no localStorage tokens.
**Locked.**

### G8 — File Size Limits (recommendation)

**Gap**: No upload size cap stated.
**Recommendation**:
- `.txt` / `.md`: 1 MB
- `.docx`: 10 MB
- Attachments: 25 MB
- Reject server-side via `Content-Length` check **before** streaming body.
**Locked, implemented in Stage 5.**

### G9 — CORS / CSRF Strategy (recommendation)

**Gap**: Frontend on `http://localhost:5173`, backend on `http://localhost:8000` in dev → CORS needed. Production same-origin via Railway routing if deployed under one domain, separate origins otherwise.
**Recommendation**:
- Dev: FastAPI CORS middleware allowing `http://localhost:5173`, `credentials: true`.
- Prod: same-origin if possible (frontend served from `app.example.railway.app`, backend from `api.example.railway.app` with explicit allowlist).
- CSRF: Double-submit cookie pattern on state-changing endpoints — session cookie + `X-CSRF-Token` header echoed from a non-HttpOnly cookie. Implemented in Stage 2.
**Locked.**

### G10 — `python-docx` Image Handling (deferred)

**Gap**: `.docx` files often embed images. `python-docx` exposes them as parts but mapping into Delta + uploading to MinIO is significant work.
**Decision**: For Stage 5, **drop images during `.docx` import**. Document this in the import dialog: "Images are not preserved during import." Future stage can extract embedded images to attachments.
**Locked.**

---

## Assumptions Log

These are minor decisions made without explicit user input. The user can override before execution.

| ID | Assumption | Rationale | Reversible? |
|---|---|---|---|
| A1 | Local dev runs **infra (Postgres/Valkey/MinIO) in Docker Desktop, FastAPI + Vite native on Windows** | User chose Railway for prod but didn't pin local mode after the deploy decision. This gives best iteration speed on Windows. | Yes — switch to WSL2 or full-Docker compose without code changes |
| A2 | Backend uses SQLAlchemy 2.0 async ORM (consistent with boilerplate) | Boilerplate uses asyncpg directly + helpers; we'll layer SQLAlchemy 2.0 on top for ergonomics on `documents`, `permissions`, `attachments`, `audit_log` tables. Auth feature stays close to boilerplate style. | Yes — could stay raw asyncpg throughout |
| A3 | Sessions stored in **Valkey only**, not Postgres | The boilerplate has a Postgres `sessions` table; we replace it with Valkey because user picked "Sessions + pub/sub + fan-out" for Valkey | Yes — we can keep Postgres sessions if Valkey unavailable in dev |
| A4 | Frontend uses **TypeScript** (not plain JS) | Industry default for new Vite+React projects in 2026; unstated but assumed | Yes |
| A5 | Frontend state management: **React Context + TanStack Query** for server state | Lighter than Redux; fits the data-fetch-heavy nature of doc lists | Yes — Redux Toolkit if user prefers |
| A6 | Frontend routing: **React Router v6** | Standard | Yes |
| A7 | UI styling: **TailwindCSS** matching Figma kit's design tokens | Figma → tokens → Tailwind config is a clean pipeline. Alternative is CSS Modules. | Yes — confirm against the actual Figma file in Stage 1 |
| A8 | Password hashing: **bcrypt** via `passlib[bcrypt]` (boilerplate default) | Stated in boilerplate | No (would require migration) |
| A9 | Document IDs: **UUID v7** (time-ordered) | Better index locality than v4 for time-sorted dashboards | Yes — fall back to v4 |
| A10 | All dates stored as `TIMESTAMPTZ` UTC; client converts | Standard practice | No |
| A11 | WebSocket URL pattern: `wss://api.host/ws/docs/{doc_id}` with session cookie sent via cookie header (browsers auto-attach) | Standard | No |
| A12 | Each document has **exactly one owner** at any time; ownership transfer is out of scope | Brief says "a document owner" singular | Yes — add transfer in future stage |
| A13 | Soft-delete documents (set `deleted_at` timestamp) rather than hard-delete | Lets us undo accidents and keeps audit log meaningful | Yes |
| A14 | Logging level **DEBUG in dev, INFO in prod**; logs go to stdout (Railway captures stdout) | Standard 12-factor | Yes |
| A15 | Environment via `.env` files locally + Railway environment variables in prod | Consistent with boilerplate | No |
| A16 | The 5 seeded users have realistic names: alice@example.com, bob@example.com, carol@example.com, dan@example.com, erin@example.com, all with password `Password123!` (clearly demo-only) | Easy demo, document in README | Yes |

---

## Compatibility Notes

| Concern | Detail | Mitigation |
|---|---|---|
| **Windows native + asyncpg** | asyncpg installs cleanly on Windows via uv. No known issues. | None needed. |
| **Yjs binary protocol over WebSocket** | Browser `y-websocket` client sends Uint8Array frames (binary opcode); FastAPI WebSocket must use `websocket.send_bytes` / `receive_bytes`. | Document explicitly in WebSocket handler. Test with binary frames in pytest. |
| **y-py version pinning** | y-py occasionally has breaking releases lagging behind Yjs. | Pin both `yjs` (frontend, package.json) and `y-py` (backend) to verified-compatible versions; document the pair in `Claude.md` / `AGENTS.md`. |
| **Valkey vs Redis client** | Valkey is API-compatible with Redis. Use `redis-py` (asyncio variant) — works seamlessly. | None. Document the choice in core feature README. |
| **Railway Buckets vs MinIO API surface** | Both are S3-compatible but Railway Buckets prefers virtual-hosted-style URLs while MinIO needs path-style. boto3 supports both via `s3={"addressing_style": "virtual"|"path"}`. | Make addressing style env-driven. Default `path` for MinIO, `virtual` for Railway. |
| **Quill v2 vs v1** | Quill 2.0 (released 2024) is the current major; ensure `y-quill` version supports v2. | Pin Quill 2.x and a `y-quill` release that targets it; verify in Stage 3. |
| **Vite 5 + React 18** | Stable, no known issues. React 19 is shipped but Vite/Quill ecosystem still settling — use 18 unless explicitly upgraded. | Pin React 18.3.x. |
| **Alembic + async engine** | Alembic 1.13+ supports async migrations cleanly; boilerplate already configured. | None. |
| **`python-docx` not async** | It's a sync library. | Run via `run_in_threadpool` in the FastAPI handler so the event loop isn't blocked. |
| **bcrypt cost factor on Windows** | Default cost (12) takes ~250ms; fine for login but hits dev seed scripts. | Use cost 10 in dev seeds, cost 12 in prod (env-driven). |
| **CORS + WebSocket** | WebSockets bypass CORS but the initial HTTP upgrade respects browser origin checks. | Allow `http://localhost:5173` origin during handshake; reject otherwise in prod. |
| **Terraform Railway provider maturity** | The community provider is functional but lags behind Railway dashboard features. Some primitives (e.g., Buckets) may need to be created via the Railway CLI/dashboard and imported. | Stage 6 plan accounts for this — Terraform manages services + env vars; Buckets created via CLI and imported. |
| **uv on Windows** | Works natively, but PATH issues are common after install. | Stage 1 setup task includes PATH verification step. |

---

## Stack Component → Stage Map

| Component | S1 | S2 | S3 | S4 | S5 | S6 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| FastAPI / uv | Setup | Endpoints | — | WebSocket | Endpoints | — |
| Postgres / Alembic | Containers + bootstrap | Migrations: users, sessions(?) | Migration: documents.yjs_state | Migration: permissions, audit_log | Migration: attachments | — |
| Valkey | Container | Session store | — | Pub/sub + awareness | — | Managed Redis |
| MinIO / Railway Buckets | MinIO container | — | — | Snapshots | Attachments | Railway Buckets |
| Vite / React | Scaffold | Login + dashboard | Editor + Quill + Yjs | Sharing UI + presence | Import + attachments UI | — |
| Quill / Yjs / y-quill / y-py / y-websocket | — | — | Yjs as data model | Live sync | — | — |
| pytest / Vitest | Configured | Backend tests | Frontend tests start | Backend + frontend | Both | E2E smoke (deployed) |
| structlog / Pydantic / error envelope | Foundation | Used | Used | Used | Used | Used |
| bleach / filetype / python-docx / markdown | — | — | Sanitization for Delta | — | Import + validation | — |
| Docker / Compose | Local infra | — | — | — | — | Prod images |
| Terraform | — | — | — | — | — | Railway IaC |
| Figma MCP / Graphify / Superpowers | Setup | Used | Used (Figma heavy) | Used | Used | — |

---

*End of tech-stack-analysis.md*
