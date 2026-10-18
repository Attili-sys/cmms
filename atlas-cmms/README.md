# ajcmms

Work orders, assets, parts, and requests for this team.

Built on Canvas — **Python, FastAPI, SQLAlchemy**. You edit `score.yaml` and `src/`; the platform
does the rest. The address stays `cmms` (`https://cmms--innovation.canvas.ajnai.net`). Changing
`metadata.name` would create a new app and an empty database.

## Run it

```bash
canvas validate   # score.yaml and the files every app must have — before anything is uploaded
canvas deploy     # validate, then build on the platform and put it online
canvas status     # where it stands; canvas logs for what it printed
```

Needs only `canvas` and your company sign-in (`canvas login`): the platform builds the image.
To try it on your computer first, `PORT=8080 uv run python run.py`, and `uv run pytest` for the tests.

## Where are the Dockerfile and requirements.txt?

**Generated, not written.**

| | |
|---|---|
| dependencies | `pyproject.toml` — FastAPI and SQLAlchemy are pinned; add what else you need |
| the image | buildpacks build it from source — which is what keeps you covered by fleet-wide base-image patching. There is no `Dockerfile`, and the platform would not use one: an app made from an earlier blueprint may still have one, and can delete it |

Editing a generated file does nothing. `score.yaml` is the source.

## Layout

```
run.py            starts the server
src/app.py        builds the app — mounts, routers
src/views.py      HTML pages        src/api.py    JSON, at /api
src/models.py     the schema        src/envs.py   injected variables
packages/         the platform's packages (ajnkit), installed from here — never edited
```

## Where things go

See [AGENTS.md](AGENTS.md) — it is the contract, and your agent reads it on every invocation.

## Building it with an AI assistant

Tested with **Claude Code**, **Cursor** and **Antigravity**. All three use the skills in
`.agents/skills` (Claude Code through `.claude/skills`) — the step-by-step for each kind of change,
starting with `build-feature` — and follow `AGENTS.md`. Other assistants that read `AGENTS.md` —
Copilot, Codex, Gemini CLI — follow the same rules, without the skills.
