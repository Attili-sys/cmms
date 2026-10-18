---
name: review-security
description: >-
  Use before deploying a change that takes input from people or another system, keeps or
  serves files, calls out, uses an LLM's answer, or changes who may do what — `build-feature` sends
  it here — and when the user asks "is it secure", "security review", "check for vulnerabilities",
  "harden it", or is about to open the app wider (`canvas share`, `auth: none`).
---

> **An adapted app** (`.canvas/adapted`) keeps its own layout: the files below are the blueprint's —
> review the same risks in the app's own (AGENTS.md §1).

## Files

Reads the change — the diff, or the files the user names. Fixes go in the app's own code:
`src/lib/`, `src/api.py`, `src/views.py`, `src/templates/`, `score.yaml`. Never the platform's
`packages/` (ajnkit): those are the guards.

## Choosing

The platform already stops most of this — **only when the app goes through it**. Each risk, what
guards it, and what the change must do so the guard holds:

| Risk | Guarded by | The change must |
|---|---|---|
| Someone who should not reach the app | `auth: sso`, `access` in `score.yaml` (`ajnkit.access`) | keep `auth: sso`; narrow who in `access`, not in code (`add-auth`) |
| An action only some may take | `@require("<rule>")` (`ajnkit.rbac`), its people in `access.rules` | name the rule on the endpoint **and** the view (or once, on their router); never compare an email or a group in code |
| Believing who the caller says they are | `caller()` (`ajnkit.identity`) | read who it is only from `caller()`; under `auth: none` it is forgeable — never authorise on it |
| Reading someone else's record by its ID | — | fetch by ID **and** owner, or check the caller may see it; a 404 for one they may not |
| A form another site makes the browser post | `ajnkit.origin`, on every request | change data only on POST, PUT, PATCH or DELETE — never on a GET, which nothing refuses |
| An uploaded file that runs in the browser | `media.save` / `media.serve` (`ajnkit.media`) | keep and serve uploads only through them; never under `src/static/`, never under the uploader's file name |
| SQL injection | SQLAlchemy | the ORM, or `text()` with bound parameters; never an f-string, `%` or `+` into SQL |
| A script injected into a page (XSS) | Jinja's autoescaping, then the script policy (`ajnkit.origin`) | no `\|safe` or `Markup()` on anything a person, another system or a model wrote |
| Script the policy refuses | `ajnkit.origin`: only the app's own script files run | no inline `<script>`, no `onclick=` or other `on…=`, no script from another site — a file under `src/static/`; `canvas validate` names each line |
| A cookie of the app's own | — | name it `__Host-…`, `Secure`, `HttpOnly`, `SameSite=Lax`, never `Domain=`: every app shares the base domain, and a cookie set for it reaches them all |
| A file path or a command built from input | — | look a file up by an ID the app made; no `shell=True`, no `os.system` — a list of arguments, and a library before a command |
| Fetching an address someone typed (SSRF) | — (`ajnkit.http` only adds timeouts) | call only hosts the app chose; a URL from input is checked against that list first |
| Secrets | `type: secret`, `canvas secret set` (`add-secret`) | read them from `envs`; never in code, templates, logs, errors, test fixtures or the chat |
| Saying too much | Pydantic response models | every endpoint returns a model that lists its fields; no internal columns, no stack traces |
| An LLM's answer (prompt injection) | — | treat it as untrusted text: escape it, never run it, never let it choose a URL, a query or who may do what |
| Code from outside | `pyproject.toml`, `uv.lock` | add a dependency only when needed, and a maintained one; no `eval`, `exec`, `pickle` or `yaml.load` on input |
| Logs | `ajnkit.logger` | no secrets, tokens or passwords, and no personal data beyond the caller's email |

**Validate at the boundary**: a Pydantic model on every endpoint's input — types, lengths, ranges,
allowed values — and the view's form through the same `lib/` function, so the two cannot differ.

## What to do

1. List what the change takes in — form fields, JSON, query strings, headers, uploads, webhooks,
   an LLM's answer — and where each one goes
2. Walk the table for each, reading the lines themselves. Each finding: one sentence and `file:line`
3. Fix it in the app's code, with a test of the refused case, not only the happy one
   (`write-tests`): another person's ID gets a 404, `<script>` comes back escaped, an over-long
   value gets a 422, a page behind a rule refuses someone not in it
4. `uv run pytest`, then `canvas validate`
5. Tell the user in plain words what was checked and what changed. Anything only the platform can
   fix — a resource Canvas lacks — is `report-issue`, not a workaround

## What NOT to do

- **Never switch a guard off to make something work** — not `auth: none` for a script (a service
  account, `add-auth`), not an
  `access` entry for everyone, not an edit to the platform's code (`ajnkit-core`), not `|safe` to keep some formatting.
- Do not check a permission in the page alone: the endpoint is reachable without it.
- Do not hide a record by leaving it out of a list — fetched by its ID, it must still be refused.
- Do not print or log a secret to debug it, and do not paste one into the chat.
- Do not say "it is secure". Say what was checked: a review finds what it looks for.
- Do not add a security library, a firewall or a login of your own — the platform's guards are the
  design, and a second one drifts from them (AGENTS.md §5).
