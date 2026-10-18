# ajnkit — what changed

The platform's code, one version for both stacks. `canvas update` (or `canvas app update`) puts a new
one in the app's `packages/` and its lock; this file comes with it. The `apply-update` skill reads it:
a line under **Your app** is something to do in the app's own code — anything else needs nothing.

## 0.5.21 — 2026-10-13

Dependencies only: `ajnkit-core` requires `psycopg[binary]>=3.3.6`, and the Python packages are built
with hatchling 1.32.4. Nothing in an app changes.

## 0.5.20 — 2026-10-12

The page check judges pages as the app's own people would; the chat's memory example compiles.

- **`ajnkit.smoke`** (`ajnkit-core`): a page behind a rule is opened as someone who passes
  `access.read` and the rule (before: the rule alone, so the app answered 403, which counted as open and hid a
  500 behind it); an app whose `access` has only `rules` is still opened as someone signed in; a 401/403
  is listed under `refused` in the summary, never counted in `ok`; a page is judged on its status when the
  headers arrive, so a stream (SSE, a long poll) no longer hangs the check or the app's shutdown, and the
  summary is always logged (120 s in all); `src/nav.py`'s pages are opened first, and what the 40-page cap
  or the 120 s left out is `unchecked` in the summary. Nothing in an app changes.
- **`ajnkit-chat`'s *Remembering the person*** (both stacks): the example guards `who.email` (`string | null`)
  and says it needs `auth: sso`. **Your app:** if you copied the old example, add the guard — it does not
  compile on Next, and on Python it queries on a null.

## 0.5.19 — 2026-10-11

The chat can remember the person it talks to, across conversations.

- **`memory_tools(keep, drop)` and `remembered(messages, facts)`** (`ajnkit-chat`; Next `memoryTools`,
  `remembered` in `@ajnkit/chat`): the model keeps what the person says about themselves — their
  language, what they follow — with `remember`, drops it with `forget`, and every conversation starts
  with the facts. The app stores them in its own table, per person; ajnkit keeps nothing, and the
  gateway's memory stays closed (every key of a team read it). `ajnkit-chat`'s *Remembering the person*.

## 0.5.18 — 2026-10-11

What the assistant is told about ajnkit, made right and complete; a Next app reads its own settings.

- **`setting(name, fallback?)`** (`@ajnkit/core`): a Next app's own variable — score.yaml's
  `containers.app.variables`, as `SCORES_URL` — read at call time, with an error that says where to
  declare it. `env` holds only what the platform sets; the skills' `env.ORDERS_URL` and `scoresUrl`
  compiled nowhere (add-auth, call-api).
