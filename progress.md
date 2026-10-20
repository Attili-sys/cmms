# AJ CAFM — Engineering Progress Summary

**Live Canvas App:** `https://aj-cafm--innovation.canvas.ajnai.net` (`aj-cafm`, team `innovation`)
**Latest Deployment:** `@e0b1b7285ffc` (`Synced · Healthy`, build `#8`)
**Verification Status:**
- **Backend (`atlas-cmms/`)**: `76 passed` in `.venv/bin/pytest -q` (including `tests/test_non_asset_modules_fixes.py`, `tests/test_asset_management_fixes.py`, `tests/test_crud_contracts.py`) & `0` errors in `.venv/bin/ruff check .`
- **Frontend (`frontend/`)**: `0` errors in `npm run lint` & `npm run build` synced to `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/`
- **Currency Default & UI Adornments**: Default currency set to **`QR` (`Qatari Riyal`, `id=3`)** across backend and frontend with `(QR)` labels and `QR` input adornments on all cost/rate fields.
- **Live Browser Verification**: **All 7 E2E Asset Management Flows + 4 Delta Checks PASS** on `https://aj-cafm--innovation.canvas.ajnai.net`
- **Canvas Platform**: `canvas validate` & `canvas deploy` passing (`480` files, `7.8 MB` package, `/data` persistent volume mounted)

---

## 1. Completed & Deployed: Asset Management Fixes (`AM-PLAN-01`)

All **22 tracked defects and Java-parity gaps** (9 P0, 10 P1, 3 core contracts `C-01`–`C-03`) from [`assets-management-plans/01_ASSET_MANAGEMENT_FIXES_PLAN.md`](assets-management-plans/01_ASSET_MANAGEMENT_FIXES_PLAN.md) are implemented, tested, and deployed:

| Category | Issues Fixed | Summary of Changes |
|---|---|---|
| **Security & Tenant Isolation** | `P0-01`, `P0-07`, `P0-08`, `P1-11`, `P1-12` | Blocked cross-tenant `company_id` / `company_settings_id` mutation in `apply_patch()`; wired Java-parity RBAC (`can_view`, `can_create`, `can_edit`, `can_delete` with creator + assigned-user ownership) across CRUD routers; scoped public portal, category mini, floor plan, and meter reading endpoints by tenant; added cross-tenant FK validation and parent-hierarchy cycle detection (`400`). |
| **Asset Identity & DB Uniqueness** | `P0-06` | Normalized blank `customId`, `barCode`, `nfcId` to `NULL`; cleared unique identifiers on Asset Clone; added startup deduplication + PostgreSQL partial unique indexes (`uq_asset_company_custom_id`, `uq_asset_company_bar_code`, `uq_asset_company_nfc_id`) in `src/tasks.py` and Alembic migration `0002`. |
| **M2M & Custom Fields (`C-01`)** | `C-01`, `P0-04` | Single-transaction `flush()` + M2M sync + `commit()` in `_crud.py`; full hydration and persistence for all 6 asset M2M tables (`users`, `parts`, `teams`, `vendors`, `customers`, `files`) and `customFieldValues`; fixed `GET /api/assets/part/{id}` (`t_asset_part_associations`). |
| **Search, Hierarchy & Import/Export** | `P0-03`, `P0-05`, `P1-09` | Fixed `POST /api/assets/search` for `customFieldValues.value` and M2M filters using PostgreSQL-safe `Asset.id.in_(subquery)`; added SQL `ORDER BY` + pagination to `GET /api/assets/children/{id}/paginated`; replaced broken STOMP `/api/ws` dependency in Import/Export with direct HTTP responses + two-pass topological parent-first Asset CSV import. |
| **Status $\leftrightarrow$ Downtime (`C-03`) & Meters** | `C-03`, `P1-07`, `P1-08`, `P1-10`, `P1-15` | Full Java `AssetService` downtime parity (`DOWN` & `EMERGENCY_SHUTDOWN` cascade up to ancestors on start, cascade down to children on stop, WorkOrder status hooks, overlap rejection); fixed Downtime Edit modal (`editAssetDowntime`), recursive Redux `deleteAsset`, and Meter `lastReading`/`nextReading` hydration. |
| **Asset & Fleet Analytics (`C-02`)** | `C-02`, `P1-13`, `P1-14` | Replaced empty/hardcoded fallbacks with Java-accurate MTBF (days), MTTR (hours), Availability (%), Downtime hours, and TCO (`totalAcquisitionCost`, `totalWOCosts`, `rav`) across per-asset and fleet analytics endpoints. |

---

## 2. Completed & Deployed: Live Browser Verification Fixes (`@73ff68d10881` $\rightarrow$ `@f299132d9968`)

All issues surfaced during the live Browser Verification runs on `https://aj-cafm--innovation.canvas.ajnai.net` have been resolved, verified end-to-end in the browser, and deployed:

| Browser Flow | Issue Reported on Live App | Fix Deployed & Verified |
|---|---|---|
| **Flow 1 & 7 (File Upload & Image Display)** | `POST /api/files/upload` returned `500` (unwritable container path) and caused unhandled JS rejection; non-creator tenant users got `403` on image download. | Mounted persistent `/data` volume (`DATA_DIR: /data`) in `atlas-cmms/score.yaml` with writable fallback in `_get_upload_root()`; accepted `files`/`file`/`multipartFiles`; allowed same-tenant image downloads; hardened `getErrorMessage` in `frontend/src/utils/api.ts`. (**PASS**) |
| **Flow 1 (Form Fields & Clone with NFC ID)** | Add/Edit/Copy modals lacked `customId` and `nfcId`; `location` required on Edit/Copy; cloning an asset with `nfcId` returned `409 Conflict` (`nfc: {id: ...}` leaked from `model_to_dict` and mapped back to `nfc_id` in `apply_patch`); `customers` field labeled **Contractors** had raw placeholder string. | Added `customId` and `nfcId` to Add/Edit/Copy forms; stopped `model_to_dict()` from hydrating non-FK `nfc_id` as `nfc: {id: ...}` and stopped `apply_patch()` from mapping `nfc` dict to `nfc_id`; cleared `customId`, `barCode`, `nfcId`, and `nfc` in Copy form (`Assets/Show/index.tsx` & `formatters.ts`); fixed `t('customers_description')` placeholder on **Contractors** (`customers`) field. (**PASS**) |
| **Flow 2 (Hierarchy/Table Toggle)** | No visible button to switch between Hierarchy and Table views on `/app/assets`. | Added explicit **Hierarchy** and **Table** toggle buttons in the `/app/assets` toolbar. (**PASS**) |
| **Flow 3 (Import CSV & Column Auto-Matcher)** | `POST /api/import/assets` returned `500` (`"OPERATIONAL"` passed to `SMALLINT`); auto-matcher mapped CSV `name` to `ID` (`distance("name", "ID") = 4 < 5`) and left `parentAssetName` unmatched. | Fixed `_parse_asset_status_import()` to return integer enum ordinals (`0..6`); replaced greedy single-pass `distance < 5` matcher in `Imports/index.tsx` with a 2-pass exact normalized (`keyName` / `label`) + conservative fuzzy matcher. (**PASS**) |
| **Flow 4 (Running Downtime & Null Status)** | Active downtime (`duration: 0`) hidden by `.filter(d => d.duration)`; older assets with `status=NULL` showed blank status selector. | Removed `.filter(d => d.duration)` in `AssetDowntimes.tsx` and displayed `Ongoing` when `duration === 0`; defaulted `None` status to `"OPERATIONAL"` in `_serialize_asset()`. (**PASS**) |
| **Flow 6 (Fleet Analytics Overview `500`)** | `POST /api/analytics/assets/overview` returned `500` (`TypeError: can't compare offset-naive and offset-aware datetimes` on `max(dt.starts_on, start)`). | Wrapped naive PostgreSQL `TIMESTAMP WITHOUT TIME ZONE` columns (`dt.starts_on`, `w.completed_on`, `w.due_date`, `w.created_at`) in `ensure_utc(...)` across `src/routes/analytics.py`. (**PASS**) |
| **SPA Navigation & Bundle Resilience** | Navigating directly or with a pre-`no-cache` cached `index.html` could request superseded JS/CSS bundle hashes. | Synced `frontend/build/static/*` directly into `atlas-cmms/src/static/`; added valid `runtime-env.js`; added `Cache-Control: no-cache, no-store, must-revalidate` on `index.html` and `runtime-env.js`; added `ResilientStaticFiles` in `src/views.py` (falls back to current `main.*` / `<chunk>.*` when a stale hash is requested) + one-shot client bundle error reload guard in `index.html`. (**PASS**) |

---

## 3. Completed & Deployed: Non-Asset Modules Audit Fixes (All 24 Regressions Resolved)

All **24 tracked `P0`/`P1` defects** across all 6 non-asset domains from [`NON_ASSET_MODULES_AUDIT_REPORT.md`](NON_ASSET_MODULES_AUDIT_REPORT.md) are implemented and covered by [`atlas-cmms/tests/test_non_asset_modules_fixes.py`](atlas-cmms/tests/test_non_asset_modules_fixes.py):

