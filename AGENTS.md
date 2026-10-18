# AJ CAFM (Powered by Canvas)

Self-hosted maintenance system deployed on Canvas as **`aj-cafm`** (`https://aj-cafm--innovation.canvas.ajnai.net`).

The active production stack is:
- **Canvas Python Backend + Bundled SPA (`atlas-cmms/`)**: FastAPI + SQLAlchemy 2.0 + `ajnkit-core` serving all 250+ REST API endpoints across 6 domain routers (`src/routes/`), 72 ORM entity models + 53 association tables (`src/models/`), background maintenance schedulers (`src/tasks.py`), and the compiled React SPA (`src/static/ui/`).
- **React Web App (`frontend/`)**: TypeScript/React + Redux Toolkit source compiled into `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/`. All external logos and branding have been replaced with **"Powered by Canvas"**.
- **Legacy Reference (`api/`, `mobile/`, `home/`)**: `api/` is the original Java Spring Boot backend (retained for parity reference and archived in `atlas-cmms/.canvas/legacy/api/`), `mobile/` is the Expo mobile app, and `home/` is the marketing site. `cmms/` is a leftover venv — ignore.

`README.MD` is for operators installing or deploying the product. This file is the operating sheet for coding agents.

## Commands

Run these from the directory named in the heading. They are the commands checked into the repo. A green result still has to be the output of a command you just ran.

| App / Directory | Command | Source |
|---|---|---|
| Canvas App (`atlas-cmms/`) — Test & Lint | `.venv/bin/pytest -q && .venv/bin/ruff check .` | `atlas-cmms/pyproject.toml`, `atlas-cmms/AGENTS.md` |
| Canvas App (`atlas-cmms/`) — Run locally | `PORT=8080 .venv/bin/python run.py` | `atlas-cmms/README.md` |
| Canvas App (`atlas-cmms/`) — Validate & Deploy | `canvas validate`, then `canvas deploy` (deploys `aj-cafm`) | `atlas-cmms/score.yaml` |
| Web (`frontend/`) — Lint & Build | `npm run lint`, `npm run build` (then sync `build/*` to `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/`) | `frontend/package.json` |
| Legacy Full Stack (Docker) | `docker-compose up -d`, then http://localhost:3000 | `README.MD`, `docker-compose.yml` |
| Legacy Java API (`api/`) | `mvn test` or `mvn spring-boot:run` (JDK 17) | `api/pom.xml` |
| Mobile (`mobile/`) | `npm install`, then `npm test`, `npm run android`, or `npm run ios` | `mobile/package.json`, `mobile/CONTRIBUTING.md` |

`frontend/package.json` has no `test` script. Do not invent one.

## Where new code goes

| Change | Place |
|---|---|
| Canvas Python API routes | `atlas-cmms/src/routes/` |
| Canvas Python ORM models & enums | `atlas-cmms/src/models/` |
| Canvas Python services & serializers | `atlas-cmms/src/services/` |
| Canvas Python search & specification engine | `atlas-cmms/src/utils/search.py` |
| Canvas Python auth & permission dependencies | `atlas-cmms/src/deps/` |
| Canvas Python Alembic migrations | `atlas-cmms/migrations/versions/` |
| Canvas Python tests | `atlas-cmms/tests/` |
| Web pages & components | `frontend/src/content/own/` and `frontend/src/components/` |
| Web Redux state slices | `frontend/src/slices/` |
| Web strings | `frontend/src/i18n/translations/` |
| Legacy API Java | `api/src/main/java/com/grash/` |
| Legacy API schema | Liquibase changelogs under `api/src/main/resources/` |
| Mobile | `mobile/` |

## Rules that are easy to miss

Canvas Python Backend (`atlas-cmms/AGENTS.md`, `atlas-cmms/DATABASE.md`, `atlas-cmms/API_CONTRACTS.md`):

