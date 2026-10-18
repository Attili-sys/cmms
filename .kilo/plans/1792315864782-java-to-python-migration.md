# Atlas CMMS — Java → Canvas Python Migration Plan

> **Who executes this plan:** a smaller coding agent, running one phase at a time, with the user available for the gated questions. The prompts are deliberately verbose and prescriptive — the agent should not need to improvise.
>
> *History: an earlier revision of this plan proposed raw SQLAlchemy / python-jose / WeasyPrint instead of the mandatory `ajnkit` SDK, kept Liquibase as the DDL owner (incompatible with `canvas deploy`), ported the full Java JWT stack even though Canvas SSO replaces it, and treated `canvas deploy` as a one-day final step. That revision is in git history; this file is the one to execute.*

---

## 0. Scope decisions (locked by the user, do not re-litigate)

| Decision | Choice | Reason |
|---|---|---|
| Deploy target | **Canvas** (company sandbox). Canvas does not run Java and never will — the end state is 100% Python | Entire point of the migration |
| Authentication | **Canvas SSO** (`auth: sso`) — not a ported JWT stack | User confirmed "canvas sso is freaking easy"; wipes ~500 LDAP + ~400 OAuth + password-reset lines |
| Mobile app | **Parked, not deleted.** `mobile/` stays in the repo but is frozen — it will stop working the moment the Java API in `api/` is removed (Phase 13), because it talks Bearer JWT. Future work: rewire mobile to the Python Canvas API using mobile SSO (MSAL) or an app-issued API key. §12 freezes it and documents the resurrection path | User: "ofc in future i will need this mobile app" + "fully python" |
| Frontend | **React (`frontend/`) served as static files by the Python Canvas app**, same origin as the API | Single Canvas app = single SSO envelope; no CORS; no second deploy |
| Database schema owner | **SQLAlchemy models in `atlas-cmms/src/models.py`**, migrated via `canvas db revision` | Required for `canvas deploy`. Existing Postgres rows transferred via a one-time `canvas db import` from a dump |
| Self-hosted gate | `is_unrestricted_self_hosted()` returns `True` whenever running on Canvas | Branch `migrate-python` carries the `unrestricted-selfhosted` policy ([AGENTS.md](../../AGENTS.md) §Self-hosted edition) |
| Java API — dev-time only | Runs locally in docker-compose ONLY as the oracle for Phase 2 contract capture and the Phase 6 strangler-fig cutover. **It is never deployed anywhere.** After Phase 10 cutover + Phase 11 Canvas deploy, the Java tree in `api/` is deleted from the repo. See §13 | Canvas does not run Java servers; keeping Java around after cutover is dead weight |

**What NOT to port** (gone with Canvas SSO):

- `JwtTokenProvider.java`, `JwtTokenFilter.java`, `RefreshToken` entity, `/auth/refresh` endpoint
- `OAuth2AuthenticationSuccessHandler.java`, Google social login
- `LdapService.java`, `LdapSyncJob.java`, `LdapSyncJobScheduler.java`, `/auth/signin/ldap`
- `/auth/signup`, `/auth/resetpwd`, `/auth/updatepwd`, `/auth/activate-account`, `VerificationToken`, `UserInvitation`
- Password hashing (BCrypt), password column in `User`

**What NOT to port** (gone with CLOUD_VERSION=false policy — see [UNRESTRICTED_SELFHOSTED.md](../../UNRESTRICTED_SELFHOSTED.md)):

- `PaddleService`, `SubscriptionChangeRequest` logic, every `/subscriptions/*` write path
- `KeygenService`, license-file reads
- `SubscriptionEndJob`, trial-expiry scheduling
- Any `check_usage_based_limit(...)` call — becomes a no-op

---

## 1. The executor contract (how the small agent works)

Read this once at the start of every phase. The small agent is strict and literal — this contract tells it how to behave.

1. **One phase at a time.** Finish a phase's verification gate before starting the next. If the gate fails, loop inside the phase, do not skip ahead.
2. **Read-before-write.** Every phase starts with a *Reading list*. Open each file with `Read`. Do not write code until the reading list is done.
3. **ajnkit first.** If the task is DB access, current user, secrets, outbound HTTP, logs, email, uploads, or AI → check `atlas-cmms/.agents/skills/ajnkit-core/SKILL.md` (and sibling ajnkit skills) and use the ajnkit function. **Never** import `psycopg`, `sqlalchemy.create_engine`, `requests`, `httpx`, `jose`, `jwt`, `bcrypt`, `smtplib`, `boto3`, `openai`, `anthropic` directly.
4. **Source of truth is `.canvas/legacy/`.** Every Python function being ported has a Java twin somewhere under `.canvas/legacy/api/src/main/java/com/grash/`. Open it with `Read` before writing. If you cannot find the twin, STOP and ask.
5. **Preserve the frontend contract.** The React app sends JSON shapes defined by Java `*ShowDTO` / `*PostDTO` classes. Response JSON from the Python port must match byte-for-byte except for timezone representation (ISO 8601 vs ms epoch — see §4).
6. **No new abstractions.** Translate control flow 1:1. Loops stay loops, `if/else` stays `if/else`, service classes stay service classes. The time to make it elegant is after `canvas deploy` is green.
7. **Verification is a command, not a feeling.** The gate at the bottom of each phase is a shell command. Run it, paste the summary, do not mark the phase done until it is green.
8. **Human gates.** Any step marked **🧑 ASK USER** is non-negotiable — stop, ask, wait for a reply. The agent does not pick for the user.
9. **Context hygiene.** When a route group is finished, mark the file complete in the per-phase todo list and discard the Java source from working memory. Do not re-read the whole Java tree every phase.
10. **Commit per phase.** At the end of each phase, after the gate passes, `git add` only files touched this phase, commit with the message `migrate: phase <N> — <summary>`, and `git push` to the `migrate-python` branch.

---

## 2. Verified facts (checked against this repo as of 2026-10-18)

