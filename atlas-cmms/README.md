# aj-cafm (Powered by Canvas)

Self-hosted maintenance management system (Work Orders, Preventive Maintenance, Assets, Parts, Locations, Meters, Checklists, and Requests) running on Canvas.

Built on Canvas — **Python 3.14, FastAPI, SQLAlchemy 2.0, `ajnkit-core`**, serving the bundled React SPA (`src/static/ui/`).
The Canvas app name is **`aj-cafm`** (`https://aj-cafm--innovation.canvas.ajnai.net`), configured in `score.yaml`.

## Run & Deploy

```bash
canvas validate   # checks score.yaml and required platform files
canvas deploy     # validates, builds on Canvas, runs smoke tests, and deploys aj-cafm
canvas status     # checks deployment health; `canvas logs` for runtime output
```

To run and test locally:
```bash
PORT=8080 .venv/bin/python run.py
.venv/bin/pytest -q && .venv/bin/ruff check .
```

## Layout

```
run.py                        starts the Uvicorn server on $PORT
score.yaml                    Canvas deployment manifest (name: aj-cafm, Postgres 1Gi, SSO auth)
src/app.py                    builds the FastAPI app, wires ajnkit.web.platform(app), routers, and SPA
src/envs.py                   platform-injected environment variables (the only module reading os.environ)
src/tasks.py                  background maintenance loop (PM generator, PM notifier, downtime notifier, cleanup)
src/spa.py                    serves /runtime-env.js and the compiled React SPA fallback
src/models/                   73 SQLAlchemy 2.0 ORM entity models, 54 association tables, and 46 enums
src/deps/                     database session, Authentik SSO user provisioning, RBAC permission checks
src/routes/                   6 domain routers + _crud.py, 324 OpenAPI paths under /api
src/services/                 nested camelCase entity serializer with FK mini-DTO hydration, workflow, notification, license & PDF services
src/utils/                    SearchCriteria specification engine (search.py), pagination, dates, security
src/static/ & src/static/ui/  compiled React frontend bundle ("Powered by Canvas")
db/migrations/                Canvas SQL schema migrations (`001`–`006`) and `db/schema.json`
tests/                        115 unit, schema parity, OpenAPI contract, E2E CRUD, asset/non-asset parity, and smoke tests
packages/                     platform wheel (ajnkit_core) — never edited
```

## Documentation Reference

- **[AGENTS.md](AGENTS.md)** — Canvas platform rules, `ajnkit` SDK conventions, and deployment workflow.
- **[DATABASE.md](DATABASE.md)** — Complete SQLAlchemy 2.0 schema reference (all 73 ORM models, 54 association tables, 46 enums, sequences, and tenant scoping).
- **[API_CONTRACTS.md](API_CONTRACTS.md)** — REST API router catalog, foreign-key mini-DTO hydration (`_hydrate_foreign_key`), hierarchy pagination (`/children/0/paginated`), and `SearchCriteria` specification engine.
- **[MIGRATION_NOTES.md](MIGRATION_NOTES.md)** — Java-to-Python migration architecture and Reviewer Agent verification history.
- **[NOTES.md](NOTES.md)** — Project-specific architectural decisions log.
