---
name: validate
description: Use before every deploy, after editing score.yaml, adding or renaming a top-level file,
  or when a deploy stopped at `validate` or the controller said "run `canvas validate`".
---

## Files

Edits whatever it names — `score.yaml`, the app's dependencies (*a dependency*, AGENTS.md's Stack
table); an adapted app's own `Procfile`. Never the platform's files — `Procfile`, `run.py`,
`project.toml`: read only, and `canvas app update` brings them back. Runs `canvas validate`.

## What it checks

| | Refused when |
|---|---|
| `score.yaml` | not YAML; `metadata.name` still `CHANGEME` or not a valid name; not exactly one container named `app`, or one with a key other than `image`, `variables` and `volumes` (`resources` is the platform's to set); not exactly one `route`; a resource the platform does not provide yet (it provides `route`, `postgres`, `llm`, `email`, `volume`, `secret` and `service`); `access` without `auth: sso` |
| `route` | a key other than `port`, `path`, `auth`, `access`, `docs` and `scope` — `websocket`, `timeoutSeconds` and `allowedTeams` are in the schema but not provisioned yet: remove them; `scope` other than `cluster` or `internal-cluster` (no address of its own — a pair's API; keep it), or `internal-cluster` without `auth: sso`; `access`, or `docs: public`, without `auth: sso`; a `@require("…")` in `src/`, or `permit("…")` in a Next.js app, naming a rule `access.rules` does not declare (`add-auth`); `@require` written above the route decorator (`@router.get`, …) — it protects nothing, so put it below, next to the function |
| `secret` | anything but `keys` and `files`; a name not in upper case, digits and `_`; a key the platform sets, or one also in `variables`; more than 50 (`add-secret`) |
| `metadata.annotations` | a `canvas.dev/category` or tag not in the list, more than three tags, a `visibility` other than `team` or `private`; an icon or cover not a PNG, JPEG or WebP of the right size and shape (`describe-app`) |
| `postgres` | more than one; anything but `size` (the platform sets the version); `size` outside 1Gi–10Gi (more is a team owner's approval on the app's page, not a bigger `size`: `request-database`); `db/migrations/` files not named `NNN_*.sql` or over 1 MiB; migrations with no `postgres` |
| `llm` | more than one; `models` or `rpm` not what the platform takes (`request-llm`) — a person's model (Claude, Qwen, gpt-oss) or a name the gateway does not serve |
| `variables` | a name YAML does not read as text (`ON`, `NO`, `123`) — quote it: `"ON": …` |
| `volume` | more than one; `size` outside 1Gi–100Gi (over 10Gi, a team owner approves it first); not mounted exactly once under `containers.app.volumes`, or at `/`, `/tmp`, `/workspace` or a system path (`request-volume`) |
| The files every app ships | `score.yaml`, `Procfile` (with a `web:` line whose `.py` — or a Node app's `.js` — exists) and `pyproject.toml` or `requirements.txt`, or for a Node app `package.json` with its lockfile and no Python manifest beside it — checked against what would be **uploaded**, so a file `.gitignore` hides counts as missing |
| The platform's checks on every request | *the checks on every request* (AGENTS.md's table) are not installed — gone, commented out, inside an `if`, edited, or not the platform's. Put them back as that row says. Never loosen them: the app's own rules go in `access.rules` (`add-auth`) |
| A credential in a file that ships | a line holding what looks like a key or token — a private key, `sk-…`, `AKIA…`, `ghp_…` — named `file:line`. Move the value to `canvas secret set <KEY>` (`add-secret`) and read it from the environment. Only when it is not a credential — a documented example — add a comment holding `gitleaks:allow` on that line |

**Refused** (exit 20): a Next.js app's type errors, once `node_modules` is installed, when `next build`
would fail on them. An app that sets `typescript.ignoreBuildErrors: true` is not refused — the
platform's build ignores them too. Fix the errors (`npm run typecheck`), then run this again.

**Warned, not refused**: Python's lint — ruff's undefined names and syntax errors, at the version
`.pre-commit-config.yaml` pins. Each would fail when that line runs; fix them before deploying. The
app is still `valid`.

`canvas deploy` runs the same check first, and the controller refuses a source without those files,
so passing here means the platform will accept it.

## What to do

1. `canvas validate`
2. Fix what it names. A `score.yaml` problem stops the check at the first one; the missing files are
   listed all at once. Either way the first is on the `REASON` line
3. Run it again until it prints `valid`

## What NOT to do

- Do not edit the `Procfile`, `run.py` or `project.toml` — they are the platform's (an adapted app's
  own `Procfile` is the exception): without a start command the image builds and runs nothing, and nothing says why.
- Do not add a Dockerfile to get past it. The platform builds with buildpacks.
- Do not deploy to find out whether it is valid — that is what this is, in a second instead of minutes.
