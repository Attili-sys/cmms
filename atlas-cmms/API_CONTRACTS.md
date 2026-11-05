# API & Frontend DTO Contract Reference (`atlas-cmms/` ↔ `frontend/`)

This document defines the REST API and JSON DTO contracts between the FastAPI backend (`atlas-cmms/src/`) and the React/Redux frontend (`frontend/src/slices/`).

---

## 1. Router Architecture (`src/routes/`)

All API routes are mounted under `/api` (with `/auth/*` also mirrored at root `/auth/*` for compatibility) by [`src/app.py`](src/app.py).

| Router Module | Base Prefixes | Primary Frontend Slices (`frontend/src/slices/`) |
|---|---|---|
| [`_crud.py`](src/routes/_crud.py) | Shared factory (`build_crud_router`) | Provides standard `POST /search`, `GET ""`, `POST ""`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` with automatic tenant scoping (`company_id` or `company_settings_id`) and primitive defaults. |
| [`auth_users.py`](src/routes/auth_users.py) | `/auth`, `/users`, `/roles`, `/teams`, `/company-settings`, `/companies`, `/general-preferences`, `/currencies`, `/notifications`, `/subscription`, `/subscription-plans`, `/license`, `/switch-account` | `user.ts`, `role.ts`, `team.ts`, `companySettings.ts`, `generalPreferences.ts`, `currency.ts`, `notification.ts`, `subscription.ts`, `subscriptionPlan.ts` |
| [`assets_locations.py`](src/routes/assets_locations.py) | `/locations`, `/floor-plans`, `/assets`, `/asset-downtimes`, `/deprecations`, `/customers`, `/vendors`, `/custom-fields`, `/custom-field-values`, `/*-categories` (7 category routers) | `location.ts`, `floorPlan.ts`, `asset.ts`, `assetDowntime.ts`, `customer.ts`, `vendor.ts`, `category.ts` |
| [`parts_po_tasks.py`](src/routes/parts_po_tasks.py) | `/parts`, `/multi-parts`, `/part-quantities`, `/purchase-orders`, `/additional-costs`, `/tasks`, `/checklists` | `part.ts`, `multipart.ts`, `partQuantity.ts`, `purchaseOrder.ts`, `additionalCost.ts`, `task.ts`, `checklist.ts` |
| [`work_orders_pm.py`](src/routes/work_orders_pm.py) | `/work-orders`, `/work-order-histories`, `/labors`, `/relations`, `/comments`, `/work-order-meter-triggers`, `/preventive-maintenances`, `/schedules`, `/workload` | `workOrder.ts`, `workOrderHistory.ts`, `labor.ts`, `relation.ts`, `comment.ts`, `workOrderMeterTrigger.ts`, `preventiveMaintenance.ts`, `workload.ts` |
| [`meters_requests_workflows_misc.py`](src/routes/meters_requests_workflows_misc.py) | `/meters`, `/readings`, `/requests`, `/workflows`, `/files`, `/import`, `/export`, `/webhooks`, `/work-order-configuration`, `/work-order-request-configuration`, `/ui-configuration` | `meter.ts`, `reading.ts`, `request.ts`, `workflow.ts`, `file.ts`, `imports.ts`, `exports.ts`, `workOrderConfiguration.ts`, `workOrderRequestConfiguration.ts`, `uiConfiguration.ts` |
| [`analytics.py`](src/routes/analytics.py) | `/analytics/work-orders`, `/analytics/assets`, `/analytics/parts`, `/analytics/requests`, `/analytics/users` | `analytics/workOrder.ts`, `analytics/asset.ts`, `analytics/part.ts`, `analytics/request.ts`, `analytics/user.ts` |

---

## 2. Serializer & Foreign-Key Mini-DTO Hydration (`src/services/serializer.py`)

### 2.1 Why Foreign-Key Hydration is Required

In the legacy Spring Boot backend, Jackson serialized `@ManyToOne` relationships as nested mini-DTO objects (`LocationMiniDTO`, `AssetMiniDTO`, `UserMiniDTO`, `CategoryDTO`, `FileMiniDTO`, etc.). React components across `frontend/src/content/own/` read nested properties directly:
- `row.location.name`, `row.location.address`
- `row.asset.name`, `row.asset.customId`, `row.asset.status`
- `row.primaryUser.firstName`, `row.primaryUser.lastName`
- `row.category.name`
- `row.image.url`

If a backend serializer returns a bare `{"id": 5}` stub for a foreign key, the React table or details drawer either renders blank labels or throws a runtime `TypeError`.

### 2.2 Automatic FK Hydration (`_hydrate_foreign_key`)

[`model_to_dict(obj, db=db)`](src/services/serializer.py) inspects every `*_id` foreign key column on any SQLAlchemy model and calls [`_hydrate_foreign_key(target_table, raw_val, db)`](src/services/serializer.py) when a database `Session` is passed:

| Target SQL Table | Hydrated JSON Shape |
|---|---|
| `location` | `{"id", "name", "address", "customId", "longitude", "latitude"}` |
| `asset` | `{"id", "name", "description", "customId", "status", "barCode", "area", "locationId"}` |
| `own_user` | `{"id", "firstName", "lastName", "email", "phone", "jobTitle", "rate", "enabled"}` |
| `team` | `{"id", "name", "description"}` |
| `vendor` | `{"id", "name", "companyName", "email", "phone", "vendorType", "rate"}` |
| `customer` | `{"id", "name", "email", "phone", "customerType", "rate"}` |
| `file` | `{"id", "name", "url"}` |
| `part` | `{"id", "name", "cost", "quantity", "minQuantity", "nonStock", "barcode", "unit", "area"}` |
| `meter` | `{"id", "name", "unit", "updateFrequency"}` |
| `role` | Full `serialize_role(role, db)` including `createPermissions`, `viewPermissions`, `viewOtherPermissions`, `editOtherPermissions`, `deleteOtherPermissions` |
| `currency` | `{"id", "name", "code"}` |
| `work_order` | `{"id", "title", "customId", "status", "priority"}` |
| `*_category` (all 7 tables) | `{"id", "name", "description"}` |

### 2.3 Guaranteed Collection Arrays (`_MODEL_DEFAULT_LISTS`)

React components call `.map()`, `.filter()`, and `.length` on collection fields without null checks. [`_MODEL_DEFAULT_LISTS`](src/services/serializer.py) guarantees that every serialized entity includes empty lists `[]` by default (populated by custom serializers where applicable):

- `Location`: `workers`, `teams`, `vendors`, `customers`, `files`, `customFieldValues`
- `Asset`: `workers`, `users`, `assignedTo`, `teams`, `vendors`, `customers`, `files`, `parts`, `customFieldValues`
- `WorkOrder`: `assignedTo`, `customers`, `files`, `customFieldValues`
- `PreventiveMaintenance`: `assignedTo`, `customers`, `files`, `customFieldValues`
- `Schedule`: `daysOfWeek`
- `Checklist`: `taskBases`
- `TaskBase`: `options` (`[{"id": o.id, "label": o.label}]`)
- `Task`: `images`
- `Meter`: `users`, `customFieldValues`
- `WorkOrderMeterTrigger`: `assignedTo`, `customers`, `files`
- `Request`: `files`, `customFieldValues`
- `Part`: `assignedTo`, `users`, `customers`, `vendors`, `teams`, `files`, `assets`, `multiParts`, `customFieldValues`
- `PurchaseOrder`: `customFieldValues`
- `Vendor`: `customFieldValues`
- `Customer`: `customFieldValues`
- `MultiParts`: `parts`
- `Team`: `users`
- `Comment`: `files`
- `Workflow`: `secondaryConditions`

---

## 3. Critical Domain Contracts

### 3.1 Locations & Assets Hierarchy Pagination

The Locations (`/app/locations`) and Assets (`/app/assets`) screens use tree-table pagination rather than flat `POST /search` when browsing the hierarchy:
- **Locations:**
  - `GET /api/locations/children/{parent_id}/paginated?pageNum=0&pageSize=10&sortField=createdAt&direction=DESC`
  - When `parent_id == 0`, returns root locations (`Location.parent_location_id.is_(None)`).
  - Each serialized location includes `hasChildren: bool` and `hierarchy: list[int]`.
  - In [`frontend/src/slices/location.ts`](../frontend/src/slices/location.ts), `addLocation` and `editLocation` update both `state.locations` and `state.locationsHierarchy`.
- **Assets:**
  - `GET /api/assets/children/{parent_id}/paginated?pageNum=0&pageSize=10&sortField=createdAt&direction=DESC`
  - When `parent_id == 0`, returns root assets (`Asset.parent_asset_id.is_(None)`).
  - Each serialized asset includes `hasChildren: bool` and `hierarchy: list[int]`.
  - `GET /api/assets/mini?locationId=` accepts empty string `""` cleanly without raising a 422 integer validation error.
  - In [`frontend/src/slices/asset.ts`](../frontend/src/slices/asset.ts), `addAsset`, `editAsset`, and `deleteAsset` update both `state.assets` and `state.assetsHierarchy`.

### 3.2 Preventive Maintenance & Schedule Contract

- Creating a `PreventiveMaintenance` (`POST /api/preventive-maintenances`) automatically creates and links its `Schedule` row (`pm.schedule_id = sched.id`) in [`_after_create_pm`](src/routes/work_orders_pm.py).
- `Schedule.recurrence_type` (`"DAILY"`, `"WEEKLY"`, `"MONTHLY"`, `"YEARLY"`) and `Schedule.recurrence_based_on` (`"SCHEDULED_DATE"`, `"COMPLETED_DATE"`) are stored as strings.
- [`_serialize_pm`](src/routes/work_orders_pm.py) always returns a non-null `schedule` object with `startsOn`, `nextDueDate`, `daysOfWeek: list[int]`, and `nextWorkOrderDate` so `PMDetails.tsx` never encounters `null.dueDateDelay` or `null.disabled`.
- Background PM generation (`src/jobs/pm_generator.py`) copies PM template tasks onto generated WorkOrders, honors `schedule_days_of_week`, and for `COMPLETED_DATE` recurrence holds `starts_on` until the open generated WorkOrder transitions to `COMPLETE`.

### 3.3 Checklists, TaskBases & TaskOptions Contract

- Creating or patching a `Checklist` (`POST /api/checklists`, `PATCH /api/checklists/{id}`) clones `TaskBase` and `TaskOption` templates via [`_sync_checklist_task_bases`](src/routes/parts_po_tasks.py) so live WorkOrder tasks are never hijacked.
- Patching tasks on a WorkOrder (`PATCH /api/tasks/work-order/{id}`) or PreventiveMaintenance (`PATCH /api/tasks/preventive-maintenance/{id}`) reconciles existing `Task`, `TaskBase`, and `TaskOption` rows in place by ID without duplicating rows.
- [`_serialize_task_base`](src/routes/parts_po_tasks.py) serializes `TaskOption` rows as `[{"id": o.id, "label": o.label}]` to match `TaskOption` in `frontend/src/models/owns/tasks.ts`.

### 3.4 Search & Specification Engine (`src/utils/search.py`)

All `POST /api/<entity>/search` endpoints accept a `SearchCriteria` payload:
```json
{
  "pageNum": 0,
  "pageSize": 10,
  "sortField": "createdAt",
  "direction": "DESC",
  "filterFields": [
    {
      "field": "priority",
      "operation": "in",
      "values": ["HIGH", "MEDIUM"],
      "enumName": "PRIORITY",
      "alternatives": []
    }
  ]
}
```
- Supports nested/joined sort and filter paths (e.g. `schedule.startsOn`, `location.id`, `asset.id`, `category.id`, `customFieldValues.value`, virtual `Request.status` (`PENDING`, `CANCELLED`, `APPROVED`), and M2M association filters like `assignedTo`, `teams`, `vendors`, `customers`, `parts`).
- Deduplicates joined M2M / 1:N queries using a mandatory `model_cls.id.in_(filter_stmt)` subquery so `ORDER BY` on joined columns works on PostgreSQL without `SELECT DISTINCT` conflicts.
- Automatically enforces `SearchFieldPolicy` (blocking sensitive attributes like `password`, `secret`, `token`, `code`) and `apply_view_other_scope()` so limited users without `viewOtherPermissions` only see records they created or are assigned to.
- Returns a Spring Data `Page<T>` JSON envelope (`content`, `totalElements`, `totalPages`, `size`, `number`, `first`, `last`, `numberOfElements`, `empty`, `pageable`, `sort`).

### 3.5 Asset & Location M2M Relations, Custom Fields & Status-to-Downtime Lifecycle

- **M2M & Custom Field Synchronization (`_sync_asset_relations`, `_sync_location_relations`):**
  - Creating (`POST /api/assets`) or patching (`PATCH /api/assets/{id}`) an asset synchronizes `assignedTo` / `workers` (`t_asset_user_associations`), `teams` (`t_asset_team_associations`), `vendors` (`t_asset_vendor_associations`), `customers` (`t_asset_customer_associations`), `parts` (`t_asset_part_associations`), `files` (`t_asset_file_associations`), and `customFieldValues` (`custom_field_value`) within a single database transaction before returning the hydrated DTO.
- **Status-to-Downtime Lifecycle (`trigger_asset_downtime`, `stop_asset_downtime`):**
  - Transitioning an `Asset` to `DOWN` (`PATCH /api/assets/{id}`) or setting a `WorkOrder` to an non-complete status when `WorkOrderConfiguration.WorkOrderField.status` is `REQUIRED` opens an `AssetDowntime` (`duration=0`) on the asset and cascades `DOWN` + running `AssetDowntime` rows up its ancestor chain (guarding against duplicate running downtimes).
  - Transitioning an `Asset` back to `OPERATIONAL` (or completing its `WorkOrder`) closes all running `AssetDowntime` rows (`duration=0`) with elapsed seconds and cascades `OPERATIONAL` down to all descendant assets.
  - Creating or editing an `AssetDowntime` (`POST /api/asset-downtimes`, `PATCH /api/asset-downtimes/{id}`) validates against overlapping closed intervals (`406 Not Acceptable`).

### 3.6 Asset & Fleet Analytics Contracts (`src/routes/analytics.py`)

- `POST /api/analytics/assets/{asset_id}/overview` returns a JSON object `{"mtbf": float, "mttr": float, "downtime": int, "uptime": int, "totalCost": float}` matching `AssetOverviewStats` in `frontend/src/slices/analytics/asset.ts`.
- `POST /api/analytics/assets/costs/overview` returns `{"totalWOCost", "avgWOCost", "totalAcquisitionCost", "rav"}` matching `AssetCostOverviewStats`.
- Fleet reliability endpoints (`/downtimes`, `/mtbf`, `/mttr`, `/meantimes`, `/repair-times`, `/downtimes/costs`, `/downtimes/costs/date`, `/downtimes/meantime/date`, `/time-cost`, `/overview`) compute live values from `Asset`, `AssetDowntime`, `WorkOrder`, `Labor` (using merged interval duration), `AdditionalCost`, and `PartQuantity`.

### 3.7 File Upload/Download & Import/Export Contracts (`src/routes/meters_requests_workflows_misc.py`)

- `POST /api/files` persists uploaded bytes under `DATA_DIR/uploads/{company_id}/{file_id}_{safe_name}` and returns serialized `File` DTOs containing `id`, `name`, `url` (`/api/files/download/{id}`), and `thumbnailUrl`.
- `POST /api/import/assets` executes a two-pass import (Pass 1: core columns, Pass 2: hierarchy `parentAssetName` and M2M associations by name/email) matching `AssetImportDTO` keys (`id`, `name`, `archived`, `description`, `locationName`, `parentAssetName`, `area`, `barCode`, `category`, `model`, `power`, `manufacturer`, `serialNumber`, `primaryUserEmail`, `warrantyExpirationDate`, `additionalInfos`, `inServiceDate`, `assignedToEmails`, `teamsNames`, `status`, `acquisitionCost`, `customersNames`, `vendorsNames`, `partsNames`).
- `GET /api/import/download-template?language=EN&importEntity=ASSET` and `GET /api/export/{entity}` stream CSV files directly over HTTP.

### 3.8 Tenant Security, FK Ownership & RBAC Enforcement (`src/routes/_crud.py`, `src/deps/permissions.py`)

- `apply_patch()` blocks top-level and nested-dict overrides of `id`, `company_id`, `company_settings_id`, `created_at`, `created_by`, `updated_at`, `updated_by`, and `is_demo`, and supports `{"location": null}` to clear nullable foreign keys (`location_id = None`).
- `validate_foreign_key_ownership()` verifies that every referenced foreign key belongs to the caller's `company_id` or `company_settings_id` (skipping global tables `currency`, `company_settings`, `subscription`, `subscription_plan`).
- `build_crud_router` maps all 28 operational, auxiliary, and catalog models in `_ENTITY_PERMISSION_MAP` to their exact `PermissionEntity` (`can_create`, `can_view` / `apply_view_other_scope`, `can_edit_object`, `can_delete_object`) and scopes auxiliary tables without a direct `company_id` column (`Schedule`, `Reading`, `PartQuantity`, `AdditionalCost`, `CustomFieldValue`) via parent entity joins.

### 3.9 Workflows, WorkOrders, Parts, POs & Non-Asset Analytics Contracts

- **Workflows Engine (`src/services/workflow_engine.py`, `src/routes/meters_requests_workflows_misc.py`):**
  - Creating (`POST /api/workflows`) or patching (`PATCH /api/workflows/{id}`) a workflow persists both `action` and `secondaryConditions` and hydrates nested foreign-key mini-DTOs (`asset`, `location`, `team`, `user`, `part`, `vendor`, `checklist`, `workOrderCategory`, `purchaseOrderCategory`).
  - Automatically evaluates and executes enabled workflows on WorkOrder, Request, PurchaseOrder, Part, and Task events.
- **WorkOrder Configuration & Lifecycle (`src/routes/work_orders_pm.py`):**
  - `PATCH /work-orders/{id}/change-status` rejects `COMPLETE` with `406` when any configured completion guard is unsatisfied: required signature, required files, incomplete tasks, no logged labor time, unused assigned parts, or zero total cost.
  - `POST /work-orders/events` accepts a blank `companyId` query (the calendar sends `companyId=` when no company is selected) and returns `{type, date, endDate, event}` for work orders in the visible range plus future preventive-maintenance occurrences. An empty `companyId` means the caller's company.
  - `POST /work-orders/{id}/send-report` validates view permission and same-company customer recipients, then sends a plain-text summary through Canvas email. Canvas email does not provide PDF attachments; a refused recipient is returned as `{success: false, message}`.
  - Enforces author-only edit/delete on `Comment`, logs comment history, and normalizes `Relation` directional pairs (`BLOCKED_BY` $\to$ `BLOCKS`, `DUPLICATED_BY` $\to$ `DUPLICATE_OF`, `SPLIT_TO` $\to$ `SPLIT_FROM`) while rejecting self-relations and duplicates (`406`).
- **User Mini DTOs (`src/routes/auth_users.py`):**
  - `GET /users/mini` excludes disabled, `VIEW_ONLY`, and `REQUESTER` users by default; `withRequesters=true` includes enabled requesters/view-only users where the assignment UI explicitly supports them.
- **Parts & Purchase Orders (`src/routes/parts_po_tasks.py`):**
  - Enforces tenant-unique part barcodes (`406` on duplicate), positive restock quantities (`POST`/`PATCH /api/parts/{id}/restock`), and automatic warehouse inventory adjustments + `PartTransaction` consumption logs across `PartQuantity` and `PurchaseOrder` approval/rejection transitions.

---

## 4. End-to-End Contract Verification (`tests/`)

Before deploying any backend or serializer change, run:

```bash
cd atlas-cmms
.venv/bin/pytest -q && .venv/bin/ruff check .
```

Key test suites (**85 tests total**, `uv run pytest -q` on 2026-11-04):
- [`tests/test_crud_contracts.py`](tests/test_crud_contracts.py) — End-to-end verification of `/api/auth/me`, Location create + `/children/0/paginated`, Asset create + `/children/0/paginated` + `/mini?locationId=` + FK hydration, WorkOrder create + FK hydration, PreventiveMaintenance create + `Schedule` hydration + `schedule.startsOn` sort, Checklist create with `taskBases`/`options`, and Meter create + FK hydration.
- [`tests/test_asset_management_fixes.py`](tests/test_asset_management_fixes.py) — Comprehensive verification of all 22 Asset Management defects (M2M/custom-field sync, status-to-downtime cascades, analytics formulas, search deduplication, two-pass import/export, file upload/download, tenant/FK isolation, RBAC ownership, hierarchy cycle detection, and duplicate identifier checks).
- [`tests/test_non_asset_modules_fixes.py`](tests/test_non_asset_modules_fixes.py) and [`tests/test_non_asset_audit_fixes.py`](tests/test_non_asset_audit_fixes.py) — Comprehensive regression suites covering all non-asset backend, security, RBAC, `viewOther` scoping, cross-tenant FK injection, WorkOrder configuration/completion guards, PM `COMPLETED_DATE` recurrence, Part barcode/restock, Workflow patching/execution, Meter triggers, Request virtual status search, in-app notifications, Import/Export, and Analytics contracts.
- [`tests/routes/test_all_routes_and_jobs.py`](tests/routes/test_all_routes_and_jobs.py) — Route and background scheduler job coverage (`pm_generator`, `preventive_maintenance_notifier`, `downtime_notifier`, `cleanup`).
- [`tests/contract/test_openapi_covers_catalog.py`](tests/contract/test_openapi_covers_catalog.py) — OpenAPI route catalog parity check.
- [`tests/test_schema_matches_dump.py`](tests/test_schema_matches_dump.py) — SQLAlchemy 2.0 metadata vs PostgreSQL schema verification.
