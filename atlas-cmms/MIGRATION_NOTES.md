# Migration Notes — Atlas CMMS Java-to-Python Port (`atlas-cmms/`)

## 1. Summary of `.agents/skills/adapt-app/SKILL.md`
- **Canvas Platform Structure:** The application resides in `atlas-cmms/` with `score.yaml` as the single source of deployment truth (`apiVersion: score.dev/v1b1`).
- **Legacy Reference:** Original Java source (`api/`) is copied into `.canvas/legacy/api/` (with `.canvas/ported` recording `api`), excluded from Ruff via `extend-exclude = [".canvas"]`.
- **Single-Process Architecture:** `Procfile` runs `web: python run.py`. There is no separate `worker:` process; background work is executed via `src/tasks.py` started inside `src/app.py`'s lifespan when `envs.DATABASE_URL` is configured.
- **Readiness Probe:** `/healthz` in `src/views.py` must match `resources.www.params.path` in `score.yaml`, verified by `tests/test_health.py`.
- **Database Migrations:** `src/models` defines the SQLAlchemy `DeclarativeBase` (`Base`); Alembic revisions live under `migrations/` and run automatically on startup when `DATABASE_URL` is set.

## 2. Summary of `.agents/skills/ajnkit-core/SKILL.md`
- **Packages & Imports:** `ajnkit-core` is installed from `packages/ajnkit_core-*.whl`. Key modules:
  - `ajnkit.web`: `platform(app)` wires platform static files, security headers, access control, and startup smoke checks; `templates` provides Jinja2 rendering with the platform page shell.
  - `ajnkit.identity`: `caller(request.headers)` returns `Caller(email: str, name: str, groups: list[str])` parsed from Authentik SSO headers (`X-authentik-email`, `X-authentik-name`, `X-authentik-groups`).
  - `ajnkit.db`: `engine`, `SessionLocal`, and `session()` FastAPI dependency (`db: Annotated[Session, Depends(session)]`), configured from `src.envs.DATABASE_URL` (`postgresql+psycopg://...`).
  - `ajnkit.access` / `ajnkit.rbac`: Enforces `score.yaml` route access rules when `PLATFORM_AUTH == "sso"`.
  - `ajnkit.email`: Sends email via `PLATFORM_EMAIL_URL` / `PLATFORM_EMAIL_TOKEN` in cluster, or logs locally when unset.
- **Sync vs Async Rule (`AGENTS.md` §2):** FastAPI endpoints that use synchronous SQLAlchemy `Session` (`db.get`, `db.scalars`, `db.commit`) must be declared with `def` (sync threadpool), never `async def` (which would block the event loop and trigger Ruff `ASYNC`).
- **Environment Rule:** Only `src/envs.py` reads `os.environ`. All other modules import from `src.envs`.
- **Self-Hosted Edition Policy:** `CLOUD_VERSION=false` is set in `score.yaml`. `SubscriptionPlan.features` returns all `PlanFeatures` unconditionally, and `LicenseService.is_unrestricted_self_hosted()` returns `not envs.CLOUD_VERSION`.
