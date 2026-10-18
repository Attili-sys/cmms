# Migration Notes — AJ CAFM Java-to-Python Port (`atlas-cmms/`)

## 1. Canvas Platform Structure (`aj-cafm`)
- **Canvas App Identity:** Configured in `score.yaml` (`apiVersion: score.dev/v1b1`) with `metadata.name: aj-cafm` (`https://aj-cafm--innovation.canvas.ajnai.net`) and `canvas.dev/title: AJ CAFM`.
- **Legacy Reference:** Original Java source (`api/`) is archived in `.canvas/legacy/api/` (with `.canvas/ported` recording `api`), excluded from Ruff via `extend-exclude = [".canvas"]`.
- **Single-Process Architecture:** `Procfile` runs `web: python run.py`. Background maintenance jobs (`pm_generator`, `preventive_maintenance_notifier`, `downtime_notifier`, `cleanup`) run via `src/tasks.py` inside `src/app.py`'s lifespan when `envs.DATABASE_URL` is set.
- **Readiness Probe:** `/healthz` in `src/views.py` matches `resources.www.params.path` in `score.yaml`, verified by `tests/test_health.py`.
- **Database Migrations:** `src/models` defines the SQLAlchemy 2.0 `DeclarativeBase` (`Base`) with 56 tables and 38 enums; Alembic revisions live under `migrations/` (`0001_initial_schema.py`) and run automatically on startup when `DATABASE_URL` is set.

## 2. `ajnkit-core` Integration
- **Packages & Imports:** `ajnkit-core` is installed from `packages/ajnkit_core-*.whl`:
  - `ajnkit.web`: `platform(app)` wires platform static files, security headers, access control, and startup smoke checks.
  - `ajnkit.identity`: `caller(request.headers)` returns `Caller(email: str, name: str, groups: list[str])` parsed from Authentik SSO headers (`X-authentik-email`, `X-authentik-name`, `X-authentik-groups`).
  - `ajnkit.db`: `engine`, `SessionLocal`, and `session()` FastAPI dependency (`db: Annotated[Session, Depends(session)]`), configured from `src.envs.DATABASE_URL` (`postgresql+psycopg://...`).
  - `ajnkit.email`: Sends email via `PLATFORM_EMAIL_URL` / `PLATFORM_EMAIL_TOKEN` in cluster, or logs locally when unset.
- **Sync vs Async Rule (`AGENTS.md` §2):** FastAPI endpoints that use synchronous SQLAlchemy `Session` (`db.get`, `db.scalars`, `db.commit`) are declared with `def` (sync threadpool), never `async def` (enforced by Ruff `ASYNC`).
- **Environment Rule:** Only `src/envs.py` reads `os.environ`. All other modules import from `src.envs`.
- **Self-Hosted Edition Policy:** `CLOUD_VERSION=false` is set in `score.yaml`. `SubscriptionPlan.features` returns all 20 `PlanFeatures` unconditionally, and `LicenseService.is_unrestricted_self_hosted()` returns `not envs.CLOUD_VERSION`.

## 3. Completed Port Architecture & Verification
- **6 Modular API Routers (`src/routes/`):**
  1. `auth_users.py` — `/auth/*`, `/users/*`, `/roles/*`, `/teams/*`, `/company-settings/*`, `/companies/*`, `/currencies/*`, `/notifications/*`, `/subscription/*`, `/subscription-plans/*`, `/license/*`, `/switch-account/*`
  2. `assets_locations.py` — `/assets/*`, `/asset-downtimes/*`, `/asset-category/*`, `/locations/*`, `/floor-plans/*`, `/customers/*`, `/vendors/*`, `/custom-fields/*`
  3. `parts_po_tasks.py` — `/parts/*`, `/multi-parts/*`, `/part-quantities/*`, `/part-category/*`, `/purchase-orders/*`, `/purchase-order-category/*`, `/additional-cost/*`, `/labor/*`, `/tasks/*`, `/task-bases/*`, `/checklists/*`
  4. `work_orders_pm.py` — `/work-orders/*`, `/work-order-histories/*`, `/work-order-category/*`, `/work-order-configuration/*`, `/preventive-maintenances/*`, `/schedules/*`, `/relation/*`
  5. `meters_requests_workflows_misc.py` — `/meters/*`, `/readings/*`, `/meter-category/*`, `/requests/*`, `/work-order-request-configuration/*`, `/workflows/*`, `/files/*`, `/import/*`, `/export/*`, `/webhooks/*`, `/audit/*`
  6. `analytics.py` — `/analytics/work-orders/*`, `/analytics/assets/*`, `/analytics/parts/*`, `/analytics/requests/*`, `/analytics/users/*`
- **Nested Serializer (`src/services/serializer.py`):** Converts SQLAlchemy models into camelCase DTOs with nested `role` (including permission arrays and `ViewOther` mappings), `companySettings` (including `generalPreferences`, `workOrderConfiguration.workOrderFieldConfigurations`, `workOrderRequestConfiguration.fieldConfigurations`), `subscription` (with all 20 `PlanFeatures`), and `location` / `asset` / `category` / `createdBy` / `assignedTo` objects expected by the React Redux slices.
- **Branding:** All external logos removed; UI displays **"Powered by Canvas"**.
- **Automated Verification:** 56 pytest tests (`tests/test_schema_matches_dump.py`, `tests/contract/test_openapi_covers_catalog.py`, `tests/routes/test_all_routes_and_jobs.py`, `tests/test_smoke.py`) and `ruff check .` pass with 0 errors.

