---
name: local-run
description: Use when the user wants to run the app locally, asks "does it start", "run it", or is
  about to test a change before deploying.
---

## Files

Edits nothing. Runs the app with `uv` (installed with canvas), from the app's folder:

| | |
|---|---|
| macOS, Linux | `PORT=8080 uv run python run.py` |
| Windows (PowerShell) | `$env:PORT=8080; uv run python run.py` |

Then it is at `http://localhost:8080`. `uv run` installs what `pyproject.toml` lists the first time.

If a route is missing, it is in `views.py` (pages) or `api.py` (JSON). `run.py` only starts the
server and `src/app.py` only builds the app — neither handles a request. AGENTS.md §2 has the map.

## Choosing

Locally there is no platform around the app, so what score.yaml declares is not there:

| Declared | Locally |
|---|---|
| `postgres` | no database — `DATABASE_URL` is unset. Test the pages that do not need it; deploy for the rest |
| `llm` | the user's own key: `canvas llm init` once, then `eval "$(canvas llm env)"` in zsh or bash (`request-llm`) |
| `volume` | a `data/` folder next to the code, if `src/envs.py` defaults `DATA_DIR` to it (`request-volume`) |
| `email` | nothing is sent: `send()` writes the message to the log — show the user that line (`request-email`) |
| `auth: sso` | no sign-in, so `ajnkit.identity` sees an anonymous caller |

## What to do

1. Start it (above) and open `/healthz` — it must answer `{"ok": true}`, the same path score.yaml's
   route probes
2. `uv run pytest` for the tests, `canvas validate` before deploying
3. Stop it with Ctrl+C

## What NOT to do

- Do not start containers by hand or write a compose file, a Dockerfile or a `run.sh`.
- Do not run `canvas down` to stop it: `canvas down` **deletes the deployed app**, not the local one.
