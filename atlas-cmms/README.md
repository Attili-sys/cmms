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

To run locally:
```bash
PORT=8080 .venv/bin/python run.py
.venv/bin/pytest -q && .venv/bin/ruff check .
```

## Layout

```
run.py                        starts Uvicorn and runs Alembic migrations when DATABASE_URL is set
score.yaml                    Canvas deployment manifest (name: aj-cafm, Postgres 1Gi, SSO auth)
src/app.py                    builds the FastAPI app, wires ajnkit.web.platform(app), routers, and SPA
src/envs.py                   platform-injected environment variables (the only module reading os.environ)
src/tasks.py                  background maintenance loop (PM generator, PM notifier, downtime notifier, cleanup)
src/spa.py                    serves /runtime-env.js and the compiled React SPA fallback
src/models/                   56 SQLAlchemy 2.0 ORM tables (tables.py) and 38 enums (enums.py)
src/deps/                     database session, Authentik SSO user provisioning, RBAC permission checks
src/routes/                   6 domain routers covering all 241 REST API endpoints
src/services/                 nested camelCase entity serializer, license service, PDF generator
src/static/ & src/static/ui/  compiled React frontend bundle ("Powered by Canvas")
migrations/                   Alembic migration baseline (0001_initial_schema.py)
tests/                        56 unit, schema parity, OpenAPI contract, route, and smoke tests
packages/                     platform wheel (ajnkit_core) — never edited
```

## Where things go

See [AGENTS.md](AGENTS.md) and [MIGRATION_NOTES.md](MIGRATION_NOTES.md).

