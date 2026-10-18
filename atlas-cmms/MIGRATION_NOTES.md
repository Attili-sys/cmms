# Migration Notes — AJ CAFM Java-to-Python Port (`atlas-cmms/`)

## 1. Canvas Platform Structure (`aj-cafm`)
- **Canvas App Identity:** Configured in [`score.yaml`](score.yaml) (`apiVersion: score.dev/v1b1`) with `metadata.name: aj-cafm` (`https://aj-cafm--innovation.canvas.ajnai.net`) and `canvas.dev/title: AJ CAFM`.
- **Legacy Reference:** Original Java source (`api/`) is archived in `.canvas/legacy/api/` (with `.canvas/ported` recording `api`), excluded from Ruff via `extend-exclude = [".canvas"]`.
- **Single-Process Architecture:** `Procfile` runs `web: python run.py`. Background maintenance jobs (`pm_generator`, `preventive_maintenance_notifier`, `downtime_notifier`, `cleanup`) run via [`src/tasks.py`](src/tasks.py) inside [`src/app.py`](src/app.py)'s lifespan when `envs.DATABASE_URL` is set.
- **Readiness Probe:** `/healthz` in [`src/views.py`](src/views.py) matches `resources.www.params.path` in `score.yaml`, verified by `tests/test_health.py`.
- **Database Migrations:** [`src/models/`](src/models/__init__.py) defines the SQLAlchemy 2.0 `DeclarativeBase` (`Base`) with 72 ORM entity classes, 53 association tables, and 44 enums (documented in **[DATABASE.md](DATABASE.md)**); Alembic revisions live under `migrations/` (`0001_initial_schema.py`) and run automatically on startup when `DATABASE_URL` is set.

## 2. `ajnkit-core` Integration
- **Packages & Imports:** `ajnkit-core` is installed from `packages/ajnkit_core-*.whl`:
  - `ajnkit.web`: `platform(app)` wires platform static files, security headers, access control, and startup smoke checks.
  - `ajnkit.identity`: `caller(request.headers)` returns `Caller(email: str, name: str, groups: list[str])` parsed from Authentik SSO headers (`X-authentik-email`, `X-authentik-name`, `X-authentik-groups`).
  - `ajnkit.db`: `engine`, `SessionLocal`, and `session()` FastAPI dependency (`db: Annotated[Session, Depends(session)]`), configured from `src.envs.DATABASE_URL` (`postgresql+psycopg://...`).
  - `ajnkit.email`: Sends email via `PLATFORM_EMAIL_URL` / `PLATFORM_EMAIL_TOKEN` in cluster, or logs locally when unset.
- **Sync vs Async Rule (`AGENTS.md` §2):** FastAPI endpoints that use synchronous SQLAlchemy `Session` (`db.get`, `db.scalars`, `db.commit`) are declared with `def` (sync threadpool), never `async def` (enforced by Ruff `ASYNC`).
- **Environment Rule:** Only [`src/envs.py`](src/envs.py) reads `os.environ`. All other modules import from `src.envs`.
- **Self-Hosted Edition Policy:** `CLOUD_VERSION=false` is set in `score.yaml`. `SubscriptionPlan.features` returns all `PlanFeatures` unconditionally, and `LicenseService.is_unrestricted_self_hosted()` returns `not envs.CLOUD_VERSION`.

## 3. Completed Port Architecture & Reviewer Agent Sign-Off
- **6 Modular API Routers (`src/routes/`, documented in [API_CONTRACTS.md](API_CONTRACTS.md)):**
  1. [`auth_users.py`](src/routes/auth_users.py) — `/auth/*`, `/users/*`, `/roles/*`, `/teams/*`, `/company-settings/*`, `/companies/*`, `/general-preferences/*`, `/currencies/*`, `/notifications/*`, `/subscription/*`, `/subscription-plans/*`, `/license/*`, `/switch-account/*`
  2. [`assets_locations.py`](src/routes/assets_locations.py) — `/assets/*`, `/asset-downtimes/*`, `/deprecations/*`, `/locations/*`, `/floor-plans/*`, `/customers/*`, `/vendors/*`, `/custom-fields/*`, `/custom-field-values/*`, and all 7 `/*-category` routers
  3. [`parts_po_tasks.py`](src/routes/parts_po_tasks.py) — `/parts/*`, `/multi-parts/*`, `/part-quantities/*`, `/purchase-orders/*`, `/additional-costs/*`, `/tasks/*`, `/checklists/*`
  4. [`work_orders_pm.py`](src/routes/work_orders_pm.py) — `/work-orders/*`, `/work-order-histories/*`, `/labors/*`, `/relations/*`, `/comments/*`, `/work-order-meter-triggers/*`, `/preventive-maintenances/*`, `/schedules/*`, `/workload/*`
  5. [`meters_requests_workflows_misc.py`](src/routes/meters_requests_workflows_misc.py) — `/meters/*`, `/readings/*`, `/requests/*`, `/workflows/*`, `/files/*`, `/import/*`, `/export/*`, `/webhooks/*`, `/work-order-configuration/*`, `/work-order-request-configuration/*`, `/ui-configuration/*`
  6. [`analytics.py`](src/routes/analytics.py) — `/analytics/work-orders/*`, `/analytics/assets/*`, `/analytics/parts/*`, `/analytics/requests/*`, `/analytics/users/*`
- **Foreign-Key Mini-DTO Hydration & Serializer ([`src/services/serializer.py`](src/services/serializer.py)):**
  - `model_to_dict(obj, db=db)` automatically hydrates all 19 foreign-key target tables (`location`, `asset`, `own_user`, `team`, `vendor`, `customer`, `file`, `part`, `meter`, `role`, `currency`, `work_order`, and `*_category`) into nested mini-DTO objects so React table columns and detail views (`row.location.name`, `row.asset.name`, `row.primaryUser.firstName`, `row.image.url`) render cleanly.
  - `_MODEL_DEFAULT_LISTS` ensures every collection property (`workers`, `teams`, `vendors`, `customers`, `files`, `assignedTo`, `taskBases`, `options`, `daysOfWeek`, `customFieldValues`, etc.) defaults to `[]` instead of `undefined`.
- **Hierarchy & Route Fixes Verified in E2E Smoke Testing:**
  - Added `GET /api/locations/children/{parent_id}/paginated` and `GET /api/assets/children/{parent_id}/paginated` (`parent_id=0` for roots) and updated `frontend/src/slices/location.ts` and `frontend/src/slices/asset.ts` so creating/editing/deleting locations and assets immediately updates `locationsHierarchy` and `assetsHierarchy`.
  - Fixed `GET /api/assets/mini?locationId=` to accept empty string `""` cleanly.
  - Fixed `PreventiveMaintenance` creation/update to create and link its `Schedule` (`pm.schedule_id = sched.id`) with string enum values (`"DAILY"`, `"SCHEDULED_DATE"`).
  - Fixed `Checklist` creation/update to persist `TaskBase` and `TaskOption` (`[{"id": o.id, "label": o.label}]`).
  - Added index redirect on `/app/imports` → `/app/imports/work-orders` in `frontend/src/router/app.tsx`.
- **Branding:** All external logos removed; UI displays **"Powered by Canvas"**.
- **Automated Verification:** 57 pytest tests (`tests/test_crud_contracts.py`, `tests/test_schema_matches_dump.py`, `tests/contract/test_openapi_covers_catalog.py`, `tests/routes/test_all_routes_and_jobs.py`, `tests/test_smoke.py`) and `ruff check .` pass with 0 errors.