- **Sync vs Async**: FastAPI endpoints using synchronous SQLAlchemy `Session` (`db.get`, `db.scalars`, `db.commit`) MUST be declared with `def`, never `async def` (enforced by Ruff `ASYNC`).
- **Environment variables**: Only `atlas-cmms/src/envs.py` reads `os.environ`. All other modules import from `src.envs`.
- **Single process**: `Procfile` runs `web: python run.py`. Background jobs (`pm_generator`, `preventive_maintenance_notifier`, `downtime_notifier`, `cleanup`) run inside `src/tasks.py` started by `src/app.py` lifespan.
- **Foreign-key mini-DTO hydration**: Always pass `db=db` to `model_to_dict(obj, db=db)` (`atlas-cmms/src/services/serializer.py`). React components access nested properties on foreign keys (`row.location.name`, `row.asset.name`, `row.primaryUser.firstName`, `row.category.name`, `row.image.url`); bare `{"id": 1}` stubs will break UI rendering.
- **Tenant scoping (`company_id` vs `company_settings_id`)**: Operational tables inherit `CompanyAuditMixin` (`company_id`), whereas catalog/config tables (`Role`, `Checklist`, `*Category`) are scoped by `company_settings_id`.
- **Hierarchy pagination**: Locations (`/app/locations`) and Assets (`/app/assets`) load their root tree tables via `GET /api/locations/children/0/paginated` and `GET /api/assets/children/0/paginated`, and their Redux slices (`frontend/src/slices/location.ts`, `frontend/src/slices/asset.ts`) must keep `locationsHierarchy` and `assetsHierarchy` synchronized on create/edit/delete.
- **Frontend static sync**: After running `npm run build` in `frontend/`, copy the build output into both `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/` while preserving `atlas-cmms/src/static/ui/runtime-env.js`.

Branding (`frontend/` & `atlas-cmms/`):

- All product logos and upstream brand marks have been removed and replaced with **"Powered by Canvas"**. Do not re-introduce external logos or upstream brand links.

Translations (`frontend/src/i18n/translations/AGENTS.md`):

- Translate values only. Leave keys unchanged.

Legacy Java Schema & Tests (`api/src/main/resources/db/Agents.md`, `api/src/test/java/com/grash/agents.md`):

- Every foreign key sets `onDelete=Cascade`, or `onDelete=Set null` when the column is nullable.
- Unit tests use `MockitoExtension`, `@Mock`, and `@InjectMocks`. Controller tests use `@WebMvcTest` and `MockMvc`.

Secrets stay in `.env` and the environment. Never commit them.

## Read when

| File | Read when |
|---|---|
| `atlas-cmms/AGENTS.md` | Modifying the Canvas Python app (`atlas-cmms/`), `score.yaml`, or `ajnkit` integration |
| `atlas-cmms/DATABASE.md` | Inspecting or modifying SQLAlchemy 2.0 ORM models, association tables, enums, sequences, or tenant scoping |
| `atlas-cmms/API_CONTRACTS.md` | Modifying API routes, serializers (`model_to_dict`), foreign-key mini-DTO hydration, search criteria, or Redux slice contracts |
| `atlas-cmms/MIGRATION_NOTES.md` | Reviewing the Java-to-Python architecture, route parity, or Reviewer Agent sign-off history |
| `frontend/README.md` | Building, linting, or modifying the React web application (`frontend/`) |
| `frontend/src/i18n/translations/AGENTS.md` | Editing translation JSON |
| `dev-docs/` | Super-admin, LDAP, TLS, backup, upgrades |
| `ATLAS_CAFM_DECISION_REPORT.md` | Choosing what to build next. It is an audit, not a description of code you have changed |
| `UNRESTRICTED_SELFHOSTED.md` | Understanding which restrictions were removed on this branch and which controls are retained |
| `api/src/test/java/com/grash/agents.md` | Writing or changing legacy Java API tests |
| `api/src/main/resources/db/Agents.md` | Touching legacy Liquibase changelogs |

## Self-hosted edition (this branch)

This branch (`migrate-python` / `unrestricted-selfhosted`) removes all commercial restrictions. The capability policy is:

> When `CLOUD_VERSION=false`, every implemented feature is available without a subscription, activation key, license file, numerical quota, trial period, or connection to a licensing service.

Rules for agents working on this branch:

- **Do not re-add** Keygen validation, Paddle billing checks, license-file reads, trial-expiry scheduling, or feature-count quotas in any self-hosted code path.
- In `atlas-cmms/`, `LicenseService.is_unrestricted_self_hosted()` (and `LicenseService.isUnrestrictedSelfHosted()` in legacy Java) is the single gating method.
- `SubscriptionPlan.features` / `getFeatures()` always returns every `PlanFeatures` member. Do not use stored plan features as a gate.
- Authentication (Authentik SSO on Canvas), role/entity permissions, company isolation, approval rules, rate limits, and audit logging are **not** commercial restrictions and must remain unchanged.

## Done

A Canvas backend change (`atlas-cmms/`) is done when `.venv/bin/pytest` (57 tests including `tests/test_crud_contracts.py`) and `.venv/bin/ruff check .` pass in `atlas-cmms/`. A web change (`frontend/`) is done when `npm run lint` and `npm run build` succeed in `frontend/` and the built assets are synced to `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/`. A mobile change is done when `npm test` has been run in `mobile/`. A UI change is done when the affected screen has been verified in a browser or E2E test.
