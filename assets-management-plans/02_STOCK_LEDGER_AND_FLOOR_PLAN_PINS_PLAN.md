# 02 — Stock Ledger & Floor-Plan Asset Pins (P0 client-parity gaps)

**Status:** Approved for execution · **Owner:** Opus (lead) + Sonnet subagents · **Deploy:** once, at the end, to `aj-cafm` on Canvas

**Why.** The client's vibe-coded CAFM audit (Nov 2026) showed our asset/inventory core already covers
more than his — except two things his users rely on every day:

1. **A stock movement ledger**: every quantity change is a row with type, signed change, running
   balance, who, WO/PO, and a reason. His Take-out / Receive / Count-the-shelf flow.
2. **Floor-plan asset pins**: drawings per location (with kind + revisions, PDF accepted), assets
   pinned on the plan, colour-coded by status.

Everything in this plan is grounded in the current code (file:line references are as of `955ea8d3`).

---

## 0. Ground truth — what exists today

### Stock
| Fact | Where |
|---|---|
| `part.quantity` (Float) is the only balance. No locking anywhere (`with_for_update` is never used). | `atlas-cmms/src/models/parts_po.py:36` |
| `part_transaction` exists (aliased `PartConsumption`): `quantity` (magnitude), `part_id`, `work_order_id`, `description`, audit columns. **No type, no balance, no reason, no PO link.** | `parts_po.py:61-73` |
| Writes that DO log: restock (`PART_RESTOCK`), WO consumption (`PART_CONSUMPTION`), PO approve (`PART_RECEPTION`), workflow APPROVE action. | `routes/parts_po_tasks.py:300-334`, `:378`, `:836-851`; `services/workflow_engine.py:340-360` |
| Writes that **silently** change stock (no row): WO part removed/reduced (`_consume_or_restore_part_stock`, `delta<0`), PO un-approve reversal, part form PATCH of `quantity`, CSV import, initial quantity on create. | `parts_po_tasks.py:384-386`, `:853-859`, CRUD `/parts`, `/import/{entity}` |
| Consumption analytics filters by `description` and **never nets returns** → overstated when a WO part line is reduced/removed. | `routes/analytics.py:1039-1057` |
| UI: `RestockPartModal` only; no history anywhere. | `frontend/src/content/own/Inventory/` |

### Floor plans
| Fact | Where |
|---|---|
| `floor_plan`: `id, name, area (NOT NULL), image_id, location_id`. **No audit columns, no company_id, no kind/revision, no pins.** | `models/location_asset.py:133-140` |
| Generic CRUD `/floor-plans` + `GET /floor-plans/location/{id}`. Tenant scoping is via the CRUD auxiliary predicate (no `company_id`). | `routes/assets_locations.py:577-602`, `routes/_crud.py:193` |
| UI: a name list with delete; image upload only; **no viewer**. | `frontend/src/content/own/Locations/LocationDetails.tsx:114-165, 355-400` |
| Uploads: `/files/upload`, 25 MB cap, stored under `DATA_DIR/uploads/<company>`. | `routes/meters_requests_workflows_misc.py:897-950` |

### Platform constraints that shape the design
- **Canvas refuses** a drop, rename, type change or **new constraint on an existing table** (`atlas-cmms/AGENTS.md` §7). ⇒ On existing tables we only add **nullable columns with no FK / unique / check**. New tables may carry FKs and unique constraints.
- Migrations are hand-written SQL in `atlas-cmms/db/migrations/NNN_*.sql` (pattern of `001`–`004`), mirrored in `db/schema.json`, and the test gate `tests/test_schema_matches_dump.py` compares models with `fixtures/schema_dump.json`. All three move together.
- `tests/contract/test_openapi_covers_catalog.py` reads `fixtures/contract/endpoints.yaml` — new endpoints get catalog entries.
- Sync SQLAlchemy ⇒ every new route is `def`, never `async def` (Ruff `ASYNC`).
- `model_to_dict(obj, db=db)` always (FK mini-DTO hydration).
- **No database backup on Canvas.** Migrations must be additive and idempotent (`IF NOT EXISTS`, guarded `UPDATE`/`INSERT`), so the previous build still runs against the new schema (rollback = redeploy previous commit).

