---
name: adapt-app
description: Use in an app's folder (a score.yaml) when an existing app is being ported onto Canvas (the sandbox) — "adapt the old app",
  "migrate", "port my app", "move my app here" — or when .canvas/legacy/ exists. `canvas app adapt
  <old> <new>` copied the old app there, to port from.
---

## Files

| | |
|---|---|
| `.canvas/legacy/` | the old app — **read it, never write it**. Not deployed, not committed |
| `.canvas/legacy/**/.env*.keys` | the names its credentials had; their values were not copied |
| this app | where everything goes, by AGENTS.md §2 |

## Keep the app as it is

**A port moves the app; it does not redesign it.** What the user sees and does stays exactly the
same:

- **its look** — colours, fonts, layout, logos, its own CSS and pages. Not the platform's page
  shell or components, and no restyling, unless the user asks for it
- **its business logic** — every rule, calculation, default and validation, with the same inputs
  giving the same outputs (the tests pin them)
- **its workflows** — the same pages, steps, buttons, wording and order

Only the plumbing changes: the framework, where the code lives, the database, the sign-in, the
settings. **When a platform rule would change what the user sees or does — or you are not sure
whether it would — ask the user, and wait.** Never decide it for them.

## Its static files

Every file in the image is dated 1980, so an ETag of date and size calls a changed file unchanged:
version their URLs (`?v=`), or drop If-None-Match and If-Modified-Since first —
`ajnkit.origin.fresh(request)` in an ASGI middleware.

## Choosing

**First an inventory, shown to the user before any code moves** — what the app does, and where each
part goes:

| In the old app | In the blueprint |
|---|---|
| routes returning HTML | `views.py` + `src/templates/` (Jinja), its own CSS and look kept as they are; a React or other SPA → `choose-frontend` |
| routes returning JSON | `api.py`, Pydantic models in and out |
| the logic inside the routes | `src/lib/` — both the view and the endpoint call it (`build-feature`) |
| a database | `postgres` + `src/models.py`, then `canvas db revision` (`request-database`) |
| files written to disk | a `volume` (`request-volume`); `/tmp` for scratch |
| OpenAI or other model calls, text to speech included (OpenAI TTS, ElevenLabs, Google or Azure speech) | `llm`, an unmodified OpenAI SDK — speech with a `-tts` model (`request-llm`); the outside service's key is dropped, not copied |
| a login of its own | the platform's sign-in, already on (`add-auth`) — keep the old one or drop it: ask |
| environment variables | `containers.app.variables` in `score.yaml`, read in `src/envs.py` |
| credentials, API keys (the `.keys` files) | a `secret` (`add-secret`) — declare the names; the user sets each value. Never copy one |
| a cache, a queue, a worker, cron | not as such — `add-cache`: in the process or a `postgres` table; a worker or cron is `src/tasks.py`; say what changes |
| Dockerfile, compose, Kubernetes files, Makefile | nothing: the platform builds and runs the app |

Say how big it is. The stack is fixed — Python, FastAPI, SQLAlchemy — so a Flask app is a close port
and Django, Node, PHP or anything else is a **rewrite**. **Port only on the user's explicit yes** to
the port and its size — `canvas-adapt` asks it first, when the app came in through it.

## What to do

1. Read the old app — `.canvas/legacy/`, or, ported in place (`.canvas/ported`), this folder
   itself — and show the inventory above, with its size; wait for the yes
2. Port **one feature at a time**: its `lib/` function, its endpoint in `api.py`, its page in
   `views.py`, and tests that pin what the old app did — the same inputs give the same outputs.
   `uv run pytest` passes before the next feature
3. Dependencies: only what the ported code imports, into `pyproject.toml`
4. **Data is not moved.** Say so; bringing existing rows over is a separate step the user agrees to
5. `canvas validate`, then AGENTS.md §1: auto-deploy, or ask
6. Report: what was ported, what was left out and why, what needs the user's decision — and ask
   whether to delete `.canvas/legacy/` now that the port is done

## What NOT to do

- Do not change the folder `canvas app adapt` copied from, or anything under `.canvas/legacy/`.
  Ported in place, an old file goes only once its feature is ported and tested — say which, and
  get a yes.
- Do not copy a credential's value into any file, even from the old app's code.
- Do not keep the old framework beside FastAPI, or bring its Dockerfile, compose or CI.
- Do not port it all in one go: one feature, its tests, then the next.
- Do not change its colours, look, business logic or workflows, or "tidy" them toward the blueprint. Ask.
