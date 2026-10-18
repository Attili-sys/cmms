---
name: ajnkit-core
description: >-
  Reference for the platform's core package — ajnkit-core (Python, `from ajnkit import …`) or
  @ajnkit/core (Next.js, `import … from "@ajnkit/core"`). Use when writing code that reads who is calling,
  checks a rule, talks to the database, calls something outside, logs, or draws a page in the
  platform's shell — and to find a function's exact name and what it raises. Deciding what to build
  is the task skills' (add-auth, add-page, build-feature); this is how the code is written.
---

The platform's code, installed in the app (`packages/`, pinned in the lock) and never edited.
Read it, when the answer is not here: Python `uv run python -c "import ajnkit; print(*ajnkit.__path__)"`,
Next.js `node_modules/@ajnkit/core/dist/`. Each module's docstring is its rule.

## Who is calling, and what they may do

| | Python | Next.js |
|---|---|---|
| who | `caller(request.headers)` → `Caller(email, name, groups)` (`ajnkit.identity`) | `await currentCaller()` (`@ajnkit/core`) |
| a rule on a page or route | `@require("dashboard")` on the view; `dependencies=[Depends(require("dashboard"))]` on a router (`ajnkit.rbac`) | `await permit("dashboard")`, first in the page, action or route |
| may they, without ending the request | `allowed(who, "dashboard")` | `permitted(who, "dashboard")` |
| a POST that only asks (readers may send it) | `@access.asks` on the route — the only route on its path, or it is closed to readers (logged once) | its path in `src/asks.ts` — a route handler's, never a page's: a server action (`Next-Action`, a multipart form) is never an ask |

The people are in `score.yaml` (`access.rules.<name>`), never in the code; `canvas validate` refuses a
rule the code names and score.yaml does not declare. Under `auth: none` identity headers are absent
and forgeable: a rule raises `AuthNotEnabled` (Python) rather than trust them.

## Data, outside calls, logs

| | Python | Next.js |
|---|---|---|
| the database | `db: Annotated[Session, Depends(session)]` (`ajnkit.db`) | `db()` (`@/canvas/db`, the app's adapter over its schema) |
| a call outside | `with http.client() as c:` — 10 s, 5 s to connect (`ajnkit.http`) | `await call(url, init)` — 10 s |
| a log line | `log.info("…", extra={…})` (`ajnkit.logger`) — JSON the platform collects | `log.info(…)` |
| a setting | `envs.NAME` (the app's `src/envs.py`; its own added there) | the platform's `env.NAME`; the app's own `setting("NAME")` (`@ajnkit/core`) |
| a secret | `envs.secret("KEY")`, `envs.secret_file("KEY")` — where used | `secret("KEY")`, `secretFile("KEY")` — where used |
| an error, with where it was raised | `log.exception("…")` inside the `except` | `log.error("…", { error: e })` |

Never a request without a timeout, never `os.environ` / `process.env` outside the settings file, never
a secret, token or password in a log.

The database: a query ends after 15 s, and the app has 10 connections — the use-database skill.

## What fails, and when

- A rule score.yaml does not declare: Python stops at start, Next's `permit` throws.
- Under `auth: none` (your computer too) every rule lets nobody in.
- After each deploy the platform opens every page as a signed-in test person; a 500 fails the deploy
  (Python).

## In a test

```python
monkeypatch.setattr(envs, "PLATFORM_AUTH", "sso")
monkeypatch.setattr(envs, "PLATFORM_ACCESS", {"rules": {"dashboard": ["Finance"]}})
client.get("/dashboard", headers={"X-authentik-email": "ann@x.net", "X-authentik-groups": "Finance|Other"})
```
```ts
vi.stubEnv("PLATFORM_AUTH", "sso");
vi.stubEnv("PLATFORM_ACCESS", JSON.stringify({ rules: { dashboard: ["Finance"] } }));
expect(permitted({ email: "ann@x.net", name: null, groups: ["Finance"] }, "dashboard")).toBe(true);
```

One test for who gets in, one for who does not; a call outside, call-api; the database, write-tests.

## Pages

Python: `templates.TemplateResponse(request, "page.html", {...})` (`ajnkit.web`); pages extend
`base.html`; components from `{% from "platform/ui.html" import … %}`. Next.js: server components
from `@/canvas/ui`. Both: the reference is the app's `COMPONENTS.md`; never draw a header or footer.

## What the platform adds on every request

Python's `run.py` serves through `web.platform(app)`, Next's `src/proxy.ts` through
`@ajnkit/core/proxy`: score.yaml's access, a cross-site write refused (403), a body over 10 MB refused
(413), the security headers (only the app's own script runs — no inline `<script>`, no `onclick=`).
Never loosen them; never install a second copy. A file is a parameter, never read by hand: Python's
256 MB form cap is for a route that takes `photo: UploadFile` (or `Form`); one that reads
`await request.form()` itself has the 10 MB of any body. Next takes files at `PUT /media`, and refuses
a body sent with no length (411). No WebSocket: the platform provisions none, and refuses them.
Python's 422 says where and what (`loc`, `msg`, `type`, the first 10), never the input it refused —
unless the app registers its own `RequestValidationError` handler.