---

## 1. Design

### 1A. Stock ledger

**One write path.** New `atlas-cmms/src/services/stock.py`:

```python
class MovementType(StrEnum):   # in src/models/enums.py
    OPENING = "OPENING"            # ledger baseline / initial quantity on create / import
    RECEIPT = "RECEIPT"            # manual receive (old "restock")
    PO_RECEIPT = "PO_RECEIPT"      # PO approved
    PO_REVERSAL = "PO_REVERSAL"    # PO un-approved after receipt
    ISSUE = "ISSUE"                # manual take-out (WO optional, reason required without WO)
    WO_CONSUMPTION = "WO_CONSUMPTION"
    WO_RETURN = "WO_RETURN"        # WO part line reduced / removed
    COUNT_GAIN = "COUNT_GAIN"      # shelf count above book
    COUNT_LOSS = "COUNT_LOSS"      # shelf count below book
    ADJUSTMENT = "ADJUSTMENT"      # quantity changed through the part form / API PATCH

INBOUND = {OPENING, RECEIPT, PO_RECEIPT, WO_RETURN, COUNT_GAIN}   # + ADJUSTMENT when positive

def record_movement(db, part_id, movement_type, quantity, *, user_id, company_id,
                    work_order_id=None, purchase_order_id=None, reason=None,
                    unit_cost=None, allow_negative=False) -> PartTransaction
def count_stock(db, part_id, counted, *, user_id, company_id, reason) -> PartTransaction | None
```