- `api/src/main/java/com/grash/`: **72** `*Controller.java`, **86** `*Service.java`, **76** `@Entity` classes, **13** files in `security/`, **5** `*Job.java`
- `api/src/main/resources/db/`: **121** Liquibase changelogs
- `api/src/main/resources/templates/`: **20** Thymeleaf `.html` files
- Frontend auth: [frontend/src/utils/api.ts:135](../../frontend/src/utils/api.ts#L135) sends `Authorization: Bearer <accessToken>` — this line will be removed in §9
- Branch: `migrate-python` (git status at start of this session)
- `cmms/` folder is a stale pytest/ruff/venv cache — ignore. The `cmms/AGENTS.md` reference at [AGENTS.md:3](../../AGENTS.md#L3) is dead; fix as part of Phase 0.
- No `atlas-cmms/` folder yet. It is created in Phase 1.

---

## 3. Risk register (confirmed, not speculative)

| Risk | Confirmed by | Mitigation (concrete, this plan) |
|---|---|---|
| Canvas SSO breaks the React login flow | Frontend posts to `/auth/signin` and reads JWT from body ([frontend/src/content/pages/Auth](../../frontend/src/content/pages/Auth)) | §9: strip JWT from React, serve from same origin, map Canvas SSO identity → `User` row on first hit |
| `canvas db revision` won't accept 121 pre-existing Liquibase changelogs | Canvas blueprint expects SQLAlchemy as DDL source | §4: dump prod schema → write **one** SQLAlchemy model file that reflects it exactly → `canvas db baseline` to mark it as applied → `canvas db import` for data |
| Thymeleaf PDFs rely on iTextPDF layout that WeasyPrint renders differently | 20 templates in `api/src/main/resources/templates/`, custom header/footer/page-break CSS | §8: prototype the hardest template (full WO report) in Phase 1, visual-diff before porting the rest |
| `SpecificationBuilder` dynamic queries | Every `POST /{resource}/search` endpoint | §5: port as `atlas-cmms/src/utils/search.py` before any route group |
| Envers `_AUD` tables and `@PostLoad` company isolation | Confirmed: `WorkOrderHistory` is a plain entity; `_AUD` tables never leave Java | Port `WorkOrderHistory` as a normal model; implement company isolation in an ajnkit-core dependency, not `@PostLoad` |
| `jscpd --compare` across Java and Python | Supported by jscpd semantic model (CodeRankEmbed, 548 MB) per [code-migration/SKILL.md](../skills/code-migration/SKILL.md) | Use it as a progress thermometer, not a correctness gate. Correctness gate is `pytest` + API contract diff |
| Mobile app sends Bearer JWT | [mobile/](../../mobile/) | §12: mobile stays on the Java API in docker-compose during migration; deprecation decision is a separate, later conversation |
| `canvas app adapt` command signature for a Java app | Not explicitly documented in [canvas-adapt/SKILL.md](~/.claude/skills/canvas-adapt/SKILL.md) — only Next.js example given | Phase 1 **invokes the `canvas-adapt` skill interactively** rather than hard-coding the command; the skill walks the user through the right flow for a Java-source refactor |

---

## 4. Pydantic + JSON contract rules (read before writing any route or schema)

Every schema class in `atlas-cmms/src/schemas/` must obey these. The React frontend will break on silent mismatches.

- **Field casing:** Python attributes stay `snake_case`; JSON over the wire is `camelCase`. Use:
  ```python
  from pydantic import BaseModel, ConfigDict
  from pydantic.alias_generators import to_camel

  class _CamelModel(BaseModel):
      model_config = ConfigDict(
          populate_by_name=True,
          alias_generator=to_camel,
          from_attributes=True,
      )
  ```
- **Nested entity references** serialize as `{"id": N}` only (matching Java `IdDTO`). Define `class IdRef(_CamelModel): id: int` once and reuse.
- **Dates / timestamps:** Java Jackson emits `long` milliseconds since epoch for `Date`. Use a `field_serializer` that returns `int(dt.timestamp() * 1000)`; on input accept both `int ms` and ISO 8601 strings.
- **Enums:** emit the enum **name** (e.g. `"HIGH"`), not the ordinal — mirrors Jackson default.
- **Pagination envelope:** every `POST /{resource}/search` returns:
  ```json
  {"content": [...], "totalElements": N, "totalPages": N, "number": N, "size": N,
   "first": true, "last": false, "numberOfElements": N, "empty": false}
  ```
  Implement once in `atlas-cmms/src/utils/pagination.py: as_spring_page(items, total, page_req) -> dict`.
- **Mobile `X-Platform` header:** accept, do not validate, do not log at WARN.
- **Mobile request bodies that include `{"company": {"id": N}}`:** ignore the client value, always use `current_user.company_id`.
- **Empty-body endpoints** (`204 No Content`) — do not return `{}`; return `Response(status_code=204)`.

Contract-check procedure: run the Java API in docker-compose, replay a canned request against it and against the Python port, then `jd` or `deepdiff` the two JSON bodies. See §6 for how this becomes the per-route-group gate.

---

## Phase 0 — Pre-flight (human-interactive, 1 session) 🧑

**Who runs this:** the user, with the agent assisting. The small agent CANNOT finish Phase 0 alone — the Canvas-adapt skill requires explicit user yes/no gates.

### 0.1 Branch and backup

```bash
cd /Users/attiliab/Documents/GitHub/cmms
git status                                           # clean working tree expected
git branch --show-current                            # must be migrate-python
git tag pre-canvas-migration-$(date +%Y%m%d)         # restorable snapshot
git push --tags
```

### 0.2 Fix the stale cmms/ pointer in AGENTS.md

- Open [AGENTS.md:3](../../AGENTS.md#L3). The sentence beginning "cmms/ is a separate Canvas app..." is stale (the folder is just a venv).
- Replace with: `` `cmms/` is a leftover venv — ignore. The Canvas Python port lives in `atlas-cmms/` (see `.kilo/plans/1792315864782-java-to-python-migration.v2.md`). ``
- Remove the `cmms/AGENTS.md` row from the "Read when" table.
- Commit as `docs(agents): point to atlas-cmms, drop dead cmms/ pointer`.

### 0.3 Invoke the canvas-adapt skill 🧑

Agent prompt (paste verbatim into the small agent):

> Load the `canvas-adapt` skill. Our folder (`/Users/attiliab/Documents/GitHub/cmms`) already contains an app (the Java `api/`). We want **Refactor**, not Adapt — the goal is a Python Canvas app under `atlas-cmms/` with the Java source copied into `atlas-cmms/.canvas/legacy/` for the port to read from. The user's answer to the backup prompt is "yes, snapshot tag was pushed in 0.1." The user's answer to "which way" is "Refactor." The app name is `atlas-cmms`. Walk the skill's §1 → §2 → §4 steps and run the commands it instructs. Do not improvise command names — ask the skill. Stop at the end of §4 step 3 (blueprint files landed) and report back.

Expected result after 0.3:

- `atlas-cmms/` exists with `score.yaml`, `Procfile`, `src/app.py`, `src/envs.py`, `src/views.py`, `src/api.py`, `packages/` (ajnkit), `tests/`, `.agents/skills/adapt-app/SKILL.md`, `.agents/skills/ajnkit-core/SKILL.md`, `.canvas/legacy/` with the Java source copied in, `.canvas/ported` marker.

### 0.4 Read the newly-arrived skills

```bash
cat atlas-cmms/.agents/skills/adapt-app/SKILL.md
cat atlas-cmms/.agents/skills/ajnkit-core/SKILL.md
ls atlas-cmms/packages/           # confirm ajnkit packages
```

Save a one-paragraph summary of each skill to `atlas-cmms/MIGRATION_NOTES.md` so later phases don't need to re-read in full.

### 0.5 Canvas resources needed (declare now, add in Phase 1)

- Postgres (`canvas app add postgres` — or whatever the adapt-app skill prescribes). Only one DB; this is a single Canvas app.
- No LLM, no chat, no media, no email at Phase 1 (add in Phase 8 for PDFs/email).

### Phase 0 gate

```bash
cd atlas-cmms && canvas validate
```

Must exit 0. Commit with `migrate: phase 0 — canvas scaffold at atlas-cmms/`.

**🧑 ASK USER before continuing to Phase 1:** "Phase 0 is done. Ready to lock the DB schema (Phase 1) and start the API contract capture (Phase 2) in parallel? These are both read-only against prod data. Y/N."

---

## Phase 1 — Schema freeze (SQLAlchemy models as the ONE source of DDL)

**Why first:** `canvas db revision` reads `atlas-cmms/src/models.py` and generates migrations. Everything downstream (route groups, tests, data import) binds to column names and types. Lock this before writing any route.

### 1.1 Reading list

- `atlas-cmms/.agents/skills/ajnkit-core/SKILL.md` — the sections on DB, models, migrations
- `.canvas/legacy/api/src/main/resources/db/Agents.md` — foreign-key / sequence rules the Java side enforced
- Every `.canvas/legacy/api/src/main/java/com/grash/model/**/*.java` — all 76 entities. Group by package (see §1.5).

### 1.2 Dump the current Postgres schema (ground truth)

The Liquibase changelogs are not the ground truth any more — what *applied* to prod is. From docker-compose:

```bash
docker compose exec postgres pg_dump --schema-only --no-owner --no-privileges atlas > /tmp/atlas-schema.sql
```

- Open `/tmp/atlas-schema.sql`. Every `CREATE TABLE` here is a model you must write. Every column, type, nullable, default, and FK constraint is a field on that model. Every `CREATE SEQUENCE` must appear in the model config.
- The `*_AUD` Envers tables are **not** modeled (Envers was Java-internal, never exposed). Confirm by searching the Java tree: `rg -l "_AUD" api/src/main/java/` should return zero results.

### 1.3 Write the models

**File layout:** one file per aggregate root under `atlas-cmms/src/models/`:

```
atlas-cmms/src/models/
  __init__.py              # re-exports all models
  _base.py                 # DateAudit, Audit, CompanyAudit abstract bases
  _enums.py                # Status, Priority, AssetStatus, PermissionEntity, RoleType, PlanFeatures, LicenseEntitlement, …
  company.py               # Currency, Company, SubscriptionPlan
  user.py                  # Role, UserSettings, User, SuperAccountRelation
  team.py, vendor.py, customer.py
  asset.py                 # Location, AssetCategory, Asset, FloorPlan, Deprecation
  work_order.py            # WorkOrderBase, WorkOrder, WorkOrderHistory, Request, Labor, AdditionalCost
  task.py                  # TaskBase, Task, TaskOption, Checklist
  pm.py                    # PreventiveMaintenance, Schedule, WorkOrderMeterTrigger
  part.py                  # Part, PartCategory, PartQuantity, PartTransaction, MultiParts
  meter.py                 # Meter, MeterCategory, Reading
  file.py                  # File
  custom_field.py          # CustomField, CustomFieldValue, FieldConfiguration
  workflow.py              # Workflow, WorkflowAction, WorkflowCondition
  webhook.py, notification.py, comment.py
  purchase_order.py        # PurchaseOrder, PurchaseOrderCategory
  misc.py                  # UiConfiguration, GeneralPreferences, UserAppStats, CustomSequence, Relation, ApiKey, RequestPortal*, Shift*
```

**Column rules (apply to every model):**

- Use the SQLAlchemy base and session that `ajnkit-core` exposes. Do **not** call `declarative_base()` yourself. The adapt-app skill will tell you the exact import — look it up, don't guess.
- Column names must exactly match the SQL dump: Java uses `naming_strategy=snake_case` by default. Verify `created_at` not `createdAt` in the DB.
- Primary keys: `id` as `BigInteger`, pulled from a sequence named `<table>_seq` with `increment 50` (Hibernate hilo pattern — see `db/Agents.md`).
- Foreign keys: `ondelete="CASCADE"` on NOT NULL FKs, `ondelete="SET NULL"` on nullable ones. (This matches the Java rule.)
- `created_at` / `updated_at`: `TIMESTAMP WITH TIME ZONE`, defaults `now()`.
- `created_by_id` / `updated_by_id`: nullable `BigInteger` FKs to `user.id`, set by an ajnkit DB event hook, not in model definitions.
- `company_id` on every `CompanyAudit` subclass: NOT NULL FK, `ondelete="CASCADE"`.

### 1.4 Enum policy

- Python `enum.StrEnum` subclass per Java enum, values exactly matching the Java `.name()` strings.
- Stored in Postgres as `VARCHAR`, not `enum type` (Java/Hibernate uses `@Enumerated(STRING)`).

### 1.5 Order of writing (dependency-first)

The agent writes models in this order, one group at a time, committing after each group passes `python -c "from src.models import *; print('ok')"`:

| Group | Models |
|---|---|
| G1 | `_enums`, `_base` (abstract) |
| G2 | `Currency`, `SubscriptionPlan`, `Company` |
| G3 | `Role`, `UserSettings`, `User`, `SuperAccountRelation`, `ApiKey` |
| G4 | `Team`, `Vendor`, `Customer`, `GeneralPreferences`, `UiConfiguration` |
| G5 | `Location`, `AssetCategory`, `Asset`, `FloorPlan`, `Deprecation`, `File` |
| G6 | `TaskBase`, `Task`, `TaskOption`, `Checklist` |
| G7 | `WorkOrderBase`, `WorkOrder`, `WorkOrderHistory`, `Request`, `Labor`, `AdditionalCost` |
| G8 | `PreventiveMaintenance`, `Schedule`, `WorkOrderMeterTrigger` |
| G9 | `Part`, `PartCategory`, `PartQuantity`, `PartTransaction`, `MultiParts` |
| G10 | `Meter`, `MeterCategory`, `Reading` |
| G11 | `CustomField`, `CustomFieldValue`, `FieldConfiguration`, `CustomSequence` |
| G12 | `Workflow`, `WorkflowAction`, `WorkflowCondition` |
| G13 | `WebhookEndpoint`, `Notification`, `Comment` |
| G14 | `PurchaseOrder`, `PurchaseOrderCategory` |
| G15 | `RequestPortal`, `RequestPortalField`, `Shift*`, `UserAppStats`, `Relation` |

### 1.6 Verify the models match the dump

Write `atlas-cmms/tests/test_schema_matches_dump.py`:

- Load `/tmp/atlas-schema.sql` using `sqlalchemy.create_engine("sqlite:///:memory:")` + `sqlparse` to extract `CREATE TABLE` DDL into a `{table: {column: (type, nullable, default, fk)}}` dict.
- Load the SQLAlchemy metadata via `src.models` and build the same dict.
- Assert the two dicts are equal, with a clear diff on failure.

### 1.7 Baseline migrations against the dump

```bash
cd atlas-cmms
canvas db revision --autogenerate -m "baseline from liquibase dump"
# Open the generated migration and REPLACE its body with a no-op (op.execute("-- schema was created by liquibase; this baseline just marks it")) OR
# diff the migration against /tmp/atlas-schema.sql and keep only the deltas (ideally none).
canvas db baseline       # or whatever ajnkit-core calls to mark the current state applied without running it
```

(If the actual Canvas commands differ, follow `ajnkit-core/SKILL.md` — do not improvise.)

### Phase 1 gate

```bash
cd atlas-cmms
uv run pytest tests/test_schema_matches_dump.py -v         # all 76 tables match
uv run python -c "from src.models import *; print(len(Base.metadata.tables))"   # prints 76
canvas validate                                             # still green
```

Commit as `migrate: phase 1 — SQLAlchemy models match liquibase schema`.

---

## Phase 2 — Capture the API contract from the running Java (parallel with Phase 1 OK)

**Why:** every ported route must respond with the same JSON shape as the Java original. We cannot verify that from source code alone — we need recorded responses.

**Java is dev-time only here.** We run it once in docker-compose, record the responses as static JSON fixtures, then never need the Java process again. The recorded fixtures are what the Phase 6 contract tests diff against; no live Java is required after Phase 2 finishes.

### 2.1 Start the Java API

```bash
cd /Users/attiliab/Documents/GitHub/cmms
docker-compose up -d postgres api
curl -s http://localhost:8080/health      # expect 200
```

### 2.2 Seed a reproducible dataset

- Export the current demo seed if one exists (`.canvas/legacy/api/src/main/resources/data.sql` or similar) OR
- Write `scripts/seed_demo.py` that uses the Java `/signup` + `/companies/demo` endpoints to create one company with: 2 users (admin, technician), 3 assets, 2 locations, 1 PM schedule, 3 WOs (open/in-progress/complete), 1 PO, 1 request, 3 parts, 1 meter with 2 readings, 1 workflow.
- Snapshot the DB: `docker compose exec postgres pg_dump atlas > fixtures/seed.sql`.

### 2.3 Record responses

Create `fixtures/contract/`. Add `scripts/record_contract.py`:

- Signs in as the admin → captures JWT
- For every endpoint listed in `fixtures/contract/endpoints.yaml` (see 2.4), issues the request, writes `fixtures/contract/<METHOD>_<path>.json` with `{"request": {...}, "response_status": N, "response_body": ..., "response_headers": {...}}`.

### 2.4 Endpoint catalog

Generate `fixtures/contract/endpoints.yaml` by scraping the Java controllers. The agent writes `scripts/catalog_endpoints.py` that:

- Walks `.canvas/legacy/api/src/main/java/com/grash/controller/**/*.java`
- For each class with `@RequestMapping("/x")`, enumerates methods with `@GetMapping`/`@PostMapping`/`@PatchMapping`/`@DeleteMapping`
- Emits YAML: `- {method: GET, path: /work-orders/{id}, controller: WorkOrderController, java_method: getById, sample: {id: 1}}`

Target: ~400 endpoints across 72 controllers. Review visually before using.

### 2.5 Contract-diff helper

Write `atlas-cmms/tests/contract.py`:

```python
def diff_against_java(method: str, path: str, py_client, path_params=None, body=None):
    fixture = json.loads(open(f"fixtures/contract/{method}_{path_safe(path)}.json").read())
    py_resp = py_client.request(method, path.format(**(path_params or {})), json=body)
    assert py_resp.status_code == fixture["response_status"]
    diff = deepdiff.DeepDiff(fixture["response_body"], py_resp.json(),
                             ignore_order=False, exclude_regex_paths=[r"root\['createdAt'\]"])
    assert not diff, f"contract drift:\n{diff}"
```

Per-route-group tests in Phase 6 import this helper.

### Phase 2 gate

```bash
ls fixtures/contract/*.json | wc -l            # ≥ 350 (every GET + a representative POST/PATCH per controller)
uv run pytest tests/test_contract_fixtures_loadable.py -v
```

Commit as `migrate: phase 2 — captured API contract fixtures from java`.

---

## Phase 3 — Platform-provided primitives (ajnkit-core wiring)

**Why:** every route in Phase 6 will reach for these. Build them once, correctly.

### 3.1 Reading list (strict)

- `atlas-cmms/.agents/skills/ajnkit-core/SKILL.md` — read the whole thing
- `atlas-cmms/packages/ajnkit*/` — glance at the package's `__init__.py` to know the exposed surface

### 3.2 Build these modules, in this order

Each module is one file. Each has a 1-paragraph docstring citing the ajnkit function it wraps.

| File | Purpose | Must use ajnkit for |
|---|---|---|
| `src/deps/db.py` | FastAPI dependency returning a `Session` scoped to the request | ajnkit-core DB |
| `src/deps/current_user.py` | Depends → returns `User` row for the Canvas SSO identity on this request. On first visit: auto-provision (create `User`, assign to default `Company` or prompt for company selection — see §3.3) | ajnkit-core user |
| `src/deps/company.py` | Depends on `current_user`, enforces `entity.company_id == current_user.company_id`. ROLE_SUPER_ADMIN bypasses. `SuperAccountRelation` grants cross-company access | pure Python, uses `current_user` |
| `src/deps/permissions.py` | `require_permission(entity: str, action: str)` → FastAPI dependency that reads `User.role.entityPermissions` / `User.role.generalPermissions` and 403s if missing | pure Python |
| `src/deps/rate_limit.py` | **CHECK FIRST:** is rate limiting a Canvas platform concern? If yes, skip this file. If no, use `ajnkit`'s rate-limit helper if one exists, else document the gap in `MIGRATION_NOTES.md` and leave rate limiting off until the user decides | TBD |
| `src/utils/pagination.py` | `as_spring_page(items, total, page_req) -> dict` returning the Spring envelope (§4) | pure Python |
| `src/utils/dates.py` | Jackson-compatible ms-epoch (de)serializers for Pydantic | pure Python |
| `src/schemas/_base.py` | `_CamelModel`, `IdRef` (§4) | pydantic |
| `src/schemas/errors.py` | Error envelope matching the Java `ApiError` shape (open [GlobalExceptionHandler.java](../../api/src/main/java/com/grash/exception/GlobalExceptionHandler.java) to see the exact fields) | pydantic |
| `src/http/app.py` | FastAPI app factory: registers error handlers that produce the Java-matching error envelope, mounts `src/routes/*` routers, mounts `frontend/build/` static (deferred to §9), serves `GET /healthz` for the Canvas health check | FastAPI |

### 3.3 Auto-provisioning on first SSO sign-in (locked: single-company auto-join)

Policy: **single-company mode**. There is exactly one `Company` row seeded on first boot (name is read from the `COMPANY_NAME` env var; `COMPANY_NAME` defaults to "Atlas CMMS"). Every Canvas SSO identity that lands on the app is auto-joined to that one Company with role `ROLE_CLIENT`. An admin promotes them later via the existing user-management screens.

Implementation rules for `src/deps/current_user.py`:

- Pull the SSO identity using the ajnkit-core helper named in `atlas-cmms/.agents/skills/ajnkit-core/SKILL.md` (search the skill for "current user" / "sso" / "whoami" and use that exact function — do not import a lower-level library). Record the exact function name in `MIGRATION_NOTES.md` for future readers.
- Map the SSO claims to `User` fields:
  - `User.email` ← SSO email claim
  - `User.first_name` / `User.last_name` ← SSO name claims (split on last space if only `name` is present)
  - `User.company_id` ← the single bootstrapped `Company.id`
  - `User.role_id` ← the `Role` row named "User" in that Company (seed it in the bootstrap along with "Admin", "Technician", "Requester" — mirror [RoleType enum values](../../.canvas/legacy/api/src/main/java/com/grash/model/enums/RoleType.java))
  - `User.password` / `User.password_updated_at` ← nullable, never set (SSO owns auth)
  - `User.enabled` ← `True`
- First-ever SSO sign-in (empty `User` table): the user becomes `ROLE_SUPER_ADMIN` of the bootstrapped Company. This is the "god admin" who then promotes others. Record a `logger.warning` so the event is auditable.
- The dependency is `async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:` — cache the lookup on `request.state` so one HTTP request does one DB read.

Company bootstrap runs once on container startup via an ajnkit-core startup hook (or FastAPI `@app.on_event("startup")` if the skill offers no hook). It is idempotent: if any `Company` exists already, it is a no-op.

### 3.4 Error envelope

Open [api/src/main/java/com/grash/exception/GlobalExceptionHandler.java](../../api/src/main/java/com/grash/exception/GlobalExceptionHandler.java) and mirror every exception type (CustomException, EntityNotFoundException, AccessDeniedException, MethodArgumentNotValidException, DataIntegrityViolationException, …) to a FastAPI exception handler that returns:

```json
{"message": "...", "code": 404, "fieldErrors": [{"field": "name", "message": "must not be blank"}]}
```

### Phase 3 gate

```bash
cd atlas-cmms
uv run pytest tests/deps/ tests/utils/ tests/schemas/ -v
uv run uvicorn src.http.app:app --port 8081 &
curl -s http://localhost:8081/healthz          # expect {"ok": true}
kill %1
```

Commit as `migrate: phase 3 — ajnkit primitives (db, auth, perms, pagination, errors)`.

---

## Phase 4 — SearchCriteria utility (one dependency, every route group needs it)

### 4.1 Port target

`atlas-cmms/src/utils/search.py` — translates:

- Java `SpecificationBuilder.java`, `FilterField.java`, `SearchCriteria.java` → Python
- Input: a Pydantic model `SearchCriteria` with `filterFields: list[FilterField]`, `pageNum: int`, `pageSize: int`, `sortField: str`, `direction: Literal["ASC","DSC"]`
- Output: SQLAlchemy `select()` statement, filterable by every operator the Java version supports: `eq, ne, gt, lt, gte, lte, like, in, between, isNull, isNotNull`

### 4.2 Preserve quirks (write a test for each)

- `like` wraps value in `%...%` and uses `ILIKE` for case-insensitivity
- `in` accepts a list OR a comma-separated string
- `between` requires `value` and `value2`
- `sortField` nested with `.`: `"asset.name"` → `select(WO).join(Asset).order_by(Asset.name)`
- Null `sortField` → default `created_at DESC`
- `direction=="DSC"` (yes, three letters, matches Java)
- `pageSize` max 1000 clipped

### 4.3 Tests

`tests/utils/test_search.py` — one test per operator + one test per quirk above + three realistic WO/Asset/User search payloads lifted from `fixtures/contract/*search.json`.

### Phase 4 gate

```bash
uv run pytest tests/utils/test_search.py -v        # all green
```

Commit as `migrate: phase 4 — SearchCriteria utility`.

---

## Phase 5 — Route-group migration template (read before Phase 6)

Phase 6 ports 72 controllers' worth of endpoints. Every route group follows the same recipe. Here it is once.

### Recipe

For route group **G** (e.g. "WorkOrders"):

1. **Inventory file** `atlas-cmms/src/routes/G/_inventory.md`:
   - Open `.canvas/legacy/api/src/main/java/com/grash/controller/GController.java`
   - List every endpoint: method, path, request body shape, response shape, auth level, side effects (webhook / workflow / notification / sequence)
   - List every service called: `GService`, `GSubService`, …
   - Mark dependencies on other route groups (e.g. "WorkOrderController.create depends on CustomSequenceService, WebhookDispatchService")

2. **Schemas file** `src/schemas/G.py`:
   - Translate every `GShowDTO`, `GPostDTO`, `GPatchDTO` from `.canvas/legacy/.../dto/`
   - Use `_CamelModel` + `IdRef` from §4
   - Date fields use the serializers from `src/utils/dates.py`

3. **Service file** `src/services/G.py`:
   - One class `GService` with the same public methods as the Java service
   - Business logic translated 1:1 from Java (no "while I'm here" refactors)
   - DB access via `self.db` (ajnkit-core session), never raw SQL

4. **Router file** `src/routes/G/__init__.py`:
   - `router = APIRouter(prefix="/g", tags=["g"])`
   - One handler per Java endpoint
   - Each handler: `Depends(get_current_user)`, `Depends(require_permission(...))`, calls `GService(db).method(...)`, returns Pydantic model

5. **Unit tests** `tests/services/test_G_service.py`:
   - Mock the DB session, assert the service calls the right query / raises the right exception
   - Port the Java `GServiceTest` 1:1 where it exists

6. **Contract tests** `tests/routes/test_G_contract.py`:
   - For each endpoint in the group, call `contract.diff_against_java(...)` with the recorded fixture
   - Must pass for Phase 6 group gate

7. **Flip the Nginx route** (strangler fig — **local docker-compose only**, never deployed):

   Add to `nginx.conf` (route-group-local, done once per group):
   ```nginx
   location ~ ^/api/g(/|$)   { proxy_pass http://atlas_cmms:8080; }
   ```
   `atlas_cmms:8080` resolves to the Python container; unflipped routes fall through to Java in docker-compose. This Nginx config exists ONLY in `docker-compose.yml` to make the local port reversible per group — it is not part of the Canvas deploy. Canvas serves atlas-cmms directly; there is no Nginx in production.

8. **Smoke test in a browser:**
   - `docker compose up -d atlas-cmms`
   - Open http://localhost:3000, navigate to the screens that use group G
   - Create / edit / delete / search — zero red toasts, zero 4xx/5xx in network tab

### Prompting template for the small agent (copy per route group)

> **Phase 6.{N} — Port the `<GroupName>` route group.**
>
> **Preconditions check:**
> 1. `atlas-cmms/src/models/` has every model this group touches (verify by `grep`-ing the Java service's `@Autowired` repositories).
> 2. `fixtures/contract/*{group-prefix}*.json` has recorded fixtures for every endpoint (`ls fixtures/contract/ | grep -i <group>`).
> 3. `src/deps/`, `src/utils/`, `src/schemas/_base.py`, `src/utils/search.py` exist and tests pass.
> If any precondition fails, STOP and report.
>
> **Reading list (open with `Read` tool, in this order, do not skip):**
> - `.canvas/legacy/api/src/main/java/com/grash/controller/<GroupName>Controller.java`
> - `.canvas/legacy/api/src/main/java/com/grash/service/<GroupName>Service.java`
> - every DTO under `.canvas/legacy/api/src/main/java/com/grash/dto/<group>/`
> - the matching Java test file `.canvas/legacy/api/src/test/java/com/grash/<GroupName>ServiceTest.java` if it exists
>
> **Execute the §5 recipe steps 1–6.** For step 3 (service), translate control flow 1:1 — do not rewrite loops as comprehensions, do not merge methods, do not extract helpers. Preserve all Java method names (adapt `camelCase` → `snake_case`). Keep a comment `# java: <OriginalName>` on each ported method.
>
> **Specifically forbidden:**
> - Importing `psycopg`, `httpx`, `requests`, `jose`, `jwt`, `bcrypt`, `openai`
> - Writing to the DB without going through the `GService` + ajnkit-core session
> - Returning `JSONResponse(content={...})` instead of a Pydantic model (loses OpenAPI schema)
> - "Improving" the Java logic
>
> **Gate for this group (all four):**
> 1. `uv run pytest tests/services/test_<group>_service.py tests/routes/test_<group>_contract.py -v` — all green
> 2. `uv run ruff check src/routes/<group>/ src/services/<group>.py src/schemas/<group>.py` — no issues
> 3. `uv run mypy src/routes/<group>/ src/services/<group>.py src/schemas/<group>.py` — no errors
> 4. Browser smoke test: user runs the recipe step 8, confirms Y/N
>
> Report back with the four gate results pasted literally. Do not mark this group done until the user says Y on step 4.
>
> **Commit** as `migrate(phase6): port <group> route group`.

---

## Phase 6 — Port the 72 controllers in dependency order

### Priority order (ports first → ports last; later groups depend on earlier ones)

| # | Group | Notes |
|---|---|---|
| 6.1 | `health`, `instance-config`, `license`, `currencies` | Smoke tests the whole scaffold |
| 6.2 | `companies`, `users`, `roles`, `teams`, `user-settings` | Needed for the current-user dependency to fully work |
| 6.3 | `files`, `uploads` | Uses `ajnkit-media` — add the package: `canvas app add media` |
| 6.4 | `locations`, `vendors`, `customers`, `categories` (all 8) | Pure CRUD, warms up the pattern |
| 6.5 | `assets`, `asset-categories`, `floor-plans`, `deprecations` | 728-line service — biggest group so far |
| 6.6 | `parts`, `part-categories`, `part-quantities`, `part-transactions`, `multi-parts` | Inventory domain |
| 6.7 | `meters`, `meter-categories`, `readings` | PM depends on this |
| 6.8 | `tasks`, `checklists`, `task-base` | Needed by WO + PM |
| 6.9 | `custom-fields`, `field-configurations`, `work-order-configurations` | |
| 6.10 | `requests` | 533-line service, approve() creates a WO (depends on 6.11) — port approve() last |
| 6.11 | `work-orders` | 71 endpoints, 1327-line service — the biggest. Create() must call CustomSequenceService, WebhookDispatchService, WorkflowService, NotificationService — port those stubs first |
| 6.12 | `custom-sequences`, `webhooks`, `webhook-endpoints`, `workflows`, `workflow-actions`, `workflow-conditions`, `notifications`, `comments` | |
| 6.13 | `preventive-maintenance`, `schedules`, `work-order-meter-triggers` | WO creation job depends on 6.11 |
| 6.14 | `labors`, `additional-costs`, `time-categories`, `cost-categories` | WO children |
| 6.15 | `purchase-orders`, `purchase-order-categories` | |
| 6.16 | `analytics/*` (5 controllers) | Read-only aggregates, easier |
| 6.17 | `exports`, `imports` | CSV/Excel — may use `openpyxl` directly (not in ajnkit) |
| 6.18 | `request-portals`, `request-portal-fields` | Public endpoints (no auth) |
| 6.19 | `api-keys`, `reviews`, `relations`, `general-preferences`, `ui-configurations`, `company-settings`, `shift-configurations`, `workload`, `demo` | The long tail |
| 6.20 | `subscriptions`, `subscription-plans`, `subscription-change-requests` | **Return 503 or stub** per CLOUD_VERSION=false policy. Document the stub in `MIGRATION_NOTES.md`. |

### Per-group gate: see Phase 5 recipe step 8 + the prompting template.

### Phase 6 aggregate gate

```bash
cd atlas-cmms
uv run pytest -q                                   # all green
uv run ruff check src/                             # clean
uv run mypy src/                                   # clean
npx jscpd --compare .canvas/legacy/api/src/main/java/com/grash/ atlas-cmms/src/ \
  --ignore "**/target/**,**/.canvas/legacy/**,**/.venv/**" \
  --format java,python -r json -o .jscpd-compare --silent
# Read .jscpd-compare/jscpd-report.json → code.sides[0].percentage ≥ 90%
```

Commit per-group as above; also commit `migrate: phase 6 — all 72 route groups ported`.

---

## Phase 7 — Background jobs (APScheduler via ajnkit if available, else standalone)

### 7.1 Decision 🧑

**ASK USER:** "Canvas gives us a web process. Jobs are either (a) a second APScheduler process in the same container, started from `Procfile` as `worker: python -m src.jobs.runner`, or (b) a `/jobs/tick` endpoint hit by Canvas cron. Which does ajnkit-core prescribe? If unclear, open `atlas-cmms/.agents/skills/ajnkit-core/SKILL.md` and look. Then pick."

### 7.2 Port these jobs (one file per job under `src/jobs/`)

| Java | Python | Notes |
|---|---|---|
| `WorkOrderCreationJob` | `src/jobs/work_order_creation.py` | Polls `schedule` table every minute, creates WOs from due triggers |
| `PreventiveMaintenanceNotificationJob` | `src/jobs/pm_notification.py` | Daily at 06:00 UTC |
| `DeleteDemoCompaniesJob` | `src/jobs/delete_demo.py` | Daily |
| `LdapSyncJob`, `LdapSyncJobScheduler`, `SubscriptionEndJob` | **DO NOT PORT** | SSO replaces LDAP; CLOUD_VERSION=false drops subscription expiry |

### 7.3 Tests

Each job: `tests/jobs/test_<job>.py` — freeze time with `freezegun`, insert fixture rows that make the job fire, assert the DB change and the outbound side-effect call (notification, email).

### Phase 7 gate

```bash
uv run pytest tests/jobs/ -v
# plus: start the worker locally, let it tick once, grep logs for the job's heartbeat
```

Commit as `migrate: phase 7 — background jobs`.

---

## Phase 8 — PDF reports (Thymeleaf → Jinja2 + WeasyPrint, or ajnkit-pdf if it exists)

### 8.1 Check for a native option FIRST

Read `atlas-cmms/.agents/skills/` for any `ajnkit-pdf` or `ajnkit-reports` skill. If present, use it. If absent, use `jinja2` + `weasyprint`.

### 8.2 Prototype the hardest report BEFORE porting the other 19

- The hardest is the full WO report with cost tables, image gallery, signatures. File it as `src/pdf/work_order_report.py`.
- Render it from a fixture WO; open the PDF; compare visually to the Java-rendered equivalent (grab one from Phase 2 fixtures).
- Decision 🧑: if the Python PDF is >20% off (missing images, broken pagination, font substitution), ESCALATE — do not continue to the other 19 templates. We will reconsider PDF stack.

### 8.3 If prototype passes, port the other 19

One file per template under `src/pdf/`. Reuse layout CSS in `src/pdf/_base.css`. Email delivery: use `ajnkit-email` (`canvas app add email`), not SMTP.

### Phase 8 gate

```bash
uv run pytest tests/pdf/ -v
# plus: for each of the 20 reports, open the Python output + the Java output side-by-side, visual OK
```

Commit as `migrate: phase 8 — pdf reports`.

---

## Phase 9 — Frontend: strip JWT, serve from Python, wire Canvas SSO

### 9.1 Changes in `frontend/`

- [frontend/src/utils/api.ts](../../frontend/src/utils/api.ts): remove the `Authorization: Bearer` header, set `credentials: 'include'` on fetch calls.
- Remove `getAccessToken()` / `setAccessToken()` / `refreshToken()` call sites — grep for them.
- Replace the login screen with a redirect: if the API returns 401, `window.location = '/__canvas/signin'` (or whatever Canvas's SSO redirect URL is per `canvas-sdk`).
- Replace the logout handler: `window.location = '/__canvas/signout'`.
- Delete the Google/OAuth sign-in buttons from the login UI; the SSO flow is single-provider.
- Remove the password-reset and signup flows from the UI entirely (routes `/auth/reset`, `/auth/signup`, `/auth/activate-account`). If the user can't be invited by the app, Canvas sharing (`canvas share`) does it instead.

### 9.2 Build and serve from Python

- `cd frontend && npm run build` produces `frontend/build/`.
- Add a build step in `atlas-cmms/Procfile` prelaunch (or ajnkit equivalent) that copies `../frontend/build/` into `atlas-cmms/static/` on container build.
- In `src/http/app.py` mount `app.mount("/", StaticFiles(directory="static", html=True), name="static")` AFTER mounting the API routes.
- The React app and the API now share the same origin and the Canvas SSO cookie flows automatically.

### 9.3 Verify

- `docker compose up -d atlas-cmms` → open http://localhost:8081/ → Canvas SSO redirect simulated locally (ajnkit-core probably has a dev mode that fakes it — check the skill).
- Click through: login, dashboard, create WO, approve request, run report. Zero red toasts.

### Phase 9 gate

```bash
cd frontend && npm run lint && npm run build       # per AGENTS.md "Done" rules
cd atlas-cmms && uv run pytest tests/ -q           # still green
```

Commit as `migrate: phase 9 — frontend strips JWT, served from python, canvas sso`.

---

## Phase 10 — Data migration (one-shot, when ready to cutover)

### 10.1 Freeze writes on the Java API

- Set `MAINTENANCE_MODE=true` env var on the Java API (returns 503 on all writes). Confirms in logs.

### 10.2 Dump and import

```bash
docker compose exec postgres pg_dump --data-only --no-owner atlas > /tmp/atlas-data.sql
# follow ajnkit-core / canvas db import procedure to load into the Canvas-managed Postgres
canvas db import /tmp/atlas-data.sql
```

### 10.3 Row counts match

Write `scripts/compare_row_counts.py` that connects to both DBs and asserts every table has the same count. Fail loudly on any diff.

### 10.4 Point Nginx entirely at Python

- Edit `nginx.conf`: `location /api/ { proxy_pass http://atlas_cmms:8080; }`
- Stop the Java container: `docker compose stop api`
- Smoke test every screen in the browser one more time.

### Phase 10 gate

```bash
scripts/compare_row_counts.py                        # exits 0
# full browser walkthrough per AGENTS.md "Done" criteria for a UI change
```

Commit as `migrate: phase 10 — data imported, java api stopped locally`.

---

## Phase 11 — Deploy to Canvas

### 11.1 score.yaml review

```yaml
auth: sso                                    # Canvas Microsoft SSO
containers:
  app:
    variables:
      CLOUD_VERSION: "false"
      # others as needed
secrets:
  - name: SMTP_PASSWORD                      # if any secrets survive
# resources:
#   - type: postgres                         # declared by `canvas app add postgres`
#   - type: media                            # declared by `canvas app add media` (file uploads)
#   - type: email                            # declared by `canvas app add email`
```

### 11.2 Validate, deploy, verify

```bash
cd atlas-cmms
canvas validate                              # exit 0
canvas deploy                                # follow its prompts
# open https://atlas-cmms--<team>.<base>
# Canvas SSO sign-in happens
# full browser walkthrough — every screen
```

### 11.3 First-SSO-login provisioning

- Verify the policy chosen in §3.3 fires correctly for a user that doesn't yet have a `User` row.
- Verify `current_user.company_id` is populated.

### Phase 11 gate

- Canvas URL is live
- All screens work for 2 distinct SSO users in 2 distinct companies
- Browser DevTools: no 401, no 500 across the smoke test

Commit as `migrate: phase 11 — deployed to canvas`. Tag `canvas-launch-v1`.

---

## Phase 12 — Freeze mobile (do not delete; it will be revived later)

Per the user: mobile is wanted back in the future, so `mobile/` stays in the repo. But its current wiring — Bearer JWT against the Java API — will stop working the moment §13 removes `api/`. So we freeze it, document that it's frozen, and write down what rebuilding it against the Python Canvas API will require.

Steps:

1. **Do NOT delete `mobile/`.** Keep every file.
2. Create [mobile/FROZEN.md](../../mobile/FROZEN.md) with this content (replace `<DATE>` with the actual date Phase 12 runs):
   ```markdown
   # Mobile app is frozen as of <DATE>

   The Expo app in this folder was built against the Java Spring Boot API in `api/`
   using `Authorization: Bearer <jwt>`. As of <DATE> the backend has moved to a
   Python app deployed on Canvas (`atlas-cmms/`), and the Java tree in `api/` is
   scheduled to be removed in a separate commit (migration plan Phase 13).

   **What this means today:** the mobile app no longer has a backend to talk to
   and will fail to log in. Do not try to run it as-is.

   **To revive it**, pick one path:

   1. **Mobile SSO (recommended, matches web auth)** — rewire the app to use MSAL
      for native (`react-native-msal` or Microsoft's Expo guidance) to obtain
      Canvas SSO tokens, then pass them to the Canvas-hosted API. Canvas serves
      atlas-cmms at `https://atlas-cmms--<team>.<base>/`; the SSO cookie that
      MSAL hands you authenticates every request. Remove the entire
      `src/auth/jwt*` module and the `/auth/signin` call sites in the app.

   2. **API key path** — keep the current fetch layer, but swap Bearer JWT for an
      `X-API-Key: ak_...` header. API keys are created in the web UI
      (atlas-cmms `/api-keys`). Simpler to wire; worse UX (users copy-paste a
      key). No SSO flow in the mobile app.

   Either path is a separate project, not part of the Java → Python migration.
   Open a tracking issue when the rewire is scheduled.
   ```
3. Add a one-line banner to [mobile/README.md](../../mobile/README.md) at the very top:
   `> ⚠ **This app is frozen as of <DATE>** — see [FROZEN.md](FROZEN.md) before running anything.`
4. Edit [AGENTS.md](../../AGENTS.md):
   - Change the mobile row in the Commands table to: `| Mobile | **Frozen as of <DATE>** — see [mobile/FROZEN.md](mobile/FROZEN.md) | — |`
   - Change the Where-new-code-goes row similarly: `| Mobile | **Frozen** — do not add code to `mobile/` without first reviving it per `mobile/FROZEN.md` | — |`
5. Do **not** change the top-level [README.MD](../../README.MD) install docs for mobile — leave them as-is but add a one-line "⚠ mobile currently frozen, see mobile/FROZEN.md" line in the mobile section.
6. Commit as `migrate: phase 12 — freeze mobile pending canvas sso rewire`.

**The small agent must not** delete, rename, or rewrite any file inside `mobile/`. It only adds `FROZEN.md`, prepends the banner to `mobile/README.md`, and edits the two rows in `AGENTS.md`.

---

## Phase 13 — Delete the Java tree

Only after Phase 11 is green on the live Canvas URL and §10 data import has been verified.

1. Confirm `atlas-cmms` has been serving all traffic for ≥ 48 h with zero rollbacks.
2. `git rm -r api/`
3. Edit [docker-compose.yml](../../docker-compose.yml): remove the `api` service and the `nginx` strangler-fig routes.
4. Edit [AGENTS.md](../../AGENTS.md): collapse the Commands and Where-new-code-goes tables to the Python app only.
5. Update [README.MD](../../README.MD) install instructions to reference only `atlas-cmms/` + `frontend/`.
6. **Keep `.canvas/legacy/`** inside `atlas-cmms/` as the frozen Java reference for 90 days — then it is also deletable. Add a dated line to `atlas-cmms/MIGRATION_NOTES.md` saying when it can go.
7. Commit as `migrate: phase 13 — remove java tree; project is fully python`.

---

## Appendix A — Executor prompting style (keep responses tight)

Based on the Oct-2026 coding-agent prompting research (see §Sources):

- **Specs > prompts.** Each phase has a reading list + success criteria. The small agent should not have to design anything.
- **Scope and verify.** Each phase has one shell-command gate. If the gate exits non-zero, the agent loops inside the phase. It does not advance.
- **Context hygiene.** The small agent discards the Java source from working memory after each route group. Re-reads only the files for the next group.
- **Guardrails over cleverness.** The §1 contract forbids imports (`psycopg`, `jose`, etc.) that would route around ajnkit. The agent follows the list; it does not reason about exceptions.
- **Specify details.** Every "write a file" instruction names the exact path, the exact exports, and the exact tests.
- **Human gates are mandatory.** 🧑 steps block the agent until a human replies. The agent must not synthesize an answer.

## Appendix B — When something isn't in ajnkit

Fallback order:
1. Confirm by reading the ajnkit package source: `uv run python -c "import ajnkit; print(ajnkit.__path__)"` → open the folder, grep for the function you need.
2. If genuinely absent: write a thin wrapper in `src/utils/` that is clearly labeled `# ajnkit-gap-shim` + a one-line note in `MIGRATION_NOTES.md` under "ajnkit gaps".
3. If the gap keeps biting: file via `report-issue` skill.

Do **not** silently add a dependency on a non-ajnkit library without logging it in `MIGRATION_NOTES.md`.

## Appendix C — Rough effort estimate (small agent + user supervision)

| Phase | Agent time | User time |
|---|---|---|
| 0 | 1 h | 1 h (gates) |
| 1 | 1 d | 30 min |
| 2 | 1 d (parallel with 1) | 15 min |
| 3 | 1 d | 30 min (3.3 decision) |
| 4 | 4 h | 15 min |
| 5 | — (reading only) | — |
| 6 | 2–3 weeks (72 groups × 1–3 h/group + reruns) | 1 h per group for smoke tests ≈ 2 days total |
| 7 | 1 d | 30 min (7.1 decision) |
| 8 | 1 d prototype + 2 d rest | 1 h visual review |
| 9 | 1 d | 2 h browser walkthrough |
| 10 | 2 h | 1 h |
| 11 | 2 h | 1 h |
| 12 | 30 min | 10 min |
| 13 | 30 min (after 48 h soak) | 10 min |

**Realistic calendar:** 4–6 weeks end-to-end to a live Canvas deploy. Mobile is deleted in Phase 12 (half an hour); the Java tree is deleted in Phase 13 after a 48-hour soak on the live Canvas URL. End state: one Python app on Canvas, one React build served by it, zero Java.

## Sources (for Appendix A)

- [7 prompting strategies to sharpen your AI-assisted code — LeadDev](https://leaddev.com/software-quality/7-prompting-strategies-to-sharpen-your-ai-assisted-code)
- [Coding with AI Agents: Best Practices for 2026 — DEV](https://dev.to/stravukarl/coding-with-ai-agents-best-practices-for-2026-2h8o)
- [AI Prompt Engineering Best Practices for Developers in 2026 — Fungies.io](https://fungies.io/?p=37876)
- [How to Use AI Coding Agents Effectively — WillowVoice](https://willowvoice.com/blog/how-to-use-ai-coding-agents-effectively)
- [Prompt Engineering for AI Coding Assistants in 2026 — Neura.market](https://neura.market/directories/cursor/blog/devto-4163032)