- **What goes around ajnkit, on both stacks.** `packages.json` gains `replaces_npm` (openai,
  @google/genai, @anthropic-ai/sdk, @ai-sdk/*, nodemailer, @aws-sdk/client-s3 and -ses, axios,
  next-auth, jose…), which `canvas validate` and Studio now check in a Next app's `src/`, and
  `replaces` more Python (requests, aiohttp, psycopg, `create_engine`, dotenv, loguru, langchain_*,
  tavily, resend…). An adapted app may see new notes; each names the call to use.
- **The reference skills say what fails, and how to test.** ajnkit-email: an ambiguous failure (502,
  504, a timeout) is never sent again. ajnkit-llm: a model call's errors by status, the sync Python
  client, which models the key has, a typed answer in Next. ajnkit-core: the database's limits, what
  stops the app at start, identity in a test. ajnkit-chat and ajnkit-media: their limits, and
  one replica.
- **Shorter guidance.** AGENTS.md a quarter shorter (it is read on every request); each rule kept in one
  place — how the code is written in the reference skill, when and the steps in the task skill.

### Your app

- A Next app that reads its own variable through `process.env` — move it to `setting("NAME")` from
  `@ajnkit/core`.

## 0.5.17 — 2026-10-10

Apps import the platform's code from ajnkit itself; the chat's last word, static files and the app's
title, fixed.

- **No re-export files.** The Python blueprint's `src/utils/` (each file `ajnkit.<x>` under an older
  name) and the Next blueprint's `src/canvas/` files that only re-exported `@ajnkit/…` — with the
  `@/canvas/auth`, `/config` and `/services` barrels — are gone (canvas#211). Python imports
  `from ajnkit import <x>`; Next imports `@ajnkit/core` (who is calling, `permit`, `env`, `call`,
  `log`), `@ajnkit/llm`, `@ajnkit/chat`, `@ajnkit/media`, `@ajnkit/email`, or a module of one
  (`@ajnkit/core/auth/origin`). `@/canvas/ui` (the shell, given the app's pages) and `@/canvas/db`
  (the app's schema) stay. A feature's module imported without its package says what to run —
  `ajnkit-chat is not installed — canvas app add chat` — from `ajnkit.web.missing`, which `run.py`
  and `tests/conftest.py` call.
- **The chat's last word shows at once** (canvas#207): both stacks send `{"answered": true}` once the
  answer's text and sources are out, before the follow-ups' model call, and the window shows the
  whole answer then; it stays busy until the follow-ups come. An older window ignores the event.
- **A changed static file reaches every browser** (canvas#208): an unversioned file is always sent
  whole — Python's `/static/` (`ajnkit.origin.fresh`), and a Next app's `public/` (the proxy, with
  `fresh` from `@ajnkit/core/auth/origin`; Next's own `/_next/` files keep theirs) — a browser that
  kept an old ETag, made from the 1980 date buildpacks give every file, was told 304 for a changed
  file of the same size.
- **score.yaml read as YAML** (blueprints#45): the app's title and description (`about()`) come from
  `metadata.annotations` by a YAML parser — PyYAML (`pyyaml>=6.0.3`) in ajnkit-core, `yaml` (^2.9.1,
  as YAML 1.1) in @ajnkit/core — so `"Q&A #1"`, `C# tools`, `'It''s here'`, `"Say \"hi\""` and flow
  style are what they say; an unreadable score.yaml gives no title, never an error.
- **Your app**: `canvas app update` writes the app's imports of `src.utils.<x>` and of the removed
  `@/canvas/…` files to ajnkit and removes those files; one it left (`No module named 'src.utils'`,
  or a `@/canvas/…` import `npm run typecheck` says is gone) is written the same way by hand. Nothing
  else to change.

## 0.5.16 — 2026-10-10

The page check opens the app's pages, not only the menu's.

- `ajnkit.smoke` finds the app's GET pages inside its included routers: FastAPI keeps an included
  router whole, so 0.5.15 saw only `src/nav.py`'s pages — on canvas-dev it opened `/` and missed a broken
  `/broken`. The route walk is the one `ajnkit.access` already uses (`_routes`).
- **Your app**: nothing to change — `canvas app update` brings it.

## 0.5.15 — 2026-10-10

Deployed, an app checks its own pages once it is up.

- `ajnkit.smoke` (Python), started by `web.platform`: when the app is deployed, it waits for `/healthz`,
  then opens each GET page with no parameter in its path over 127.0.0.1 — as a reader, and each page
  `src/nav.py` gives a rule as someone that rule lets in — and logs one line a page and a summary.
  `canvas deploy` and Canvas Studio read the summary: a page that answers 500 means the deploy is not
  done. A pod can pass /healthz while every page fails (Studio's evaluation). `PLATFORM_SMOKE=0`
  turns it off. GET only, once per start; nothing on a laptop or in tests.
- **Your app**: nothing to change — `canvas app update` brings it.

## 0.5.14 — 2026-10-10

One answer of a few: the `choice` component (Python).

- `choice(name, label, options, selected="", required=False)`: a labelled group of radio buttons,
  each option shown in full and the picked one marked — a quiz's question, a poll, a rating. Each
  question has its own `name`, so each is answered apart (Canvas Studio's evaluation wrote raw radios
  sharing one name: a candidate could answer one question of the whole test).
- **Your app**: nothing to change — `canvas app update` brings it.

## 0.5.13 — 2026-10-10

Each role sees its own menu; the AI client's skill says how to get data back.

- `src/nav.py`'s pages may name a rule as a third item — `("Questions", "/questions", "admin")` — and
  the page shell (Python) shows that page only to who the rule lets in (`rbac.allowed`, as `@require`
  decides). `ajnkit.web.pages(request)` gives the pages for who is asking; without a request, the
  pages with no rule. `canvas validate` checks the rule is declared, as it does for `@require`.
- The ajnkit-llm skill: a typed answer with `client().chat.completions.parse(…, response_format=Model)`,
  never a reply cut at its fences; a failed call is said, not swallowed.
- **Your app**: nothing to change — `canvas app update` brings it. To keep an admin's pages out of a
  member's menu, add the rule to their lines in `src/nav.py` (add-auth).

## 0.5.12 — 2026-10-10

An app tells Canvas Studio's preview it showed.

- The page shell (both stacks), when the page is framed — only the portal may frame an app (0.5.9) —
  posts `{ajnkit: "shown"}` to the frame's parent. Studio's preview offers "open it in a new tab" only
  when no app page said so, in place of a line under every preview. The message carries nothing else.
- **Your app**: nothing to change — `canvas app update` brings it.

## 0.5.11 — 2026-10-09

The chat's web search picks its filters reliably.

- `WEB_SEARCH_TOOL`'s descriptions tell the model, with examples, to put a source it is asked about in
  `sites` (Al Jazeera → aljazeera.com) and leave its name out of `query`; a relative time in `days`
  ('last month' 30); a named range in `after` and `before` ('in December 2022' → 2022-12-01 to
  2023-01-01). Tried on `gemini-flash-lite`: 0.5.10's words put outlets and dates into the query, or
  wrote `site:` itself; these chose the filters each time.
- **Your app**: nothing to change — `canvas app update` brings it.

## 0.5.10 — 2026-10-09

Web search by site and time frame.

- `search()` (llm package, both stacks) takes `sites` (`["aljazeera.com", "bbc.com"]`, at most 10),
  `after` and `before` (a date, or `"YYYY-MM-DD"`) and `days` (the last N days, counted in UTC; not with
  `after`). They are written into the query as the search engine's operators, after checks: a site
  must be a hostname (a path allowed), so none can carry an operator of its own; a date must be one,
  and `after` not later than `before`. A filter that is not one raises `ValueError` (Next `RangeError`)
  before anything is sent. Operators the query holds itself pass as they are.
- `domains` is now `sites`' old name, kept: the gateway kept only the first of several domains,
  without a word. `sites` keeps them all. `search_domain_filter` is no longer sent.
- `max_results` is 1 to 10, the search engine's most for one query — it was 1 to 20, and the gateway
  gave 10 anyway.
- `WEB_SEARCH_TOOL` (chat package) lets the model choose them: `sites` when the person names a source,
  `days` for "last week", `after` / `before` for dates they name — never operators written in the
  query. A filter it gets wrong comes back to it refused, to correct.
- The `search-web` skill has the whole of it: a route with `q`, `site`, `from`, `to`, `days`; a page's
  form; an answer from the results; the chat's tool, and today's date in its system prompt.
- **Your app**: nothing to change — `canvas app update` brings it. An app that passed `max_results`
  above 10, or several `domains`, moves to `max_results=10` and `sites`.

## 0.5.9 — 2026-10-09

Canvas Studio shows the app it is building (ADR-47).

- Deployed, the portal — and only the portal — may frame the app's pages: Studio's preview, beside the
  conversation. Its address is the app chart's `PLATFORM_PORTAL_URL`, read at each request, https
  only: `frame-ancestors <portal>`, and no `X-Frame-Options`. On your computer, and for any page that
  sets its own policy (an uploaded file), nothing may frame it, as before. `framer()` says which site
  may (`ajnkit.origin`; `@/canvas/auth/origin`).
- **Your app**: nothing to change — `canvas app update` brings it.

## 0.5.8 — 2026-10-09

Web search, on the AI key the app already has.

- `search(query, max_results=5, domains=…, country=…)` in the llm package (`ajnkit.llm`;
  `@/canvas/services` in Next): the web's results, best first — each a title, an address, a snippet
  and sometimes a date — through the platform's AI gateway, on the same key as the model. $0.005 a
  query, from the same budget as model calls. `SearchRefused` when the gateway refuses: the budget is
  used up (429), or the key may not search (403). No key is `NoAI`, as for `client()`.
- `WEB_SEARCH_TOOL` in the chat package: put it among `converse()`'s tools, and the model searches when
  a question needs the web. It tells the model the results are web pages to use, never instructions
  to follow.
- A new skill, `search-web`, says when and how; `ajnkit-llm`'s reference skill has the function.
- **Your app**: nothing to change — `canvas app update` brings it. A Python app without the llm package
  adds it with `canvas app add llm`.

## 0.5.7 — 2026-10-09

Twelve reports checked; these are the platform's half of the fixes.

- Speech has a budget: at most 8 calls to `chat.speak` and `chat.listen` at once in one app process
  (`SPEECH_AT_ONCE`, both stacks). The next one is refused at once with a 503 and `Retry-After: 1`,
  and the window tries it again. Each call holds one of the server's 40 threads for the whole gateway
  call (Python), so 40 speeches at once used to make the pages and the readiness probe wait (#119).
- The chat window reads an answer aloud in a few parts, not a call per sentence: the first sentence
  alone (the voice starts at once), then what came meanwhile, up to about 280 characters, fetched while
  the one before plays: one speech call in flight per window. A busy app's 503 is tried again (#121).
- `chat.table()`: a cell's line break of any kind — `\r` from a CSV or Windows, U+2028, U+2029 — becomes a
  space, as `\n` did, on both stacks; such a row ended the table, the rows after it shown as text. The
  chat window knows such a row as a row too. A `Decimal` (Postgres `numeric`) is rounded as a float is
  (Python) (#124).
- A 422 names where and what was wrong — `loc`, `msg`, `type`, the first 10 errors — and never writes the
  input back: FastAPI's own answered a 9 MiB body with the same 9 MiB (Python). An app's own
  `RequestValidationError` handler is kept. Node's answers never echoed a body.
- **Your app** (Python): `src/views.py`'s `def healthz()` becomes `async def healthz()`.
- **Your app**: `.gitignore`'s `data/` becomes `/data/` — `data/` also left out `src/static/data/` and
  every other folder named data, which then never shipped (#118).
- **Your app** (Python, made before these lines): `src/envs.py` gains `secret()` and `secret_file()`;
  `src/static/tw.css`'s `@source not "../../.agent"` becomes `"../../.agents"`; `pyproject.toml` gains the
  blueprint's `[tool.ruff.lint]` with its `select` — apply-update has each line (#122).

## 0.5.6 — 2026-10-09

Documentation only: each package's README says the settings it reads and where they come from (the
`score.yaml` resource, the Secret), and what it brings. Nothing in an app changes.

## 0.5.5 — 2026-10-09

What the two reviews left.

- Uploads: one person may hold 20 whole files no form has named yet (both stacks) — the disk is
  shared, and they were kept a week with no limit.
- An email address with a control character (NUL and the like) is refused before it is sent, on both
  stacks alike.
- The form cap sees a form a dependency takes when it is given to `include_router(...)` (Python).
- What can answer a request is worked out once per request, not up to three times (Python).
- `matches` lives in `ajnkit.identity` — `access` and `rbac` no longer import each other; `access.matches`
  still works. `@require` decides through `rbac.allowed`, as a chat's tools do. One set of reading methods
  for both checks, on both stacks.
- The packages test themselves: the core, email, media and llm have their own tests, beside the
  blueprints' tests of their behaviour in an app.
- **Your app**: nothing to change.

## 0.5.4 — 2026-10-09

A second review of both stacks, of 0.5.3's fixes first.

- The checks read the path the router matches: `request.url.path` ended at a decoded `?` or `#`, so
  `/healthz%3F/secret` passed as the readiness probe — skipping access — and `/api/ask%3F/delete` as
  an ask (Python).
- No WebSocket is let in: access is checked by an `http` middleware, which never sees one, and the
  platform provisions none (Python).
- The 256 MiB form cap only where every route that matches reads a form: a JSON route registered
  before a form route on an overlapping path keeps 10 MiB (Python).
- Whether a request only asks is looked at only for someone who may read, and its warning is said once
  per route, never once per path a caller makes up (Python).
- `chat.api_tools`: a path value that is only dots (`..`) is refused — the client folded it away, and
  `/api/users/../notes` reached `/api/notes`.
- Starting a large upload is one at a time on Next: 40 at once let 39 past the limit of 5.
- The chat window: a link's host is shown unless the label is that host — not when it merely contains
  it; a source link never starts `/\` (another site); and no `URL.canParse`, which older browsers lack.
- Next: the 411 for a body with no length is the proxy's alone — `PUT /media` streams and counts.
- `sdk/placeholders/publish.sh` names npmjs and PyPI on every call.
- **Your app**: a route a WebSocket served is refused now — say so in `report-issue` if the app needs
  one.

## 0.5.3 — 2026-10-09

A security review of both stacks.

- `@require` takes the view's request by its type: a body model with a `headers` field could say who
  the caller was.
- The 256 MiB form cap is for a route that takes a form or a file (`Form`, `UploadFile`); anywhere
  else a multipart body has the 10 MiB cap of any other — the sender's Content-Type no longer raises it.
- `@access.asks` holds only where the marked route is the one route that can answer: a writing route
  on the same path (or a pattern that takes it) closes it to readers, logged once. A marked route with
  a path parameter is an ask now, and two routes sharing a function name no longer close each other.
- Next: an `ASKS` path is never an ask for a server action (`Next-Action`, a multipart body); a body
  sent with no length is refused (411) rather than cut off at 10 MB; `call()` keeps its timeout when
  given a signal.
- `chat.api_tools` (Python): a tool calls its own route only — the model's arguments cannot name
  another path, a value goes into the path escaped, and an argument the route does not declare is
  dropped.
- The chat window shows a link no browser can open as text, instead of stopping mid-answer.
- Large uploads: 5 under way per person (100 for the app); a file a crashed save left half-written is
  cleared after a day; a full disk during `media.save()` is a `MediaRejected`, not a 500 (Python).
- `log.info(…, extra={…})` keeps the extra fields in the JSON line (Python).
- An email address with a trailing newline is refused before it is sent (Python).
- The Python core names the versions it is tested on (`fastapi>=0.142`, `starlette>=1.7`, …).
- **Your app**: a test that monkeypatches `email.client` patches `email._client`; a test that calls a
  `@require` view directly passes a real `starlette.requests.Request`. A route that reads
  `await request.form()` itself, over 10 MiB, takes its file as a parameter (`photo: UploadFile`). A
  route marked `@access.asks` that shares its path with another route: give it a path of its own. Next:
  `src/asks.ts` lists route handlers only, never a page.

## 0.5.2 — 2026-10-08

- This changelog travels inside the core package, and `canvas update` writes it to the app's
  `packages/CHANGELOG.md` from the release the app has — so a patch from the portal brings its own
  **Your app** lines to `apply-update`, not the ones of the release the canvas carries.
- **Your app**: nothing to change.

## 0.5.1 — 2026-10-08

- A docstring on each public function of the core that had none (`identity.Caller` and `caller`,
  `access.matches`, `allowed` and `enforce`, `http.client`, `settings.get`) — what an assistant reads
  when it looks the code up. The first release published to the registry alone: `canvas update` brings
  it, with no new canvas.
- **Your app**: nothing to change.

## 0.5.0 — 2026-10-08

From the registry, and only what the app uses.

- Every release is in Artifact Registry, served by the portal to a signed-in canvas. `canvas update`
  takes the newest patch of its version (0.5.x) from there into `packages/` — a fix ships without a
  canvas release — and builds and CI go on installing from `packages/`, with no credential.
- A Python app's `packages/` holds only what it uses: the core, and each feature added with
  `canvas app add <feature>` (llm, chat, media, email) — which fetches the package, and any it needs,
  names it in `pyproject.toml` and `uv.lock`, and brings its reference skill. The task skills run it.
- **Your app**: nothing to change. A Python app keeps the features it has; the wheels of those it does
  not use leave `packages/`.

## 0.4.1 — 2026-10-08

- The first release in Artifact Registry (`ajnkit-python`, `ajnkit-npm`), where the portal serves it to
  `canvas update`. The npm packages publish only there (`publishConfig`), never to npmjs.
- **Your app**: nothing to change.

## 0.4.0 — 2026-10-08

Every package documents itself, says what is public, and brings its reference skill.

- A README in each package (in the wheel and the tarball): what it does, its public API with an
  example, the settings it reads, what it raises.
- Python: `__all__` in every module; type-checked (pyright). npm: an index per package —
  `import { client } from "@ajnkit/llm"` — beside the module paths apps use.
- Reference skills: `ajnkit-core`, `ajnkit-llm`, `ajnkit-chat`, `ajnkit-media`, `ajnkit-email`, in the
  app's `.agents/skills/` while it has the package; the blueprint's task skills point to them.
- A Next app's update forgets the ajnkit packages it had locked before installing the new ones (their
  file names do not change between versions).
- **Your app**: nothing to change.

## 0.3.0 — 2026-10-08

The platform's packages are named **ajnkit** and are five a stack: a core, and one per feature.

- Python: `ajnkit-core` (settings, identity, logger, origin, http, access, rbac, db, web, docs, the shell
  and components), `ajnkit-llm`, `ajnkit-chat`, `ajnkit-media`, `ajnkit-email`. Imports are
  `from ajnkit import …`; `src/utils/<x>.py` is still the same module.
- Next.js: `@ajnkit/core`, `@ajnkit/llm`, `@ajnkit/chat`, `@ajnkit/media`, `@ajnkit/email` — every
  one in every app; `@/canvas/...` still names them.
- A new Python app has the core; each feature's skill adds its package (`uv add ajnkit-llm`…).
- **Your app**: `canvas app update` replaces `canvas-sdk` (or `@canvas/sdk`) with every ajnkit package —
  the features it had — and nothing else needs to change if it imports `src.utils.<x>` or
  `@/canvas/...`. Code that imports `canvas.<x>` (written with 0.2.0) becomes `ajnkit.<x>`.

## 0.2.0 — 2026-10-08

Every platform module is in the package now.

- Python: `identity`, `logger`, `origin`, `http`, `access`, `rbac`, `db`, `email`, `web`, `docs`,
  `chat` and `media` are `canvas.<name>`. `src/utils/<name>.py` is the same module, so
  `from src.utils import access` still works — new code imports `canvas.<name>`.
- Python: the page shell and the components (`platform/shell.html`, `platform/ui.html`) and their
  styles and scripts (`/static/platform/`) come from the package; `run.py` serves the app through
  `canvas.web.platform`, which adds them, large uploads and the access checks wherever `src/app.py`
  has not.
- Next.js: `auth`, `config`, `services`, `ui` and the proxy's checks are `@canvas/sdk/<path>`;
  `@/canvas/...` names them, so imports are unchanged. Tailwind reads the components' classes from
  the package (`src/canvas/ui/styles/platform.css`).
- The platform's own tests of these modules leave the app's `tests/` (an update removes them); they
  run with the SDK. The app keeps its own, and the probe's (`test_health.py`, `health.test.ts`, `db.test.ts`).
- **Your app**: nothing to change. In a Python app, `src/app.py` may drop
  `app.include_router(media.router)` and `app.middleware("http")(access.enforce)` — `run.py` adds
  them — but keeping them is harmless.

## 0.1.1 — 2026-10-08

- `canvas.llm` reads the app's `src/envs.py`, as `src/utils/llm.py` did: a test that turns AI off
  there turns it off for the platform's client too.

## 0.1.0 — 2026-10-08

- The AI client, `canvas.llm` / `@canvas/sdk/llm`. A Python app adds it with
  `uv add "canvas-sdk[llm]"` (the `request-llm` skill); `src/utils/llm.py` names it.
- **Your app**: nothing to change.
