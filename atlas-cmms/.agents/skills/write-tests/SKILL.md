---
name: write-tests
description: Use when the user asks for tests — "write tests", "add a test", "unit tests",
  "pytest", "vitest", "coverage", "does it work?" — or a test fails and needs fixing.
---

## Files

| | |
|---|---|
| `tests/` | mirrors `src/`; pytest + `TestClient` |
| `tests/fixtures.py` | the app's fixtures — a test database, sample data, a signed-in client. Never `tests/conftest.py`: it is the platform's, replaced on update, and loads this one |

## Choosing

Test what the app promises — not the platform (that `DATABASE_URL` is injected, that `/healthz` answers).

## What to do

1. pytest, with FastAPI's `TestClient` — the conventions already in `tests/`. A feature gets three:
   its `lib/` function, its `/api` endpoint, and its page
2. Test behaviour the app promises, not implementation detail — and each refusal: another person's
   ID (a 404), a value past its limit (a 422), a caller the rule leaves out (a 403 — `ajnkit-core`'s *In a test*)
3. `uv run pytest`, then `canvas validate`
4. Code that uses the database: there is no Postgres on your computer, so override `session`
   (`ajnkit.db`) with SQLite in memory — `create_engine("sqlite://", poolclass=StaticPool,
   connect_args={"check_same_thread": False})`, `Base.metadata.create_all` (in the test only), then
   `app.dependency_overrides[session]`. SQLite has no `jsonb`: test those queries deployed

## What NOT to do

- Do not add a test framework. It is pytest.