Rules enforced inside `record_movement` (not in routes):
- Locks the part row: `db.get(Part, part_id, with_for_update=True)` (no-op on SQLite tests, real on Postgres).
- `quantity > 0` always (magnitude). Direction comes from the type; `ADJUSTMENT` stores the sign in `change`.
- Outbound may not take stock below 0 → `CustomException(406, "Insufficient stock for part <name>")` (keeps today's message so the UI toast is unchanged). `PO_REVERSAL` passes `allow_negative=True` (stock already left the shelf; the ledger must still record the truth) and returns a warning flag.
- `non_stock` parts: the balance is not touched; the row is still written with `balance_after = NULL` (consumption analytics keeps working).
- Writes `PartTransaction` with `movement_type`, `quantity`, `change` (signed), `balance_after`, `reason`, `purchase_order_id`, `unit_cost` (defaults to `part.cost`), and keeps writing `description` with the legacy value (`PART_CONSUMPTION`, `PART_RESTOCK`, `PART_RECEPTION`) so anything still reading `description` keeps working.
- Calls `run_part_workflows(part, db)` once. Does **not** commit — the caller owns the transaction.

**Every existing stock write is rerouted through it** (this is where the silent gaps close):

| Call site | Becomes |
|---|---|
| `restock_part` `parts_po_tasks.py:300` | `RECEIPT` (route kept as a backward-compatible alias of `/stock/receive`) |
| `_consume_or_restore_part_stock` `:361` (delta>0 / delta<0) | `WO_CONSUMPTION` / `WO_RETURN` — the return is **now logged** |
| Bulk WO part endpoints `:520-590`, `:620-695` | already go through the helper — verify, no duplicate logic |
| PO approve `:836` and workflow APPROVE `workflow_engine.py:340` | `PO_RECEIPT` with `purchase_order_id` |
| PO un-approve `:853` | `PO_REVERSAL` — **now logged** |
| Part create with `quantity > 0` (CRUD `after_create`) | `OPENING`, reason "Initial quantity" |
| Part PATCH changing `quantity` (CRUD `before_patch`) | `ADJUSTMENT`, reason from payload `stockReason` or "Edited on part form" |
| CSV import of parts (`/import/parts`) | `OPENING` (new part) / `ADJUSTMENT` (existing part, quantity changed), reason "CSV import" |

**Analytics fix** (`analytics.py:1039`): consumption = `WO_CONSUMPTION` − `WO_RETURN` per part/WO,
with legacy fallback (`movement_type IS NULL AND (description IN (NULL,'PART_CONSUMPTION','CONSUMPTION') OR work_order_id IS NOT NULL)`).

**Schema** — `db/migrations/005_stock_ledger.sql` (additive only):
```sql
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS movement_type VARCHAR(32);
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS change DOUBLE PRECISION;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS balance_after DOUBLE PRECISION;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS purchase_order_id BIGINT;   -- no FK (Canvas rule); validated in service
ALTER TABLE part_transaction ADD COLUMN IF NOT EXISTS unit_cost DOUBLE PRECISION;
CREATE INDEX IF NOT EXISTS ix_part_transaction_part_created ON part_transaction (part_id, created_at DESC);
-- backfill legacy rows
UPDATE part_transaction SET movement_type = CASE description
    WHEN 'PART_RESTOCK' THEN 'RECEIPT' WHEN 'PART_RECEPTION' THEN 'PO_RECEIPT' ELSE 'WO_CONSUMPTION' END,
    change = CASE description WHEN 'PART_RESTOCK' THEN quantity WHEN 'PART_RECEPTION' THEN quantity ELSE -quantity END
  WHERE movement_type IS NULL;
-- one OPENING baseline per stocked part so every ledger has an anchor that equals today's balance
INSERT INTO part_transaction (id, created_at, updated_at, quantity, change, balance_after, movement_type,
                              reason, description, company_id, part_id)
SELECT nextval('part_transaction_seq'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ABS(p.quantity), p.quantity,
       p.quantity, 'OPENING', 'Ledger start', 'LEDGER_START', p.company_id, p.id
FROM part p
WHERE p.non_stock = FALSE
  AND NOT EXISTS (SELECT 1 FROM part_transaction t WHERE t.part_id = p.id AND t.description = 'LEDGER_START');
```
> If `canvas validate` objects to the index (it is not a constraint, so it should not), drop that line —
> the ledger page is paginated per part and works without it at our volumes.

**API** (Pydantic in/out, camelCase like the rest of `API_CONTRACTS.md`, all `def`, all under the parts router):

| Method & path | Body | Permission | Result |
|---|---|---|---|
| `POST /api/parts/{id}/stock/receive` | `{quantity>0, reason?, unitCost?≥0, purchaseOrderId?}` | edit `PARTS_AND_MULTIPARTS` | updated part DTO |
| `POST /api/parts/{id}/stock/issue` | `{quantity>0, workOrderId?, reason?}` — `reason` required when no WO; WO must be same company and viewable | edit `PARTS_AND_MULTIPARTS` | updated part DTO |
| `POST /api/parts/{id}/stock/count` | `{counted≥0, reason?}` — `reason` required when variance ≠ 0; variance 0 writes nothing | edit `PARTS_AND_MULTIPARTS` | updated part DTO + `variance` |
| `GET /api/parts/{id}/stock/movements?page=0&size=20` | — | view `PARTS_AND_MULTIPARTS` | `{content:[{id, createdAt, movementType, change, balanceAfter, reason, unitCost, createdBy:{id,firstName,lastName}, workOrder:{id,title,customId}?, purchaseOrder:{id,name}?}], totalElements, page, size}` newest first |
| `POST/PATCH /api/parts/{id}/restock` | unchanged | unchanged | alias → receive |

Non-stock parts: receive/issue/count return `406 "Stock actions are not available for non-stock parts"`.

### 1B. Floor-plan pins

**Schema** — `db/migrations/006_floor_plan_pins.sql`:
```sql
-- existing table: nullable, no constraints
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS kind VARCHAR(32);          -- ARCHITECTURAL | MEP | FIRE_SAFETY | SECURITY | OTHER
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS revision VARCHAR(32);
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS source_file_id BIGINT;     -- original PDF; no FK (Canvas rule)
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS superseded_by_id BIGINT;   -- next revision; NULL = current
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE floor_plan ADD COLUMN IF NOT EXISTS created_by BIGINT;
-- new table: constraints allowed
CREATE SEQUENCE IF NOT EXISTS floor_plan_pin_seq START WITH 1 INCREMENT BY 50;
CREATE TABLE IF NOT EXISTS floor_plan_pin (
  id BIGINT PRIMARY KEY DEFAULT nextval('floor_plan_pin_seq'),
  created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
  created_by BIGINT, updated_by BIGINT,
  company_id BIGINT NOT NULL REFERENCES company(id) ON DELETE CASCADE,
  floor_plan_id BIGINT NOT NULL REFERENCES floor_plan(id) ON DELETE CASCADE,
  asset_id BIGINT NOT NULL REFERENCES asset(id) ON DELETE CASCADE,
  x DOUBLE PRECISION NOT NULL, y DOUBLE PRECISION NOT NULL,      -- normalised 0..1 of image width/height
  CONSTRAINT uq_floor_plan_pin UNIQUE (floor_plan_id, asset_id)
);
CREATE INDEX IF NOT EXISTS ix_floor_plan_pin_asset ON floor_plan_pin (asset_id);
```
Model `FloorPlanPin` in `models/location_asset.py` (`CompanyAuditMixin` pattern used by other operational tables).

**Coordinates are normalised (0–1)** so pins survive any render size, zoom, or a same-ratio replacement image.

**PDF support — server side.** Add `pypdfium2` (self-contained wheels, no system packages; ABI-independent so it works on the platform's Python). New `services/floor_plan_render.py`:
`render_pdf_first_page(file) -> File` → PNG, longest edge 4000 px, saved through the same storage path as `/files/upload`, `type = IMAGE`. Rejects encrypted / >50-page / >25 MB / unreadable PDFs with `406` and a clear message. Images (`png, jpg, jpeg, webp, svg`) are used as-is. Anything else: `406`.

**Revisions.** Uploading with the same `(location_id, name, kind)` as a current plan → new row, old row's `superseded_by_id` = new id, **pins copied** to the new revision (same normalised coordinates; the user drags to correct if the drawing moved). Superseded plans stay readable (history), pins on them become read-only.

**Pin integrity rules (service-enforced):**
- Asset and plan in the same company.
- Asset's location must be the plan's location **or a descendant** (walk `parent_location_id`, cycle-safe, max depth 50).
- When an asset's `location_id` changes (asset PATCH hook in `assets_locations.py`), delete its pins that break the rule above.
- `0 ≤ x, y ≤ 1`.

**Also fix while here:** CRUD create/patch on `/floor-plans` must assert the caller can edit the target `location_id` (today the auxiliary predicate scopes reads; verify writes with a cross-tenant test and close it if open).

**API** (all `def`):

| Method & path | Body | Permission | Result |
|---|---|---|---|
| `GET /api/floor-plans/location/{id}?includeSuperseded=false` | — | view `LOCATIONS` | adds `kind, revision, note, image{id,url}, sourceFile{id,url,name}?, current, supersededById, pinCount, createdAt` |
| `POST /api/floor-plans` | `{name, area, locationId, kind?, revision?, note?, file:{id}}` — file is image or PDF | edit `LOCATIONS` on location | floor plan DTO (revision chain handled) |
| `GET /api/floor-plans/{id}/pins` | — | view `LOCATIONS` | `[{id, x, y, asset:{id, name, customId, status, image{url}?, openWorkOrders}}]` — `openWorkOrders` computed in **one** grouped query (no N+1) |
| `PUT /api/floor-plans/{id}/pins/{assetId}` | `{x, y}` upsert | edit `LOCATIONS` on plan's location; plan must be current | pin DTO |
| `DELETE /api/floor-plans/{id}/pins/{assetId}` | — | same | `{success:true}` |
| `GET /api/floor-plans/{id}/pinnable-assets?search=` | — | view `LOCATIONS` + `ASSETS` | assets in the location subtree not yet pinned, max 50 |
| `GET /api/assets/{id}/floor-plan-pins` | — | view `ASSETS` | `[{floorPlan:{id,name,kind,locationId}, x, y}]` current plans only |

---

## 2. Frontend

### 2A. Ledger (`frontend/src/content/own/Inventory/`)
- `PartDetails.tsx`: header buttons **Receive · Issue · Count** (shown with part edit permission, hidden for non-stock parts); new tab **Stock history** (MUI table: When · Movement (coloured chip) · Change (+/−) · Balance · By · WO/PO (links) · Reason), server-paginated, refreshes after every action.
- `StockActionModal.tsx` (new, one component with `mode: 'receive'|'issue'|'count'`) replaces `RestockPartModal.tsx` (delete it and its import sites). Issue: WO autocomplete (existing mini WO list) + reason, required when no WO. Count: shows book quantity, live variance, reason required when variance ≠ 0.
- Part edit form (`Parts.tsx` form fields): `quantity` **read-only on edit** with helper text "Use Receive, Issue or Count" (still editable on create).
- `slices/part.ts`: `receiveStock`, `issueStock`, `countStock`, `getStockMovements`; each action updates the part in the list + detail state so low-stock badges refresh. `models/owns/stockMovement.ts`.

### 2B. Floor-plan viewer (`frontend/src/content/own/Locations/`)
- `FloorPlanViewer.tsx` (new, no new npm dependency): image in a relative box; pins absolutely positioned by percentage; zoom (buttons + wheel, 0.5×–4×) and pan inside a scroll container; drag a pin to move (pointer events, saves on drop); **Place asset** mode: pick from `pinnable-assets` autocomplete, click the plan to drop; pin click → popover (name, custom ID, status chip, open WOs, "Open asset", "Remove pin"); legend; status colours: green OPERATIONAL, red DOWN/EMERGENCY_SHUTDOWN, amber INSPECTION_SCHEDULED/MODERNIZATION, blue STANDBY/COMMISSIONING. Read-only when the user lacks edit permission or the revision is superseded. Works on touch (pointer events).
- `LocationDetails.tsx` floor-plans tab: list shows kind, revision, pin count, "current"/"superseded"; click → viewer; add form gains kind (select), revision, note, and accepts **PDF or image** (`accept="image/*,application/pdf"`); "Show older revisions" toggle; "Download original" link when a PDF source exists.
- Asset detail (`content/own/Assets/Show/...`): "On floor plan" section listing current pins with a link that opens the location's floor-plan tab focused on the pin.
- `slices/floorPlan.ts` + `models/owns/floorPlan.ts`: new fields and pin thunks.

### 2C. Strings
New keys in `frontend/src/i18n/translations/en.ts` and `ar.ts` (Arabic properly translated); other locales get the English value so no key is ever missing. Keys unchanged across files (`translations/AGENTS.md`).

---

## 3. Tests (all must be green before deploy)

`atlas-cmms/tests/test_stock_ledger.py`
- receive / issue / count happy paths; `balance_after` equals `part.quantity` after each.
- issue without WO and without reason → 406; issue above stock → 406 with the legacy message; count variance 0 writes no row; count variance ≠ 0 without reason → 406.
- non-stock part → 406 on all three; WO consumption on non-stock still writes a row with `balance_after = NULL`.
- WO part line reduce / delete writes `WO_RETURN`; PO approve → `PO_RECEIPT` with `purchase_order_id`; PO un-approve → `PO_REVERSAL`.
- part form PATCH quantity → `ADJUSTMENT`; part create with quantity → `OPENING`; CSV import writes movements.
- **Ledger invariant:** after a randomised sequence of 50 mixed operations, for every part, latest `balance_after == part.quantity` and `Σ change == quantity − opening`.
- cross-tenant: user of company B gets 403/404 on every stock endpoint for a company A part; movements list never leaks.
- analytics: consumption nets returns.
- `/restock` alias still works (backward compatibility).

`atlas-cmms/tests/test_floor_plan_pins.py`
- create plan with PNG; with PDF (fixture: a 1-page PDF generated with `reportlab` in the test) → `image` is a PNG, `sourceFile` is the PDF; encrypted/garbage PDF → 406; `.exe` → 406.
- revision: same name+kind → old superseded, pins copied; pin write on superseded → 406.
- pin upsert/move/delete; out-of-range coordinates → 422/406; asset outside location subtree → 406; asset location change removes stale pins; asset delete cascades pins.
- pins endpoint returns `openWorkOrders` correctly; query count stays constant with 1 vs 30 pins.
- cross-tenant reads and writes → 403/404 (including the CRUD `/floor-plans` write path).

Fixture updates: `fixtures/schema_dump.json` (new columns + `floor_plan_pin`), `db/schema.json`, `fixtures/contract/endpoints.yaml` (new endpoints).

---

## 4. Execution — fast, parallel, one deploy

Rule for every agent: **do not run `canvas deploy`, do not commit, do not touch files outside your
list.** Each agent ends by running its own gate and reporting the exact output.

| Wave | Who | Work | Files (exclusive) | Gate |
|---|---|---|---|---|
| **0** | Lead (Opus) | Commit the pending invitation/welcome-email work already in the tree as its own commit (it ships in the same deploy). Branch `feat/stock-ledger-floor-plan-pins`. | — | `git status` clean |
| **1** | Lead (Opus) | Foundations shared by both features: `MovementType` enum, model columns, `FloorPlanPin` model, migrations `005` + `006`, `db/schema.json`, `fixtures/schema_dump.json`, `services/stock.py` (`record_movement`, `count_stock`), `pypdfium2` via `uv add` (lock committed). | `models/*`, `db/*`, `fixtures/schema_dump.json`, `services/stock.py`, `pyproject.toml`, `uv.lock` | `uv run pytest -q tests/test_schema_matches_dump.py` + `ruff` |
| **2a** | Opus subagent | Ledger backend: reroute all 8 call sites, 4 stock endpoints + alias, analytics netting, import hook, `tests/test_stock_ledger.py`. | `routes/parts_po_tasks.py`, `services/workflow_engine.py`, `routes/analytics.py`, the import section of `routes/meters_requests_workflows_misc.py`, `tests/test_stock_ledger.py` | `uv run pytest -q tests/test_stock_ledger.py` |
| **2b** | Sonnet subagent | Floor-plan backend: render service, revision logic, pin endpoints, asset-location hook, CRUD write-path tenant fix, `tests/test_floor_plan_pins.py`. | `routes/assets_locations.py`, `services/floor_plan_render.py`, `tests/test_floor_plan_pins.py` | `uv run pytest -q tests/test_floor_plan_pins.py` |
| **3a** | Sonnet subagent (starts when 2a reports green) | Ledger UI (§2A). Reports every i18n key it used, does **not** edit translation files. | `content/own/Inventory/*`, `slices/part.ts`, `models/owns/stockMovement.ts` | `npm run lint` |
| **3b** | Sonnet subagent (starts when 2b reports green) | Floor-plan UI (§2B). Same i18n rule. | `content/own/Locations/*`, `content/own/Assets/Show/*` (floor-plan section only), `slices/floorPlan.ts`, `models/owns/floorPlan.ts` | `npm run lint` |
| **4** | Sonnet subagent | Translations (§2C) from the key lists of 3a+3b; `fixtures/contract/endpoints.yaml`; docs: `atlas-cmms/DATABASE.md`, `atlas-cmms/API_CONTRACTS.md`, root + `atlas-cmms` test counts, `assets-management-plans/README.md`. | `i18n/translations/*`, `fixtures/contract/endpoints.yaml`, the docs listed | `npm run lint` |
| **5** | Lead (Opus) | Review every diff (not the agents' summaries). Full gates. `npm run build` → sync `build/*` to `atlas-cmms/src/static/` and `src/static/ui/` **preserving `src/static/ui/runtime-env.js`**. Local run against Postgres, browser-verify the acceptance script (§5) as Admin and as a Technician. | — | see §5 |
| **6** | Lead (Opus) | Deploy once (§6), smoke test on Canvas, commit. | — | §6 |

2a ∥ 2b and 3a ∥ 3b run concurrently; they share no files. Wave 1 is the only serial bottleneck and is deliberately small.

---

## 5. Definition of done (all re-run by the lead, outputs pasted in the final report)

1. `cd atlas-cmms && uv run pytest -q` — full suite green (86 existing + new).
2. `cd atlas-cmms && uv run ruff check .` — clean.
3. `cd frontend && npm run lint && npm run build` — clean; build synced to both static folders; `runtime-env.js` untouched (`git diff --stat atlas-cmms/src/static/ui/runtime-env.js` empty).
4. `cd atlas-cmms && canvas validate` — passes.
5. Browser acceptance script, locally:
   - Part with qty 10 → Issue 3 to a WO → Receive 5 (reason "DN-1234") → Count 11 (reason "cycle count") → history shows 4 rows with balances 7, 12, 11 (+ opening), quantity field read-only on edit.
   - Issue 50 → refused with toast; Issue without WO and reason → field error.
   - Remove the part line from the WO → `WO_RETURN` row appears, balance restored.
   - Approve a PO with that part → `PO_RECEIPT` row linked to the PO.
   - Location → upload a **PDF** plan (kind MEP, rev A) → viewer shows the rendered drawing → place 3 assets → drag one → reload, positions persist → colours match statuses → pin popover opens the asset.
   - Upload rev B (same name/kind) → rev A shows superseded and read-only, rev B has the 3 pins.
   - Move a pinned asset to another building → its pin disappears.
   - Asset detail → "On floor plan" link lands on the pin.
   - Technician role: sees history and plans, no Receive/Issue/Count/Place buttons unless their role grants edit.
   - Arabic UI: new screens render RTL with translated labels.

## 6. Deploy (once) and rollback

1. Pre-flight snapshot (Canvas has **no DB backup**): from the live app export Parts and Locations CSV (`/api/export/parts`, `/api/export/locations`) and save under `atlas-cmms/.canvas/snapshots/<date>/` (git-ignored).
2. `cd atlas-cmms && canvas validate && canvas deploy` (auto-deploy is on in `pyproject.toml`; we still run it explicitly once, at the end).
3. `canvas status` healthy; `canvas logs` shows migrations `005` and `006` applied and no startup errors.
4. Smoke on `https://aj-cafm--innovation.canvas.ajnai.net`: every existing stocked part has exactly one `OPENING` "Ledger start" row whose balance equals its quantity; run one Receive and one Count on a test part named `ZZ-DEPLOY-TEST`, then delete the part; open one location's floor-plan tab and place/remove one pin.
5. Commit on the branch with the migration files; open PR to `main`.

**Rollback:** migrations are additive, so the previous commit runs unchanged against the new schema →
`git checkout <previous> && canvas deploy`. New columns/table stay and are ignored. Never write a
down-migration that drops them (Canvas refuses drops, and it would destroy ledger history).

## 7. Out of scope (explicitly)
Multi-store/bins entity, stock transfers between stores, auto-reorder/PO generation, valuation reports,
part `max_level`/`part_no`/`size`/`condition` fields, condition/criticality on assets, location roll-up
page — these are the P1/P2 items from the gap review and get their own plan.

## 8. Risks & mitigations
| Risk | Mitigation |
|---|---|
| Canvas refuses part of a migration | Additive-only by construction; `canvas validate` in wave 5 before deploy; fallback is to drop the index lines only |
| `pypdfium2` wheel missing for the platform Python | Checked in wave 1 by `uv add` + `uv lock`; fallback: accept images only and show "Convert PDF to PNG" message — pins work either way |
| Concurrent stock edits corrupt balance | Row lock in `record_movement`; invariant test |
| Silent analytics change (returns now netted) | Called out in release note to the client: consumption figures become *more* accurate and may drop |
| Large drawings slow the viewer | Server renders at max 4000 px; images over 25 MB refused at upload |
| Legacy movements have no balance | `OPENING` baseline row per part anchors every ledger at deploy time; legacy rows show "—" for balance |
