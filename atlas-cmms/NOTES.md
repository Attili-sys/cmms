# Decisions

- **2026-10-18**: The Canvas app name in `score.yaml` is **`aj-cafm`** (`https://aj-cafm--innovation.canvas.ajnai.net`), with title **`AJ CAFM`**.
- **2026-10-18**: All upstream logos and brand references have been removed across the frontend and backend and replaced with **"Powered by Canvas"**.
- **2026-10-18**: Full Java-to-Python migration completed in `atlas-cmms/` (56 SQLAlchemy tables, 241 FastAPI endpoints, background tasks in `src/tasks.py`, bundled React SPA in `src/static/ui/`).
- Company sign-in (`auth: sso`) stays on, with `attiliab@aljazeera.net` configured in `score.yaml` `resources.www.params.access.read`.
- On an empty database, `src/deps/current_user.py` automatically provisions the initial company (`AJ CAFM`), `CompanySettings`, all 24 default `FieldConfiguration` rows, and `ROLE_SUPER_ADMIN` for the first Authentik SSO caller.

