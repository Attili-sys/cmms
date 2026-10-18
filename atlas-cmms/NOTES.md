# Decisions

- **2026-10-18**: The Canvas app name in `score.yaml` is **`aj-cafm`** (`https://aj-cafm--innovation.canvas.ajnai.net`), with title **`AJ CAFM`**.
- **2026-10-18**: All upstream logos and brand references have been removed across the frontend and backend and replaced with **"Powered by Canvas"**.
- **2026-10-18**: Full Java-to-Python migration completed in `atlas-cmms/` (72 SQLAlchemy ORM entity models + 53 association tables, 250+ FastAPI endpoints, background tasks in `src/tasks.py`, bundled React SPA in `src/static/ui/`).
- **2026-10-18**: Company sign-in (`auth: sso`) stays on, with `attiliab@aljazeera.net` configured in `score.yaml` `resources.www.params.access.read`.
- **2026-10-18**: On an empty database, `src/deps/current_user.py` automatically provisions the initial company (`AJ CAFM`), `CompanySettings`, all 24 default `FieldConfiguration` rows, and `ROLE_SUPER_ADMIN` for the first Authentik SSO caller.
- **2026-10-18**: Reviewer Agent audit completed (`@2624f8ef1da1`): added automatic foreign-key mini-DTO hydration in `src/services/serializer.py`, tree-hierarchy pagination (`GET /api/locations/children/{parent_id}/paginated` and `GET /api/assets/children/{parent_id}/paginated`) with Redux `locationsHierarchy`/`assetsHierarchy` synchronization, `PreventiveMaintenance` `Schedule` linking, `Checklist` `TaskBase`/`TaskOption` persistence, `/app/imports` index routing, and `tests/test_crud_contracts.py` (57 pytest tests passing).
- **2026-10-18**: Added dedicated reference documentation in `DATABASE.md` and `API_CONTRACTS.md`.