| Domain | Issues Fixed | Summary of Changes |
|---|---|---|
| **Work Orders, Labor, Tasks & Parts Usage** | `WO-P0-01`..`04`, `WO-P1-01`..`02` | Fixed Labor timer contract (`POST /labors/work-order/{id}?start=true\|false` and `/controlling-time-timer`) with exact Java/React `TimeStatus` ordinals (`STOPPED = 0`, `RUNNING = 1`), elapsed duration accumulation (`now - started_at`), `first_time_to_react`, and auto-stop on WO completion/status change; fixed `PATCH /part-quantities/work-order/{id}` to accept React `int[]` (`editWOPartQuantities`) preserving existing quantities and adding new parts with `quantity=1.0`, plus direct `PATCH`/`DELETE /part-quantities/{id}` stock adjustments & restocking; enforced `can_edit_object`, `requiredSignature`, and `completedOn`/`completedBy` clearing on `PATCH /work-orders/{id}/change-status` and `AdditionalCost` CRUD; reconciled Tasks in-place (preserving `Task.id` and `task_options`); hydrated/synced WO M2M (`assignedTo`, `customers`, `files`, `customFieldValues`) and `GET /work-orders/part/{id}`. |
| **Preventive Maintenance & Schedules** | `PM-P0-01`..`03`, `PM-P1-01` | Scoped auxiliary `Schedule`, `Reading`, `AdditionalCost`, `WorkOrderHistory`, and `PartQuantity` endpoints on `GET` list, `POST /search`, and `PATCH /schedules/{id}/reschedule` by parent entity tenant & `can_edit_object`; hydrated and synced PM M2M (`assignedTo`, `customers`, `files`, `customFieldValues`) and `Schedule.daysOfWeek` (`schedule_days_of_week`); unified `POST /preventive-maintenances/{id}/trigger-work-order` and `pm_generator.py` via `create_work_order_from_pm()` and `advance_schedule_next_due_date()` (`DAILY`/`WEEKLY`/`MONTHLY`/`YEARLY` + `COMPLETED_DATE` gating); implemented `/workload/overview`, `/workload/unscheduled`, `/workload/work-orders/{id}/schedule`, and `POST /preventive-maintenances/workload`. |
| **Parts, Inventory, POs, Vendors & Customers** | `PO-P0-01`..`03`, `PO-P1-02` | Hydrated `partQuantities` and `customFieldValues` on Purchase Orders; incremented `Part.quantity` + logged `PartTransaction` on PO approval (`respond?approved=true`), and reversed stock + set `ApprovalStatus.REJECTED` when an approved PO is rejected (`respond?approved=false`); enforced `Part` tenant validation on `MultiParts`; hydrated and synced `Part` M2M (`assignedTo`/`users`, `teams`, `vendors`, `customers`, `files`, `customFieldValues`, `openWorkOrders`) and `Vendor`/`Customer` `customFieldValues`. |
| **Meters, Service Requests & Workflows** | `REQ-P0-01`..`03`, `REQ-P1-01`, `MTR-P0-01` | Implemented full Java-parity **Workflows Execution Engine** (`src/services/workflow_engine.py`) firing automated conditions & actions on `WORK_ORDER_CREATED`/`CLOSED`/`ARCHIVED`, `REQUEST_CREATED`/`APPROVED`/`REJECTED`, `PURCHASE_ORDER_CREATED`/`UPDATED`, `PART_UPDATED`, and `TASK_UPDATED`; fixed public `POST /requests/portal/{portalUuid}` (`get_optional_current_user` + `portal.company_id` attribution); wired `approve_request` and `cancel_request` to copy M2M (`assignedTo`, `customers`, `files`, `audio_description_id`) and accept `reason` from query or JSON body; added `POST /readings` trigger evaluation against `WorkOrderMeterTrigger` to auto-create Work Orders. |
| **Analytics & Reporting** | `AN-P0-01`..`04` | Aligned all Work Order, Part, Request, and User analytics return shapes and field names with frontend Redux slices (`complete`, `compliant`, `countsByCategory`, `hours`, `averageHours`, `totalConsumptionCost`, `consumptions`, `priorityCounts`, `twoWeeksWorkOrders`). |
| **Auth, Users, Roles & Tenant Isolation** | `AUTH-P0-01`..`04`, `AUTH-P1-01` | Fixed `is_super_admin()` in `src/deps/company.py` so tenant `ADMIN` roles (`company_id is not None`) cannot bypass `assert_company_access()`; enforced tenant checks on `/companies/{id}`, `/company-settings/{id}`, `/general-preferences/{id}`, `/field-configurations/{id}`, `/ui-configurations`, `/user-settings/{id}`; provisioned dedicated `UserSettings` per user on `POST /users`; scoped `/roles` to the caller's tenant, set `code=6` (`USER_CREATED`), and protected system default roles (`403`). |

---

## 4. Next Steps Roadmap

1. **Asset Management Fixes (`AM-PLAN-01`) — COMPLETE**: All 22 backend/frontend fixes and all 7 live browser verification flows are signed off and deployed (`@f299132d9968`).
2. **Non-Asset Module Parity Fixes — COMPLETE & DEPLOYED (`@e0b1b7285ffc`)**: All 20+ non-asset module fixes are implemented, verified by `75 passed` backend tests + `ruff check`, and live on Canvas.
3. **Net-New Enterprise Asset Features (Phase 2+)**:
   - Asset Movement & Custody History ledger (`Stage 3` of [`ASSET_MANAGEMENT_SPEC.md`](ASSET_MANAGEMENT_SPEC.md))
   - Authenticated QR Label Print Sheet, Warranty Countdown Banner, and Quick-Action Speed Dial (`Stage 4`)
   - Asset Criticality (`A/B/C`) & Condition/Health Score (`0–100`) matrix (`Stage 6`)
   - Straight-Line / Declining-Balance Depreciation Engine & Repair-vs-Replace threshold banner (`Stage 7`)
