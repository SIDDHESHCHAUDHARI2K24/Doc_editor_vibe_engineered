# Stage 6 Development Plan — Deployment via Terraform to Railway

**Stage**: 6 of 6 (final)
**Headline deliverable**: The full application — FastAPI backend, Vite frontend, managed Postgres, managed Redis, Railway Buckets — runs in production on Railway.com under one domain serving frontend at `/*` and backend at `/api/*`. Infrastructure is declared in Terraform; the only manual step on first deploy is provisioning a Railway API token. Subsequent deploys happen automatically on `main` branch push (Railway's GitHub integration). Tagged releases trigger a GitHub Actions workflow that runs the deployed smoke-test suite and creates a GitHub Release. Database migrations run automatically in the Railway pre-deploy hook. The smoke-test suite is also runnable locally against any deployed environment by setting `BASE_URL`.

**Cross-references**: `tech-stack-analysis.md`, `dependency-map.md`, `derived-design-system.md`, `stage-1-development-plan.md`, `stage-2-development-plan.md`, `stage-3-development-plan.md`, `stage-4-development-plan.md`, `stage-5-development-plan.md`

---

## Executive Summary

Stage 6 turns the locally-running app into a production deployment. Every architectural decision was made earlier; this stage is about packaging, declaring, and verifying. The work is mechanical but the consequences of getting it wrong are visible (deploys fail, app is broken, smoke tests are red).

Three concerns dominate:

1. **Containerization** — A single Docker image hosting nginx + FastAPI + the Vite-built frontend. nginx serves static at `/*` and proxies `/api/*` (and `/ws/*`) to uvicorn. Multi-stage Dockerfile keeps the image lean (<500 MB target).
2. **Terraform-managed infrastructure** — Railway services, plugins (managed Postgres + Redis), Buckets, environment variables, and domains declared as code. Buckets may need a CLI workaround per global risk R4; the plan handles this explicitly.
3. **Environment-driven configuration** — The `Settings` class from Stage 1 already declared every prod-relevant variable; this stage activates the prod values. `RAILWAY_ENVIRONMENT` env var presence flips: S3 endpoint, addressing style, cookie Secure flag, log level, bcrypt cost.

The "automated smoke tests on deploy" choice means GitHub Actions becomes a real concern — not just for the prod-promotion workflow but also for the post-deploy verification. The plan includes both workflows.

- **Total tasks**: 7
- **Total sub-tasks**: 28
- **Estimated effort**: 4–6 days for a single developer; 2.5–3.5 days with parallel agent execution
- **Top 3 risks**:
  1. **Terraform Railway provider lags behind dashboard features** (R4 in global risk register). Buckets primitive specifically may not be supported. Workaround: provision via Railway CLI in a one-time bootstrap script, then `terraform import` into state. Documented in `P6.T3.S4`.
  2. **Same-container deployment of nginx + FastAPI** has a process-management subtlety: which process is PID 1? We use `supervisord` (or `dumb-init` + a small launcher script) to manage both processes and forward signals. Getting this wrong means Railway's restart policy can't shut down cleanly.
  3. **Pre-deploy migration hook timing** — Railway's pre-deploy command runs in a separate ephemeral container before the new service starts. Migration must complete before traffic shifts. Failed migration must abort the deploy. This is configurable but easy to misconfigure.

---

## Entry Criteria

All Stage 5 exit criteria met. Specifically:
- ✅ Full feature set works in local dev: auth, doc CRUD, real-time collaboration, sharing, image attachments, .md / .docx import.
- ✅ DEMO.md script runs end-to-end without surprises.
- ✅ Backend pytest coverage solid; Vitest passing.
- ✅ `Settings` class (S1 P1.T3.S5) declares every prod env var.
- ✅ `core/storage.py` is environment-driven (addressing style + endpoint URL switchable via env).
- ✅ Local Docker Compose for dev still works.

**Additional prerequisites unique to Stage 6:**
- ✅ User has a Railway account
- ✅ User has a Railway API token (created via Railway dashboard → Account Settings → Tokens)
- ✅ User has a GitHub repository for the project with admin access
- ✅ Local Terraform CLI installed (`>= 1.6`)
- ✅ Railway CLI installed (`npm i -g @railway/cli` or scoop on Windows)

## Exit Criteria

1. Two production-grade Dockerfiles in place: `infra/docker/Dockerfile.app` (single image hosting nginx + FastAPI + static frontend), `infra/docker/Dockerfile.dev` if needed for local prod-like compose.
2. `infra/docker/nginx.conf` configured to serve static at `/*` and proxy `/api/*` and `/ws/*` to uvicorn on `127.0.0.1:8000`.
3. `infra/docker/supervisord.conf` (or equivalent) managing nginx + uvicorn as child processes with proper signal forwarding.
4. Image builds locally to <500 MB and `docker run -p 8080:8080 ...` brings up a functional app reachable at `http://localhost:8080`.
5. `infra/terraform/` directory with `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, README, and a `terraform.tfvars.example`.
6. Terraform declares: Railway project + production environment, the app service, managed Postgres plugin, managed Redis plugin, environment variables wired across services.
7. Railway Buckets bootstrap script `scripts/bootstrap_railway_buckets.sh` (and `.ps1`) creates the bucket via Railway CLI; Terraform `import` block pulls it into state on subsequent `terraform plan`.
8. `terraform apply` from a fresh project reaches a healthy production deployment in <15 minutes.
9. Backend `Settings` reads `RAILWAY_ENVIRONMENT` and switches S3 endpoint URL + addressing style; cookie Secure flag; log level; bcrypt cost. All other prod variables are provided via Terraform-managed env vars.
10. Railway pre-deploy hook runs `alembic upgrade head` before each deploy. A failing migration aborts the deploy.
11. Seed users (5 demo accounts) are inserted via Alembic data migration on first deploy (already done in S2 P1.T1.S4 — verified end-to-end in production here).
12. Railway Buckets has CORS configured to allow PUT + GET + HEAD from the production domain. Configured via the bootstrap script + a `terraform null_resource` that runs after Buckets exists.
13. `git push` to `main` triggers Railway's auto-deploy; deploy completes in <5 minutes; smoke test workflow runs and posts results.
14. GitHub Actions workflow `.github/workflows/deploy-smoke-test.yml` triggers on every successful Railway deploy (via webhook or post-merge cron) and runs the pytest smoke suite against the deployed `BASE_URL`.
15. GitHub Actions workflow `.github/workflows/release.yml` triggers on `v*.*.*` tag push: runs smoke tests, creates a GitHub Release with auto-generated notes from PR titles since last tag.
16. Smoke test suite at `backend/tests/smoke/` runnable both:
    - Locally: `BASE_URL=https://yourapp.up.railway.app uv run pytest backend/tests/smoke -v`
    - In CI: GitHub Actions runs it with secrets injected.
17. Smoke tests cover (at minimum): login flow, doc creation + RBAC, WebSocket connect + echo, image upload + GET URL resolution, .md import, share + permission revocation.
18. README "Deployment" section documents the first-time setup walkthrough.
19. `docs/DEPLOY.md` is the comprehensive first-deploy guide (token creation, Terraform init, apply, post-apply verification).
20. `docs/RUNBOOK.md` covers operational scenarios: deploy failed, migration failed, secret rotation, scaling, observability, rollback.

---

## Phase Overview

Three phases. Phase A is containerization — produce a deployable artifact. Phase B is Terraform — declare infrastructure. Phase C is CI/CD wiring + smoke tests + docs. They overlap by design — containerization is fully independent, Terraform doesn't need finished CI to apply, and CI work can begin against a stub Dockerfile.

| Task | Phase | Focus | Deliverable | Effort |
|---|---|---|---|---|
| **P6.T1** | A | Application container | Multi-stage Dockerfile, nginx config, supervisord, .dockerignore, prod-like compose | XL |
| **P6.T2** | A | Environment-aware backend | `Settings` switches via `RAILWAY_ENVIRONMENT`; `core/storage.py` honors `S3_ADDRESSING_STYLE`; cookie + log + bcrypt prod values | M |
| **P6.T3** | B | Terraform infrastructure | `infra/terraform/` with project, services, plugins, env vars, Buckets bootstrap | XL |
| **P6.T4** | B | Pre-deploy migration hook | Railway pre-deploy command runs `alembic upgrade head`; failure aborts deploy | M |
| **P6.T5** | C | Smoke test suite | `backend/tests/smoke/` covering full E2E flow against any `BASE_URL` | L |
| **P6.T6** | C | GitHub Actions workflows | Auto-deploy webhook integration, post-deploy smoke test workflow, tag-triggered release workflow | L |
| **P6.T7** | A+B+C | Docs + first deploy + handoff | README, DEPLOY.md, RUNBOOK.md, actual first-deploy verification, handoff checklist | M |

---

## Intra-Stage Dependency Graph (Sub-Task Level)

```mermaid
graph TD
    subgraph "P6.T1 — Application container"
        T1_S1[P6.T1.S1<br/>Backend Dockerfile multi-stage]
        T1_S2[P6.T1.S2<br/>Frontend build stage]
        T1_S3[P6.T1.S3<br/>Combined image: nginx + uvicorn + static]
        T1_S4[P6.T1.S4<br/>nginx.conf path routing]
        T1_S5[P6.T1.S5<br/>supervisord.conf process mgmt]
        T1_S6[P6.T1.S6<br/>.dockerignore + prod-like compose]
    end

    subgraph "P6.T2 — Env-aware backend"
        T2_S1[P6.T2.S1<br/>Settings: detect RAILWAY_ENVIRONMENT]
        T2_S2[P6.T2.S2<br/>core/storage.py: addressing style switch]
        T2_S3[P6.T2.S3<br/>Cookie Secure + log level + bcrypt cost]
    end

    subgraph "P6.T3 — Terraform"
        T3_S1[P6.T3.S1<br/>versions.tf + provider config]
        T3_S2[P6.T3.S2<br/>main.tf: project + service + plugins]
        T3_S3[P6.T3.S3<br/>variables.tf + tfvars.example]
        T3_S4[P6.T3.S4<br/>Buckets bootstrap script + import]
        T3_S5[P6.T3.S5<br/>Buckets CORS via null_resource]
        T3_S6[P6.T3.S6<br/>outputs.tf: URLs + bucket name]
        T3_S7[P6.T3.S7<br/>terraform README + apply walkthrough]
    end

    subgraph "P6.T4 — Pre-deploy migration"
        T4_S1[P6.T4.S1<br/>Railway pre-deploy command config]
        T4_S2[P6.T4.S2<br/>Migration failure aborts deploy]
    end

    subgraph "P6.T5 — Smoke tests"
        T5_S1[P6.T5.S1<br/>Pytest fixtures: BASE_URL, demo accounts]
        T5_S2[P6.T5.S2<br/>Auth + doc CRUD smoke tests]
        T5_S3[P6.T5.S3<br/>WebSocket smoke test]
        T5_S4[P6.T5.S4<br/>Image upload smoke test]
        T5_S5[P6.T5.S5<br/>Share + permission smoke test]
        T5_S6[P6.T5.S6<br/>Import .md smoke test]
    end

    subgraph "P6.T6 — GitHub Actions"
        T6_S1[P6.T6.S1<br/>Auto-deploy via Railway GitHub integration]
        T6_S2[P6.T6.S2<br/>Post-deploy smoke test workflow]
        T6_S3[P6.T6.S3<br/>Tag-triggered release workflow]
    end

    subgraph "P6.T7 — Docs + handoff"
        T7_S1[P6.T7.S1<br/>README Deployment section]
        T7_S2[P6.T7.S2<br/>docs/DEPLOY.md walkthrough]
        T7_S3[P6.T7.S3<br/>docs/RUNBOOK.md operations]
        T7_S4[P6.T7.S4<br/>First production deploy + verify]
    end

    T1_S1 --> T1_S3
    T1_S2 --> T1_S3
    T1_S4 --> T1_S3
    T1_S5 --> T1_S3
    T1_S3 --> T1_S6

    T2_S1 --> T2_S2
    T2_S1 --> T2_S3

    T3_S1 --> T3_S2
    T3_S3 --> T3_S2
    T3_S2 --> T3_S4
    T3_S4 --> T3_S5
    T3_S2 --> T3_S6
    T3_S6 --> T3_S7

    T2_S1 --> T4_S1
    T2_S2 --> T4_S1
    T2_S3 --> T4_S1
    T1_S3 --> T4_S1
    T4_S1 --> T4_S2

    T3_S2 --> T4_S1

    T5_S1 --> T5_S2
    T5_S1 --> T5_S3
    T5_S1 --> T5_S4
    T5_S1 --> T5_S5
    T5_S1 --> T5_S6

    T1_S6 --> T6_S1
    T3_S2 --> T6_S1
    T6_S1 --> T6_S2
    T5_S2 --> T6_S2
    T5_S3 --> T6_S2
    T5_S4 --> T6_S2
    T5_S5 --> T6_S2
    T5_S6 --> T6_S2
    T6_S2 --> T6_S3

    T6_S1 --> T7_S4
    T3_S7 --> T7_S4
    T4_S2 --> T7_S4
    T7_S4 --> T7_S1
    T7_S4 --> T7_S2
    T7_S4 --> T7_S3

    classDef phaseA fill:#1e3a5f,stroke:#fff,color:#fff
    classDef phaseB fill:#5f1e3a,stroke:#fff,color:#fff
    classDef phaseC fill:#1f5f3a,stroke:#fff,color:#fff
```

**Parallelization callouts** for an orchestrating agent:

- **Wave 1** (after Stage 5 complete): `P6.T1.*` (containerization), `P6.T2.*` (env-aware backend), `P6.T3.S1`/`P6.T3.S3` (Terraform skeleton), `P6.T5.S1` (smoke test fixtures) all parallel — different files, different concerns.
- **Wave 2**: After Dockerfile lands, `P6.T6.S1` (GitHub integration setup) parallelizes with `P6.T3.S2`–`P6.T3.S6` (Terraform resources). Smoke tests `P6.T5.S2`–`P6.T5.S6` parallelize entirely (each is independent).
- **Wave 3**: Pre-deploy migration hook `P6.T4` blocks on Terraform service config; `P6.T6.S2` (smoke test workflow) blocks on smoke tests + Railway being deployable.
- **Highest-risk path**: T1_S5 (supervisord process mgmt) → T1_S3 (combined image) → T7_S4 (first deploy verify). If signal forwarding is wrong, Railway can't restart cleanly. Test with `docker stop` + `docker run --rm` cycles before pushing.
- **Final integration sub-task**: `P6.T7.S4` (first production deploy + verify) is the genuine sync point of the entire stage — everything else feeds into it.

---

## Phase A: Containerization & Environment-Aware Backend

### Task P6.T1: Application container

**Feature**: Containerization
**Effort**: XL / 1.5–2 days
**Dependencies**: All Stage 5 features working in dev
**Risk Level**: Medium (single-container nginx+uvicorn pattern has process-management subtleties)

#### Sub-task P6.T1.S1: Backend Dockerfile multi-stage

**Description**: A multi-stage Dockerfile that produces a slim Python image with FastAPI + all deps. Stage 1 builds the wheel; Stage 2 is the minimal runtime.

**Implementation Hints**:
- File: `infra/docker/Dockerfile.app` (the combined image is built in P6.T1.S3; this sub-task builds the backend portion as one stage).
- Base: `python:3.12-slim-bookworm`. Pinned for reproducibility; `slim` reduces size vs default.
- Stage 1 (builder):
  - Install `uv` (`pip install uv` or download from astral.sh release).
  - Copy `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version`.
  - `uv sync --frozen --no-dev` to install runtime deps only.
  - This produces a `.venv/` directory we can copy to runtime.
- Stage 2 (runtime placeholder — will be combined with frontend in P6.T1.S3):
  - Copy `.venv/` from builder.
  - Copy `backend/app/`.
  - User: non-root (`appuser` UID 1000).
  - `WORKDIR /app/backend`.
- Health check at this stage: `python -c "from app.app import create_app; create_app()"` smoke test in CI build step.

**Dependencies**: Stage 5 backend code
**Effort**: M / 4 hours
**Risk Flags**: `uv sync --frozen --no-dev` may differ from boilerplate's existing `uv sync`. Verify the runtime `.venv/` is functional.
**Acceptance Criteria**:
- `docker build --target backend -t app-backend .` succeeds.
- Image size <300 MB.
- `docker run --rm app-backend python -c "from app.app import create_app; print('ok')"` prints `ok`.

#### Sub-task P6.T1.S2: Frontend build stage

**Description**: Add a parallel build stage in the same Dockerfile that runs `npm install` + `npm run build` to produce the static `dist/` directory.

**Implementation Hints**:
- Stage in `Dockerfile.app`:
  - Base: `node:20-alpine`.
  - Copy `frontend/package.json`, `frontend/package-lock.json`.
  - `npm ci` (deterministic install vs `npm install`).
  - Copy `frontend/`.
  - `npm run build` → produces `frontend/dist/`.
- Output is consumed by the combined image stage (P6.T1.S3) which `COPY --from=frontend-build /frontend/dist /usr/share/nginx/html`.

**Dependencies**: Stage 5 frontend code
**Effort**: S / 2 hours
**Risk Flags**: Vite's build may need env var injection for production API base URL — but with same-domain topology, the default relative `/api/v1/...` paths just work. Verify in build.
**Acceptance Criteria**:
- `docker build --target frontend-build -t app-frontend .` succeeds.
- The resulting `dist/` is <2 MB compressed.
- Manual sanity: extract dist, serve with `python -m http.server`, app loads.

#### Sub-task P6.T1.S3: Combined image — nginx + uvicorn + static

**Description**: Final stage combining the backend `.venv/` and `app/` with the frontend `dist/`, with nginx and supervisord installed.

**Implementation Hints**:
- Base: `python:3.12-slim-bookworm`.
- Install system deps: `nginx` and `supervisor` via `apt-get install -y`.
- COPY from frontend-build stage to `/usr/share/nginx/html`.
- COPY from backend-build stage `.venv/` and `app/` to `/app/backend/`.
- COPY `infra/docker/nginx.conf` to `/etc/nginx/nginx.conf` (replaces default).
- COPY `infra/docker/supervisord.conf` to `/etc/supervisor/conf.d/supervisord.conf`.
- COPY a small `entrypoint.sh` that runs `dumb-init -- supervisord -n -c /etc/supervisor/conf.d/supervisord.conf`.
- EXPOSE 8080 (Railway's default port; configurable via `PORT` env var — the entrypoint reads `$PORT` and passes to nginx via env substitution).
- Final image USER: `appuser`. Both nginx and uvicorn run as non-root.
- HEALTHCHECK: `curl -f http://localhost:${PORT:-8080}/api/v1/health || exit 1`.

**Dependencies**: P6.T1.S1, P6.T1.S2, P6.T1.S4, P6.T1.S5
**Effort**: M / 4 hours
**Risk Flags**: Running nginx as non-root requires that the listening port is >1024. Use 8080 (Railway default), not 80. Also requires `chown` of nginx state directories during image build. The `nginx:alpine` image solves this; we're rolling our own from python-slim, so set up perms manually.
**Acceptance Criteria**:
- `docker build -t app:latest .` produces a single image <500 MB.
- `docker run --rm -p 8080:8080 -e DATABASE_URL=... -e VALKEY_URL=... -e S3_ENDPOINT_URL=... [...] app:latest` starts.
- Browsing `http://localhost:8080` shows the app login page.
- `curl http://localhost:8080/api/v1/health` returns 200.

#### Sub-task P6.T1.S4: nginx.conf path routing

**Description**: nginx config that serves static at `/*` and proxies `/api/*` and `/ws/*` to uvicorn on `127.0.0.1:8000`.

**Implementation Hints**:
- File: `infra/docker/nginx.conf`.
- Skeleton:
  ```nginx
  user appuser;
  worker_processes auto;
  pid /tmp/nginx.pid;
  
  events { worker_connections 1024; }
  
  http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    
    upstream backend { server 127.0.0.1:8000; }
    
    server {
      listen ${PORT};
      server_name _;
      root /usr/share/nginx/html;
      index index.html;
      
      # API proxy
      location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_pass_request_headers on;
        proxy_buffering off;
        client_max_body_size 25M;  # matches our largest upload (attachment)
      }
      
      # WebSocket proxy
      location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400s;  # 24h; long-lived WS connections
        proxy_send_timeout 86400s;
      }
      
      # SPA fallback
      location / {
        try_files $uri $uri/ /index.html;
      }
      
      # Static asset caching
      location ~* \.(js|css|png|jpg|jpeg|webp|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
      }
    }
  }
  ```
- `${PORT}` is substituted by `envsubst` at container start (entrypoint script).
- `client_max_body_size 25M` — must match or exceed our largest upload (attachments cap from Stage 5). Anything larger is rejected by nginx before reaching FastAPI.
- WebSocket timeouts long enough for typical editing sessions.
- SPA fallback ensures React Router routes resolve to `index.html`.

**Dependencies**: None (config-only)
**Effort**: M / 3 hours
**Risk Flags**: WebSocket proxying requires `Upgrade`/`Connection` headers exactly right; missing them silently breaks WS. Test with browser DevTools.
**Acceptance Criteria**:
- `nginx -t -c /etc/nginx/nginx.conf` passes inside the container.
- API requests reach FastAPI; static is served correctly.
- WebSocket connects in browser DevTools (Network → WS).
- SPA route like `/dashboard` returns 200 with `index.html`.

#### Sub-task P6.T1.S5: supervisord.conf process management

**Description**: supervisord config that launches and manages nginx + uvicorn as child processes. Forwards SIGTERM to both for graceful shutdown.

**Implementation Hints**:
- File: `infra/docker/supervisord.conf`.
- ```ini
  [supervisord]
  nodaemon=true
  user=appuser
  logfile=/dev/null
  logfile_maxbytes=0
  pidfile=/tmp/supervisord.pid
  
  [program:nginx]
  command=/bin/sh -c "envsubst '${PORT}' < /etc/nginx/nginx.conf > /tmp/nginx.conf && nginx -c /tmp/nginx.conf -g 'daemon off;'"
  autostart=true
  autorestart=true
  stdout_logfile=/dev/stdout
  stdout_logfile_maxbytes=0
  stderr_logfile=/dev/stderr
  stderr_logfile_maxbytes=0
  priority=20
  
  [program:uvicorn]
  command=uv run uvicorn app.app:create_app --factory --host 127.0.0.1 --port 8000 --workers 2
  directory=/app/backend
  autostart=true
  autorestart=true
  stdout_logfile=/dev/stdout
  stdout_logfile_maxbytes=0
  stderr_logfile=/dev/stderr
  stderr_logfile_maxbytes=0
  priority=10  # start uvicorn before nginx
  ```
- `priority=10` for uvicorn ensures it starts first; nginx starts after at priority 20.
- Logs to stdout/stderr so Railway captures them.
- `--workers 2` is conservative for Railway's free tier; tune in P6.T7 based on observed perf.
- Graceful shutdown: supervisord forwards SIGTERM. Each child process gets it; nginx and uvicorn both handle SIGTERM correctly. The `dumb-init` wrapper in `entrypoint.sh` ensures supervisord itself receives SIGTERM rather than SIGKILL.

**Dependencies**: None
**Effort**: M / 3 hours
**Risk Flags**: HIGH — process management mistakes here cause Railway's restart policy to fail. Specifically test: `docker run` then `docker kill --signal SIGTERM` and verify both processes shut down within 30 seconds.
**Acceptance Criteria**:
- Container starts both processes.
- Both processes' logs appear on container stdout.
- `docker kill -s SIGTERM <container>` results in clean shutdown within 30s.
- One process crashing → supervisord restarts it.

#### Sub-task P6.T1.S6: .dockerignore + prod-like compose

**Description**: A `.dockerignore` to prevent build-context bloat. A `docker-compose.prod.yml` for local "prod-like" sanity testing before pushing.

**Implementation Hints**:
- `.dockerignore` at repo root:
  ```
  .git
  .github
  **/node_modules
  **/.venv
  **/__pycache__
  **/dist
  **/build
  **/.pytest_cache
  docs
  *.md
  .env*
  !.env.example
  infra/terraform
  ```
- `docker-compose.prod.yml` next to `docker-compose.yml`:
  ```yaml
  services:
    app:
      build:
        context: .
        dockerfile: infra/docker/Dockerfile.app
      ports:
        - "8080:8080"
      environment:
        - PORT=8080
        - DATABASE_URL=postgresql+asyncpg://app:app@postgres:5432/docs_dev
        - VALKEY_URL=redis://valkey:6379/0
        - S3_ENDPOINT_URL=http://minio:9000
        - S3_ACCESS_KEY=minioadmin
        - S3_SECRET_KEY=minioadmin
        - S3_ADDRESSING_STYLE=path
        - S3_BUCKET_DOCUMENTS=docs
        - S3_BUCKET_SNAPSHOTS=snapshots
        - S3_BUCKET_ATTACHMENTS=attachments
        - ENVIRONMENT=production
        - LOG_LEVEL=INFO
        - BCRYPT_COST=12
        - SESSION_COOKIE_SECURE=false  # local-only; true in real prod
        - CORS_ORIGINS=http://localhost:8080
      depends_on:
        postgres: { condition: service_healthy }
        valkey: { condition: service_healthy }
        minio: { condition: service_healthy }
  ```
- Reuses Postgres/Valkey/MinIO services from existing `docker-compose.yml` via `extends:` or by sharing the file structure.
- Documented in README: "Local prod-like test: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up`".

**Dependencies**: P6.T1.S3
**Effort**: S / 2 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` brings up all services.
- App reachable at `http://localhost:8080`.
- Manual smoke: login, create doc, edit, share, import, image upload all work.
- `.dockerignore` keeps build context under 50 MB.

---

### Task P6.T2: Environment-aware backend

**Feature**: Configuration / 12-factor
**Effort**: M / 4-6 hours
**Dependencies**: Stage 1 Settings class
**Risk Level**: Low (mostly mechanical config flips)

#### Sub-task P6.T2.S1: Settings detects RAILWAY_ENVIRONMENT

**Description**: The `Settings` class (S1 P1.T3.S5) already declares all env-driven fields. This sub-task adds Railway-specific defaults that activate when `RAILWAY_ENVIRONMENT` is set.

**Implementation Hints**:
- File: `backend/app/features/core/settings.py`.
- Add a derived field:
  ```python
  @computed_field
  @property
  def is_railway(self) -> bool:
      return bool(os.getenv("RAILWAY_ENVIRONMENT"))
  ```
- The actual values are still env-driven (Terraform sets them); this is just a sanity check used in code paths that need to know.
- For code that genuinely needs to switch behavior based on Railway presence (e.g., trusting `X-Forwarded-For`), use this property.
- Document in `core/settings.py` README: "All deployment-specific config is via env vars; this property exists only for the rare cases where code logic differs."

**Dependencies**: Stage 1 Settings
**Effort**: S / 1 hour
**Risk Flags**: None.
**Acceptance Criteria**:
- Setting `RAILWAY_ENVIRONMENT=production` makes `settings.is_railway` return True.
- Test in `core/test_settings.py`.

#### Sub-task P6.T2.S2: core/storage.py addressing style switch

**Description**: The S3 client in `core/storage.py` (S1 P1.T3.S8) reads `s3_addressing_style` from settings. This sub-task verifies it actually works with both MinIO (path) and Railway Buckets (virtual-hosted).

**Implementation Hints**:
- The code is already in place from S1; no changes needed beyond verification.
- Verification: deploy to Railway in P6.T7.S4 and confirm presigned PUT against Buckets succeeds with virtual-hosted style.
- If issues surface, fall back to path style for Railway Buckets too (Railway docs note older buckets may need path style — see global compatibility notes).

**Dependencies**: Stage 1 storage helper
**Effort**: XS / 1 hour
**Risk Flags**: None at code level; deployment verification handles real-world test.
**Acceptance Criteria**:
- With `S3_ADDRESSING_STYLE=virtual` and Railway Buckets endpoint, presigned PUT URL works against the bucket from a browser.
- With `S3_ADDRESSING_STYLE=path` and MinIO endpoint, presigned PUT URL works against MinIO from a browser.

#### Sub-task P6.T2.S3: Cookie Secure + log level + bcrypt cost

**Description**: Production-only env values that flip behavior. Already declared as Settings fields; this sub-task ensures the deploy actually sets them.

**Implementation Hints**:
- Production env vars (set via Terraform in P6.T3.S2):
  - `SESSION_COOKIE_SECURE=true`
  - `SESSION_COOKIE_SAMESITE=lax` (same-domain, Lax is fine; would need `none` for cross-origin)
  - `LOG_LEVEL=INFO`
  - `BCRYPT_COST=12`
  - `DEBUG=false`
- Dev defaults remain: `Secure=false`, `LOG_LEVEL=DEBUG`, `BCRYPT_COST=10`, `DEBUG=true`.
- The CSRF middleware (S2 P1.T2.S7): with same-domain prod, `SameSite=Lax` is sufficient + double-submit cookie. No code changes.

**Dependencies**: P6.T2.S1
**Effort**: S / 1 hour
**Risk Flags**: `Secure=true` cookies require HTTPS — Railway provides this automatically. Don't accidentally test with HTTP from a browser; the cookie won't be sent.
**Acceptance Criteria**:
- Setting all five env vars in `docker-compose.prod.yml` and starting the local prod-like compose works.
- Deployed prod cookies have `Secure` flag visible in DevTools.

---

## Phase B: Terraform & Infrastructure

### Task P6.T3: Terraform infrastructure

**Feature**: Infrastructure-as-Code
**Effort**: XL / 1.5–2 days
**Dependencies**: P6.T1 (Dockerfile exists), P6.T2 (settings env-aware)
**Risk Level**: Medium (R4 — provider may not handle Buckets)

#### Sub-task P6.T3.S1: versions.tf + provider config

**Description**: Pin Terraform and the Railway provider versions; configure provider authentication.

**Implementation Hints**:
- File: `infra/terraform/versions.tf`.
- ```hcl
  terraform {
    required_version = ">= 1.6"
    required_providers {
      railway = {
        source  = "terraform-community-providers/railway"
        version = "~> 0.5"  # pin to current major; verify exact at impl time
      }
    }
  }
  
  provider "railway" {
    token = var.railway_api_token
  }
  ```
- `railway_api_token` is a sensitive variable; documented that user must set it via env var `TF_VAR_railway_api_token` or `terraform.tfvars`.
- README explicitly says: never commit the token.

**Dependencies**: None
**Effort**: S / 2 hours
**Risk Flags**: Provider version may drift; check for breaking changes between minor versions.
**Acceptance Criteria**:
- `terraform init` succeeds (downloads provider).
- Setting an invalid token, then `terraform plan` produces a clear auth error.

#### Sub-task P6.T3.S2: main.tf — project + service + plugins

**Description**: Declare Railway resources: project, environment, service, managed Postgres plugin, managed Redis plugin, environment variables.

**Implementation Hints**:
- File: `infra/terraform/main.tf`.
- ```hcl
  resource "railway_project" "this" {
    name = var.project_name
    description = "Collaborative document editor"
  }
  
  data "railway_environment" "production" {
    project_id = railway_project.this.id
    name = "production"
  }
  
  resource "railway_service" "app" {
    project_id = railway_project.this.id
    name = "app"
    source_repo = var.github_repo
    source_repo_branch = "main"
    config_path = "infra/docker/railway.json"  # Railway-specific build config
  }
  
  resource "railway_plugin" "postgres" {
    project_id = railway_project.this.id
    name = "postgresql"
  }
  
  resource "railway_plugin" "redis" {
    project_id = railway_project.this.id
    name = "redis"
  }
  ```
- Note: provider resource names + arguments may differ from these sketches; check provider docs at impl time. The intent is captured.
- A separate `infra/docker/railway.json` file tells Railway how to build this service: `{"$schema": "https://railway.com/railway.schema.json", "build": {"builder": "DOCKERFILE", "dockerfilePath": "infra/docker/Dockerfile.app"}, "deploy": {"startCommand": "/usr/local/bin/entrypoint.sh", "healthcheckPath": "/api/v1/health", "preDeployCommand": "cd backend && uv run alembic upgrade head"}}`.
- Environment variables on the service:
  - `DATABASE_URL = railway_plugin.postgres.connection_string` (provider exposes managed plugin URL)
  - `VALKEY_URL = railway_plugin.redis.connection_string`
  - `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ADDRESSING_STYLE=virtual`, `S3_BUCKET_*` from Buckets (post-bootstrap)
  - `ENVIRONMENT=production`, `SESSION_COOKIE_SECURE=true`, `LOG_LEVEL=INFO`, `BCRYPT_COST=12`, `DEBUG=false`
  - `CSRF_SECRET_KEY`, generated as `terraform`'s `random_password.csrf` resource
  - `CORS_ORIGINS` = empty (same-domain, no CORS needed) OR the Railway-assigned domain if needed
- Use `railway_variable` resources to set each, scoped to the production environment.

**Dependencies**: P6.T3.S1, P6.T3.S3
**Effort**: L / 1 day
**Risk Flags**: Provider's exact resource shape may not match this sketch; budget time for trial-and-error against the provider docs. Some providers expose plugin URLs as `${{plugin.connection_string}}` interpolation, which Terraform must understand.
**Acceptance Criteria**:
- `terraform plan` produces a clean plan with all expected resources.
- `terraform apply` on a fresh Railway account creates everything in <10 min.
- The Railway dashboard shows the project, service, plugins.

#### Sub-task P6.T3.S3: variables.tf + tfvars.example

**Description**: Declare all input variables and provide an example file.

**Implementation Hints**:
- File: `infra/terraform/variables.tf`:
  ```hcl
  variable "railway_api_token" {
    type = string
    sensitive = true
    description = "Railway API token. Create at railway.app → Account Settings → Tokens."
  }
  variable "project_name" {
    type = string
    default = "collaborative-doc-editor"
  }
  variable "github_repo" {
    type = string
    description = "GitHub repository in 'owner/repo' format."
  }
  variable "github_repo_branch" {
    type = string
    default = "main"
  }
  variable "custom_domain" {
    type = string
    default = null
    description = "Optional custom domain (e.g., yourapp.com). Leave null to use Railway-provided *.up.railway.app."
  }
  ```
- File: `infra/terraform/terraform.tfvars.example`:
  ```hcl
  # Copy to terraform.tfvars and fill in.
  # NEVER commit terraform.tfvars (it's in .gitignore).
  railway_api_token = "your-railway-token-here"
  github_repo       = "your-username/your-repo"
  custom_domain     = null
  ```
- `infra/terraform/.gitignore`:
  ```
  terraform.tfvars
  *.tfstate
  *.tfstate.backup
  .terraform/
  .terraform.lock.hcl
  ```

**Dependencies**: None
**Effort**: S / 2 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- `terraform validate` passes.
- Example tfvars is comprehensive.

#### Sub-task P6.T3.S4: Buckets bootstrap script + import

**Description**: Per global risk R4, the Terraform Railway provider may not support Buckets. Workaround: a one-time script that uses Railway CLI to create the bucket, then `terraform import` to bring it into state. Subsequent `terraform plan/apply` cycles see the bucket as managed.

**Implementation Hints**:
- File: `scripts/bootstrap_railway_buckets.sh` (Linux/macOS) and `.ps1` (Windows).
- Logic:
  ```bash
  #!/bin/bash
  set -e
  PROJECT_ID="$1"
  ENV_ID="$2"
  if [ -z "$PROJECT_ID" ] || [ -z "$ENV_ID" ]; then
    echo "Usage: $0 <project_id> <environment_id>"
    exit 1
  fi
  echo "Creating Railway Buckets in project $PROJECT_ID..."
  # Railway CLI command (verify exact syntax at impl time)
  railway buckets create --project="$PROJECT_ID" --environment="$ENV_ID" --name=app-bucket --region=us-east1
  echo "Bucket created. Run 'terraform import railway_bucket.this <id>' next."
  ```
- The script's output includes the new bucket ID, which the user provides to `terraform import`.
- README documents this as a one-time post-init step: "After first `terraform apply`, run `scripts/bootstrap_railway_buckets.sh <project_id> <env_id>`. Then update `main.tf` to declare the bucket resource (commented stub provided), and run `terraform import railway_bucket.this <id>`."
- If the provider DOES support Buckets at impl time (provider may have caught up), this sub-task simplifies dramatically — just declare a `railway_bucket` resource. Check provider docs.

**Dependencies**: P6.T3.S2
**Effort**: M / 4 hours
**Risk Flags**: This is the highest-uncertainty sub-task. Check provider releases at impl time. If provider supports Buckets, swap to declarative. If not, the manual flow stands.
**Acceptance Criteria**:
- Script creates a Railway bucket.
- Manual `terraform import` brings it under management.
- Subsequent `terraform plan` shows no diff (bucket already exists in state).
- README documents the flow clearly.

#### Sub-task P6.T3.S5: Buckets CORS via null_resource

**Description**: Configure Railway Buckets CORS to allow PUT + GET + HEAD from the production domain. Required for the browser direct-to-S3 image upload from Stage 5.

**Implementation Hints**:
- Buckets is S3-compatible; CORS is set via `aws s3api put-bucket-cors` against the Railway endpoint.
- ```hcl
  resource "null_resource" "bucket_cors" {
    depends_on = [railway_bucket.this]
    triggers = {
      bucket_id = railway_bucket.this.id
      cors_hash = sha256(file("${path.module}/bucket-cors.json"))
    }
    provisioner "local-exec" {
      command = <<-EOT
        AWS_ACCESS_KEY_ID=${railway_bucket.this.access_key} \
        AWS_SECRET_ACCESS_KEY=${railway_bucket.this.secret_key} \
        aws s3api put-bucket-cors \
          --bucket ${railway_bucket.this.name} \
          --endpoint-url ${railway_bucket.this.endpoint} \
          --cors-configuration file://${path.module}/bucket-cors.json
      EOT
    }
  }
  ```
- File: `infra/terraform/bucket-cors.json`:
  ```json
  {
    "CORSRules": [{
      "AllowedOrigins": ["https://yourapp.up.railway.app"],
      "AllowedMethods": ["PUT", "GET", "HEAD"],
      "AllowedHeaders": ["Content-Type", "Content-Length"],
      "MaxAgeSeconds": 3600
    }]
  }
  ```
- The allowed origin is parameterized via the production domain output (computed in P6.T3.S6).
- Requires `aws` CLI on the machine running `terraform apply`. Documented as a prereq.

**Dependencies**: P6.T3.S4
**Effort**: M / 3 hours
**Risk Flags**: This Terraform null_resource pattern with `local-exec` is a known anti-pattern but unavoidable when a provider lacks first-class support. Document clearly.
**Acceptance Criteria**:
- After `terraform apply`, browser PUT from frontend to Buckets URL succeeds (verified via S5 image upload flow in deployed env).
- CORS preflight (OPTIONS) returns the correct allowed-origin header.

#### Sub-task P6.T3.S6: outputs.tf — URLs + bucket name

**Description**: Outputs make the deployment artifacts visible after apply.

**Implementation Hints**:
- File: `infra/terraform/outputs.tf`:
  ```hcl
  output "app_url" {
    value = railway_service.app.public_url
    description = "Production app URL."
  }
  output "bucket_name" {
    value = railway_bucket.this.name
    description = "Railway Buckets name (S3-compatible)."
  }
  output "bucket_endpoint" {
    value = railway_bucket.this.endpoint
    description = "Railway Buckets S3 endpoint URL."
  }
  ```
- The `app_url` is what the user visits in browser after deploy. It's also used as the `BASE_URL` for smoke tests.

**Dependencies**: P6.T3.S2, P6.T3.S4
**Effort**: XS / 1 hour
**Risk Flags**: None.
**Acceptance Criteria**:
- `terraform output` after apply prints the URL and the user can curl it.

#### Sub-task P6.T3.S7: Terraform README + apply walkthrough

**Description**: Step-by-step guide in `infra/terraform/README.md` covering first-time setup, apply, and operations.

**Implementation Hints**:
- Sections:
  1. Prerequisites (Terraform CLI, Railway CLI, aws CLI, Railway API token, GitHub repo)
  2. First-time setup
     1. `cd infra/terraform`
     2. `cp terraform.tfvars.example terraform.tfvars` and fill in
     3. `terraform init`
     4. `terraform apply`
     5. After apply: `scripts/bootstrap_railway_buckets.sh <project_id> <env_id>`
     6. Edit `main.tf` to uncomment bucket resource block
     7. `terraform import railway_bucket.this <bucket_id>`
     8. `terraform apply` again (now CORS configures)
     9. Verify: visit `terraform output app_url`
  3. Subsequent updates: `terraform apply` after any change
  4. Tearing down: `terraform destroy` (with caveats about bucket data)

**Dependencies**: P6.T3.S6
**Effort**: M / 3 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Following the README from a fresh repo + Railway account reaches a working production deployment.

---

### Task P6.T4: Pre-deploy migration hook

**Feature**: Operations
**Effort**: M / 3 hours
**Dependencies**: P6.T3.S2 (railway.json with preDeployCommand)
**Risk Level**: Medium (failed migrations must abort deploy, not silently succeed)

#### Sub-task P6.T4.S1: Railway pre-deploy command config

**Description**: `railway.json` declares the pre-deploy command. Railway runs it in an ephemeral container before swapping traffic to the new service.

**Implementation Hints**:
- File: `infra/docker/railway.json`:
  ```json
  {
    "$schema": "https://railway.com/railway.schema.json",
    "build": {
      "builder": "DOCKERFILE",
      "dockerfilePath": "infra/docker/Dockerfile.app"
    },
    "deploy": {
      "startCommand": "/usr/local/bin/entrypoint.sh",
      "healthcheckPath": "/api/v1/health",
      "healthcheckTimeout": 30,
      "preDeployCommand": "cd /app/backend && uv run alembic upgrade head",
      "restartPolicyType": "ALWAYS",
      "restartPolicyMaxRetries": 3
    }
  }
  ```
- The pre-deploy container has access to all env vars (including `DATABASE_URL`).
- Migration runs after the new container image is built but before the new service replaces the old.
- If `alembic upgrade head` exits non-zero, Railway aborts the deploy and keeps the old service running.

**Dependencies**: P6.T1.S3 (image with backend installed)
**Effort**: M / 2 hours
**Risk Flags**: Migration time is bounded — Railway typically allows up to 10 min for pre-deploy. For a small project this is fine; large schema changes might need split migrations.
**Acceptance Criteria**:
- After deploying, Railway logs show the pre-deploy command output ending with successful Alembic upgrade.
- Database has new tables/columns from any migrations introduced since last deploy.

#### Sub-task P6.T4.S2: Migration failure aborts deploy

**Description**: Verify that a deliberately-broken migration causes the deploy to fail cleanly.

**Implementation Hints**:
- Create a test migration that intentionally fails (e.g., references a non-existent table).
- Push to main → Railway attempts deploy.
- Expected: deploy fails, old service stays up, Railway dashboard shows red status.
- Revert the broken migration, push again, verify recovery.
- This is a one-time verification, not a permanent test.
- Document the verification in `docs/RUNBOOK.md` so the user knows to verify before relying on the hook.

**Dependencies**: P6.T4.S1
**Effort**: S / 1 hour
**Risk Flags**: None.
**Acceptance Criteria**:
- Verified via deliberate-fail migration test.
- Documented in RUNBOOK.

---

## Phase C: CI/CD, Smoke Tests, Documentation

### Task P6.T5: Smoke test suite

**Feature**: Quality / verification
**Effort**: L / 1 day
**Dependencies**: All Stage 5 features deployed
**Risk Level**: Low

#### Sub-task P6.T5.S1: Pytest fixtures for BASE_URL + demo accounts

**Description**: Pytest configuration that allows the suite to point at any base URL via env var. Fixtures for httpx AsyncClient against the deployed URL, demo account login, etc.

**Implementation Hints**:
- File: `backend/tests/smoke/conftest.py`.
- ```python
  @pytest.fixture(scope="session")
  def base_url() -> str:
      url = os.getenv("BASE_URL")
      if not url:
          pytest.skip("BASE_URL not set; smoke tests skipped")
      return url.rstrip("/")
  
  @pytest.fixture
  async def httpx_client(base_url: str) -> AsyncClient:
      async with AsyncClient(base_url=base_url, follow_redirects=False, timeout=30) as client:
          yield client
  
  @pytest.fixture
  async def alice_session(httpx_client: AsyncClient) -> AuthenticatedSession:
      response = await httpx_client.post("/api/v1/auth/login", json={
          "identifier": "alice@example.com",
          "password": "Password123!",
      })
      assert response.status_code == 200
      yield AuthenticatedSession(client=httpx_client, user=response.json()["user"])
      await httpx_client.post("/api/v1/auth/logout", cookies=httpx_client.cookies)
  ```
- Similar fixtures for `bob_session`, `carol_session`.
- Each test runs in <30 seconds; total suite <5 minutes.

**Dependencies**: Stage 5 deployed
**Effort**: M / 3 hours
**Risk Flags**: Cookies in httpx are a per-client default; ensure logout actually destroys the server-side session, since smoke tests may run repeatedly.
**Acceptance Criteria**:
- `BASE_URL=http://localhost:8080 uv run pytest backend/tests/smoke -v` works against local prod-like compose.
- Smoke tests skip cleanly when `BASE_URL` is unset.

#### Sub-task P6.T5.S2: Auth + doc CRUD smoke test

**Description**: End-to-end test: login as alice, create doc, list docs, rename, delete, logout.

**Implementation Hints**:
- File: `backend/tests/smoke/test_auth_and_docs.py`.
- Single test function covering the linear flow. Failure at any step fails the test.

**Dependencies**: P6.T5.S1
**Effort**: S / 2 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Test runs green against deployed env.

#### Sub-task P6.T5.S3: WebSocket smoke test

**Description**: Login as alice and bob in two clients, both connect to a shared doc's WebSocket, alice sends a Yjs UPDATE, bob receives it.

**Implementation Hints**:
- File: `backend/tests/smoke/test_websocket.py`.
- Use `websockets` library against `wss://<base_url>/ws/docs/{doc_id}` (the URL scheme depends on whether base_url is http or https — derive).
- Cookies extracted from httpx client and attached to ws connection via header.
- Send a SYNC_STEP_1 message, receive SYNC_STEP_2, send a small UPDATE, verify bob receives it.

**Dependencies**: P6.T5.S1
**Effort**: M / 3 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Test runs green against deployed env.
- Times out cleanly within 30s if WS doesn't connect.

#### Sub-task P6.T5.S4: Image upload smoke test

**Description**: Upload a tiny PNG image as alice, verify finalize succeeds, verify GET URL returns the image bytes.

**Implementation Hints**:
- File: `backend/tests/smoke/test_image_upload.py`.
- Use a 1x1 PNG fixture (24 bytes). Upload via the presign + PUT + finalize flow.
- Verify magic-byte validation succeeds (PNG header is correct).

**Dependencies**: P6.T5.S1
**Effort**: M / 3 hours
**Risk Flags**: PUT goes direct to Buckets — CORS must be correctly configured (P6.T3.S5).
**Acceptance Criteria**:
- Test runs green against deployed env.

#### Sub-task P6.T5.S5: Share + permission smoke test

**Description**: Alice creates doc, shares with bob as editor, bob can read + write, alice changes bob's role to viewer, bob can read but not write, alice revokes, bob can't access.

**Implementation Hints**:
- File: `backend/tests/smoke/test_sharing.py`.
- Each role transition verified by attempting an editor-only action and asserting the expected status code.

**Dependencies**: P6.T5.S1
**Effort**: M / 3 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Test runs green.

#### Sub-task P6.T5.S6: Import .md smoke test

**Description**: Alice creates doc, captures cursor at index 0, imports a tiny .md fixture, verifies the doc state contains the imported content.

**Implementation Hints**:
- File: `backend/tests/smoke/test_import.py`.
- Fixture: `# Hello\n\nWorld` (10 bytes).
- Reads the doc state via `GET /documents/{id}/state` after import, decodes Yjs binary, asserts text content includes "Hello" and "World".

**Dependencies**: P6.T5.S1
**Effort**: M / 3 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Test runs green.

---

### Task P6.T6: GitHub Actions workflows

**Feature**: CI/CD
**Effort**: L / 1 day
**Dependencies**: P6.T5 (smoke tests exist), P6.T1 (Dockerfile in place)
**Risk Level**: Low

#### Sub-task P6.T6.S1: Auto-deploy via Railway GitHub integration

**Description**: Configure Railway to watch the GitHub repo and auto-deploy on push to main. This is mostly Railway-side configuration with a GitHub webhook; Terraform handles the linkage.

**Implementation Hints**:
- The `railway_service.app` resource declared in P6.T3.S2 includes `source_repo` and `source_repo_branch = "main"`. After `terraform apply`, Railway connects the repo and deploys on every push to main.
- No GitHub Actions needed for this — it's Railway's built-in feature.
- Document in README: "Pushing to main triggers an auto-deploy. Railway dashboard shows build + deploy status. Smoke tests run separately via the post-deploy workflow."
- A complementary Railway dashboard setting: "Pull Request Environments" — leave OFF for our single-environment scope.

**Dependencies**: P6.T3.S2
**Effort**: S / 2 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Pushing to main: Railway dashboard shows a new build within 2 min; deploy completes within 5 min.
- App URL serves the new code.

#### Sub-task P6.T6.S2: Post-deploy smoke test workflow

**Description**: GitHub Actions workflow that triggers after a Railway deploy completes and runs the smoke test suite. Reports green/red on the PR (if any) or as a check on the merge commit.

**Implementation Hints**:
- File: `.github/workflows/post-deploy-smoke.yml`.
- Trigger: `workflow_dispatch` (manual) + `repository_dispatch` (Railway can hit this via webhook).
- Alternatively, simpler: trigger on `push` to `main`, then add a "wait for deploy" step (poll Railway API for deploy status) before running tests.
- ```yaml
  name: Post-deploy smoke
  on:
    push:
      branches: [main]
    workflow_dispatch:
  jobs:
    smoke:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Wait for Railway deploy
          run: |
            # Poll Railway API for latest deployment status
            ./scripts/wait_for_railway_deploy.sh
          env:
            RAILWAY_API_TOKEN: ${{ secrets.RAILWAY_API_TOKEN }}
            RAILWAY_PROJECT_ID: ${{ secrets.RAILWAY_PROJECT_ID }}
        - uses: astral-sh/setup-uv@v3
        - run: cd backend && uv sync --frozen
        - name: Run smoke tests
          env:
            BASE_URL: ${{ secrets.PRODUCTION_BASE_URL }}
          run: cd backend && uv run pytest tests/smoke -v
  ```
- `scripts/wait_for_railway_deploy.sh` polls Railway's GraphQL API until the latest deployment for our service is "SUCCESS" or fails after timeout (~10 min).
- GitHub repo secrets: `RAILWAY_API_TOKEN`, `RAILWAY_PROJECT_ID`, `PRODUCTION_BASE_URL`.

**Dependencies**: P6.T5, P6.T6.S1
**Effort**: L / 1 day
**Risk Flags**: Railway API for "wait for deploy" is GraphQL; may need a small Python script rather than shell. Document.
**Acceptance Criteria**:
- Pushing to main triggers deploy → smoke tests run → green check on the commit within 10 min.
- A deliberate failure (e.g., break a smoke test) fails the workflow.

#### Sub-task P6.T6.S3: Tag-triggered release workflow

**Description**: GitHub Actions workflow on `v*.*.*` tag push. Runs smoke tests against the just-deployed prod, generates release notes from PR titles since last tag, creates a GitHub Release.

**Implementation Hints**:
- File: `.github/workflows/release.yml`.
- ```yaml
  name: Release
  on:
    push:
      tags: ['v*.*.*']
  jobs:
    release:
      runs-on: ubuntu-latest
      permissions: { contents: write }
      steps:
        - uses: actions/checkout@v4
          with: { fetch-depth: 0 }
        - uses: astral-sh/setup-uv@v3
        - name: Wait for Railway deploy of this tag
          run: ./scripts/wait_for_railway_deploy.sh
          env:
            RAILWAY_API_TOKEN: ${{ secrets.RAILWAY_API_TOKEN }}
            RAILWAY_PROJECT_ID: ${{ secrets.RAILWAY_PROJECT_ID }}
        - name: Run smoke tests
          env:
            BASE_URL: ${{ secrets.PRODUCTION_BASE_URL }}
          run: cd backend && uv sync --frozen && uv run pytest tests/smoke -v
        - name: Generate release notes
          id: notes
          run: |
            PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
            if [ -n "$PREV_TAG" ]; then
              git log "${PREV_TAG}..HEAD" --pretty=format:"- %s" --merges > /tmp/release-notes.md
            else
              echo "Initial release" > /tmp/release-notes.md
            fi
        - uses: softprops/action-gh-release@v1
          with:
            body_path: /tmp/release-notes.md
            generate_release_notes: false
  ```
- Acts as a release gate: if smoke tests fail, no release is created.
- Tags follow semver: `v1.0.0`, `v1.1.0`, etc.

**Dependencies**: P6.T6.S2 (reuses smoke test infrastructure)
**Effort**: M / 4 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Pushing tag `v0.1.0` triggers workflow → smoke tests pass → GitHub Release `v0.1.0` is created with notes.
- Workflow fails cleanly if smoke tests fail.

---

### Task P6.T7: Documentation + first deploy + handoff

**Feature**: Documentation / quality
**Effort**: M / 4-6 hours
**Dependencies**: All other tasks
**Risk Level**: Low

#### Sub-task P6.T7.S1: README "Deployment" section

**Description**: Top-level README gets a deployment section with high-level info; details deferred to `docs/DEPLOY.md`.

**Implementation Hints**:
- New section in README:
  ```markdown
  ## Deployment
  
  Production deployment runs on Railway.com with managed Postgres + Redis + Buckets.
  
  - One-time setup: see `docs/DEPLOY.md`.
  - Auto-deploy on push to `main`.
  - Smoke tests auto-run after each deploy via GitHub Actions.
  - Tagged releases (`vX.Y.Z`) trigger the release workflow.
  - Operations runbook: `docs/RUNBOOK.md`.
  ```

**Dependencies**: All others
**Effort**: S / 1 hour
**Risk Flags**: None.
**Acceptance Criteria**:
- Section is concise (≤30 lines) and links out for detail.

#### Sub-task P6.T7.S2: docs/DEPLOY.md walkthrough

**Description**: Comprehensive first-deploy guide that a new contributor can follow start-to-finish.

**Implementation Hints**:
- Sections:
  1. Prerequisites (Railway account, GitHub repo with admin, Terraform CLI, Railway CLI, aws CLI for CORS, Docker for local prod-like test)
  2. Create Railway API token (link to Railway Account Settings)
  3. Set up Terraform
  4. First `terraform apply`
  5. Buckets bootstrap (if provider doesn't support natively)
  6. Post-Buckets re-apply
  7. Verify: visit `terraform output app_url`
  8. Sign in as alice; create a doc; verify everything works
  9. Configure GitHub repo secrets for the smoke-test and release workflows
  10. Push a small change to main; verify auto-deploy
  11. Tag `v0.1.0`; verify release workflow

**Dependencies**: P6.T7.S4
**Effort**: M / 3 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- A new contributor can follow this and reach a working deploy.

#### Sub-task P6.T7.S3: docs/RUNBOOK.md operations

**Description**: Operations playbook for common scenarios.

**Implementation Hints**:
- Scenarios to cover:
  1. **Deploy failed at build**: Railway dashboard logs → fix Dockerfile → push.
  2. **Deploy failed at pre-deploy migration**: Railway logs → identify failing migration → revert PR or hotfix → push.
  3. **Deploy succeeded but app crashed at runtime**: Railway logs → identify error → check env vars in Railway dashboard.
  4. **Smoke tests fail post-deploy**: Investigate from the test output → most often a flaky test or a real regression.
  5. **Secret rotation**: Update Railway env var via dashboard or `terraform apply` after editing tfvars.
  6. **Scaling**: Railway's per-service replicas + memory tuning; this app's bottleneck is likely Postgres connection pool.
  7. **Manual rollback**: Railway dashboard → previous successful deploy → "Redeploy". Note: doesn't undo migrations; document SQL-level rollback if a migration is the issue.
  8. **Buckets data loss / restore**: Buckets is durable; data loss is highly unlikely but covered as "no automated backups in this stage; use manual `aws s3 sync` for backups".
  9. **WebSocket connection issues**: nginx config check, Railway's HTTP/2 vs HTTP/1.1 considerations.
  10. **Observability**: Railway logs + structlog JSON output. No external observability stack in MVP.

**Dependencies**: All others
**Effort**: M / 3 hours
**Risk Flags**: None.
**Acceptance Criteria**:
- Each scenario has clear steps.
- Includes commands and expected outputs.

#### Sub-task P6.T7.S4: First production deploy + verification

**Description**: Actually running the first deploy. This is the integration moment of the entire stage — and the project. This sub-task is **not** code; it's an executed checklist.

**Implementation Hints**:
- Follow `docs/DEPLOY.md` from a clean Railway account.
- Verify each step's success before continuing.
- Capture any deviations as updates to DEPLOY.md.
- Run the smoke test suite manually with `BASE_URL=https://...`.
- Run the full DEMO.md walkthrough manually in a browser.
- Capture screenshots / a brief video for the README's "What's deployed" section (optional).
- Fix anything broken; iterate.

**Dependencies**: All others
**Effort**: M / 4 hours
**Risk Flags**: This is where Stage 6 risks materialize — anything missed in the plan surfaces here. Budget time for unexpected issues.
**Acceptance Criteria**:
- Production app is live at the Railway URL.
- All smoke tests pass against the deployed URL.
- DEMO.md walkthrough runs end-to-end in browser against the deployed URL.
- DEPLOY.md updated with any deviations or learnings.
- A `v0.1.0` git tag is pushed; release workflow runs successfully; GitHub Release exists.

---

## Appendix

### Glossary

- **Railway**: The PaaS we deploy to.
- **Railway plugin**: Managed primitive (Postgres, Redis) provisioned via the Railway dashboard or Terraform.
- **Railway Buckets**: Railway's S3-compatible managed object storage primitive.
- **Pre-deploy hook**: Railway-feature; runs a command in an ephemeral container before swapping traffic to a new deploy.
- **same-domain topology**: Frontend at `/*` and backend at `/api/*` and `/ws/*` on a single Railway service.
- **null_resource**: Terraform resource that runs an arbitrary `local-exec` provisioner — used here as a workaround for unsupported provider features.

### Full Risk Register (Stage 6)

| ID | Risk | Mitigation | Sub-task |
|---|---|---|---|
| S6-R1 | Terraform Railway provider doesn't support Buckets | CLI bootstrap + import workaround | P6.T3.S4 |
| S6-R2 | nginx + uvicorn signal handling broken under supervisord | Test SIGTERM cycle locally before pushing | P6.T1.S5 |
| S6-R3 | Pre-deploy migration timeout on large schema change | Split migrations; use Railway's migration timeout settings | P6.T4.S1 |
| S6-R4 | Buckets CORS misconfigured → image upload fails | aws s3api put-bucket-cors via null_resource; verify in smoke test | P6.T3.S5 |
| S6-R5 | Smoke tests flaky against newly-deployed env (warmup) | Add 5s sleep after deploy-success before tests; or retry once | P6.T6.S2 |
| S6-R6 | Cookie Secure breaks in local dev | Env-driven; Secure=false in dev compose | P6.T2.S3 |
| S6-R7 | WebSocket connection drops behind Railway's edge router | Long timeouts in nginx.conf (24h) + frontend reconnect (S4) | P6.T1.S4 |
| S6-R8 | Railway's auto-deploy triggers on noise (docs-only changes) | Path filters in `.railwayignore` for docs/, *.md | P6.T6.S1 |
| S6-R9 | Single-container model concentrates failure domain | Acceptable for MVP; Phase 2 considers separate frontend service | (architectural) |
| S6-R10 | First deploy reveals issues not covered by local prod-like compose | P6.T7.S4 explicitly buffered; iterate | P6.T7.S4 |

### Assumptions Log (Stage 6 specific)

| ID | Assumption |
|---|---|
| S6-A1 | Single Railway service hosting both backend and frontend in one container. Suitable for MVP scale; revisit if traffic or team size grows. |
| S6-A2 | One production environment only. PR previews disabled. |
| S6-A3 | Auto-deploy on push to main. No staging environment for promotion gating; smoke tests act as the gate. |
| S6-A4 | Migrations run in pre-deploy hook. Forward-only (no automated rollback). Bad migrations are reverted via revert PR + new deploy. |
| S6-A5 | Smoke tests run against prod after every deploy. Failure of smoke tests does NOT auto-rollback; user investigates manually. (Auto-rollback on smoke failure is a Stage 7 enhancement.) |
| S6-A6 | Railway free / starter plan is sufficient for demo scale. Cost: rough estimate $5-20/mo for compute + Postgres + Redis + small Buckets usage. |
| S6-A7 | No CDN in front of Railway. Static assets served via nginx with long cache headers. Acceptable for MVP. |
| S6-A8 | No external observability (Datadog, Sentry, etc.). Railway's built-in logs are the observability layer for MVP. |
| S6-A9 | Bucket data has no automated backup. Manual `aws s3 sync` is the documented backup procedure. |
| S6-A10 | The Railway region is left to default (likely us-east1). Latency to other regions is acceptable for MVP. |

### Stage-6 Final Project Handoff Checklist

This is the final stage of the project. Before declaring "done":

- [ ] All P6 exit criteria checked
- [ ] Production deploy is live at a stable Railway URL
- [ ] DEMO.md script runs end-to-end against production URL in browser
- [ ] Smoke test suite green against production
- [ ] At least one `v*.*.*` tag pushed; release workflow succeeded; GitHub Release created
- [ ] All 5 demo accounts work in production
- [ ] WebSocket collaboration works between two real browsers (verified manually)
- [ ] Image upload + .md import + .docx import all verified in production browser session
- [ ] DEPLOY.md updated with any first-deploy learnings
- [ ] RUNBOOK.md complete
- [ ] No TODO comments anywhere in the codebase without an associated stage tag, or all remaining TODOs are explicitly post-MVP and tracked
- [ ] Total Railway monthly cost reviewed and is acceptable
- [ ] Final repo audit: README accurate, CHANGELOG (if present) updated, all `dev-plans/` committed
- [ ] User can hand the repo to a new developer who can: run locally, deploy, and operate without further help

### Key Cross-References to Earlier Stages

- `Settings` class with all env vars: introduced S1 P1.T3.S5; activated in S6 P6.T2.
- `core/storage.py` env-driven addressing style: introduced S1 P1.T3.S8; verified against Railway Buckets in S6 P6.T2.S2.
- Demo users seeded via Alembic data migration: introduced S2 P1.T1.S4; runs in pre-deploy hook in S6 P6.T4.
- `core/sanitize.py`: introduced S3, extended S5; runs in production unchanged.
- `YDocRegistry` + WebSocket endpoint: introduced S4; deployed unchanged in S6.
- Image attachments + import: introduced S5; CORS enabled in production in S6 P6.T3.S5.
- Vitest + pytest test suites: cumulative across stages; smoke tests in S6 P6.T5 are an additional layer specific to deployed verification.

---

*End of Stage 6 development plan*

*End of project planning. The 8-deliverable set is complete: tech-stack-analysis, dependency-map, derived-design-system, and 6 stage-development plans.*
