# API & Frontend DTO Contract Reference (`atlas-cmms/` ↔ `frontend/`)

This document defines the REST API and JSON DTO contracts between the FastAPI backend (`atlas-cmms/src/`) and the React/Redux frontend (`frontend/src/slices/`).

---

## 1. Router Architecture (`src/routes/`)

All API routes are mounted under `/api` (with `/auth/*` also mirrored at root `/auth/*` for compatibility) by [`src/app.py`](src/app.py).

| Router Module | Base Prefixes | Primary Frontend Slices (`frontend/src/slices/`) |
|---|---|---|
| [`_crud.py`](src/routes/_crud.py) | Shared factory (`build_crud_router`) | Provides standard `POST /search`, `GET ""`, `POST ""`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` with automatic tenant scoping (`company_id` or `company_settings_id`) and primitive defaults. |
| [`auth_users.py`](src/routes/auth_users.py) | `/auth`, `/users`, `/roles`, `/teams`, `/company-settings`, `/companies`, `/general-preferences`, `/currencies`, `/notifications`, `/subscription`, `/subscription-plans`, `/license`, `/switch-account` | `user.ts`, `role.ts`, `team.ts`, `companySettings.ts`, `generalPreferences.ts`, `currency.ts`, `notification.ts`, `subscription.ts`, `subscriptionPlan.ts` |
| [`assets_locations.py`](src/routes/assets_locations.py) | `/locations`, `/floor-plans`, `/assets`, `/asset-downtimes`, `/deprecations`, `/customers`, `/vendors`, `/custom-fields`, `/custom-field-values`, `/*-category` (7 category routers) | `location.ts`, `floorPlan.ts`, `asset.ts`, `assetDowntime.ts`, `customer.ts`, `vendor.ts`, `category.ts` |
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

- `Location`: `workers`, `teams`, `vendors`, `customers`, `files`
- `Asset`: `workers`, `teams`, `vendors`, `customers`, `files`, `parts`
- `WorkOrder`: `assignedTo`, `customers`, `files`
- `PreventiveMaintenance`: `assignedTo`, `customers`, `files`
- `Schedule`: `daysOfWeek`
- `Checklist`: `taskBases`
- `TaskBase`: `options` (`[{"id": o.id, "label": o.label}]`)
- `Task`: `images`
- `Meter`: `users`, `customFieldValues`
- `Part`: `assignedTo`, `customers`, `vendors`, `teams`, `files`, `assets`, `multiParts`
- `MultiParts`: `parts`
- `Team`: `users`
- `Comment`: `files`

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
- [`_serialize_pm`](src/routes/work_orders_pm.py) always returns a non-null `schedule` object with `daysOfWeek: list[int]` and `nextWorkOrderDate` so `PMDetails.tsx` never encounters `null.dueDateDelay` or `null.disabled`.

### 3.3 Checklists, TaskBases & TaskOptions Contract

- Creating or patching a `Checklist` (`POST /api/checklists`, `PATCH /api/checklists/{id}`) persists its `taskBases` and `options` via [`_sync_checklist_task_bases`](src/routes/parts_po_tasks.py).
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
- Supports nested/joined sort and filter paths (e.g. `schedule.startsOn`, `location.id`, `asset.id`, `category.id`).
- Automatically enforces `SearchFieldPolicy` (blocking sensitive attributes like `password`, `secret`, `token`, `code`).
- Returns a Spring Data `Page<T>` JSON envelope (`content`, `totalElements`, `totalPages`, `size`, `number`, `first`, `last`, `numberOfElements`, `empty`, `pageable`, `sort`).

---

## 4. End-to-End Contract Verification (`tests/test_crud_contracts.py`)

Before deploying any backend or serializer change, run:

```bash
cd atlas-cmms
.venv/bin/pytest -q && .venv/bin/ruff check .
```

Key test suites:
- [`tests/test_crud_contracts.py`](tests/test_crud_contracts.py) — End-to-end verification of `/api/auth/me`, Location create + `/children/0/paginated`, Asset create + `/children/0/paginated` + `/mini?locationId=` + FK hydration, WorkOrder create + FK hydration, PreventiveMaintenance create + `Schedule` hydration + `schedule.startsOn` sort, Checklist create with `taskBases`/`options`, and Meter create + FK hydration.
- [`tests/routes/test_all_routes_and_jobs.py`](tests/routes/test_all_routes_and_jobs.py) — Route and background scheduler job coverage (`pm_generator`, `preventive_maintenance_notifier`, `downtime_notifier`, `cleanup`).
- [`tests/contract/test_openapi_covers_catalog.py`](tests/contract/test_openapi_covers_catalog.py) — OpenAPI route catalog parity check.
- [`tests/test_schema_matches_dump.py`](tests/test_schema_matches_dump.py) — SQLAlchemy 2.0 metadata vs PostgreSQL schema verification.
