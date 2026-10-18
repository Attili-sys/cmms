# Decisions

- 2026-10-14: The product name is **ajcmms**. The Canvas address stays `cmms` so the existing database stays. The portal title is `ajcmms`. The in-app brand comes from `BRAND_CONFIG` in `src/static/ui/runtime-env.js`.
- The code we change is this folder. `api/`, `frontend/`, and `home/` one level up are the original Atlas CMMS, kept as the reference for what the screens expect.
- Company sign-in stays on, and only attiliab@aljazeera.net can open it, until that is changed on purpose.
- A second person at the same email domain cannot sign in until an invite exists. Not built yet.
