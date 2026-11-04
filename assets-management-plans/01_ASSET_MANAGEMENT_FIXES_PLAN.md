# Asset Management Fixes Plan (Defects & Java Contract Parity Only — Rev 2)

- **Document ID**: `AM-PLAN-01` (Revision 2 — incorporates Second-Opinion Reviewer `REVISE` findings + full audit of remaining Asset tabs & Java controllers)
- **Parent Audit Spec**: [`ASSET_MANAGEMENT_SPEC.md`](../ASSET_MANAGEMENT_SPEC.md)
- **Scope**: **100% Fixes & Existing Feature Parity Only** — All **9 P0** security/crash defects, all **10 P1** correctness/UX/parity defects, and the **3 broken existing-feature contracts** (`C-01` M2M & Custom Fields, `C-02` Per-Asset Statistics Tab & Java Analytics Parity, `C-03` Full Java Status $\leftrightarrow$ Downtime & WorkOrder Parity).
- **Non-Goals (Excluded Net-New Features)**:
  - No new database tables for Asset Movement/Custody History, Criticality/Health Score, or Financial Depreciation.
  - No new UI tabs or widgets for Depreciation/RAV/Repair-vs-Replace (`C-04`), QR Print Sheet (`C-05`), Warranty Banner, or Quick-Action Speed Dial.

---

## 1. Complete Issue & Parity Inventory (22 Tracked Items)

| Issue ID | Severity | Source | Defect / Parity Gap Summary | Phase |
|---|---|---|---|---|
| `P0-07` | **P0** | Reviewer Rev 2 | **Any authenticated client can move any record to another tenant**: `apply_patch()` processes nested `{"company": {"id": X}}` before checking `ignore` against `fk_key`, and does not block `company_settings_id`, `updated_by`, or `updated_at`. Also `{"location": null}` / `{"parentAsset": null}` fails to clear nullable FKs. | **Phase 1** |
| `P0-08` | **P0** | Reviewer Rev 2 | **Zero role or entity permission enforcement on routes**: `can_view`, `can_create`, `can_edit`, `can_delete` in `src/deps/permissions.py` are wired to 0 routes (and `can_edit`/`can_delete` lack creator/assigned-user `own` ownership parity with Java `canBeEditedBy`). | **Phase 1** |
| `P0-01` | **P0** | Reviewer Rev 1+2 | **Cross-tenant disclosure in public mini routes, floor plans, and meter readings**: `GET /assets/public/mini/{portal_uuid}` and `GET /locations/public/mini/{portal_uuid}` ignore `RequestPortal.uuid` (and optional `?locationId=`); `GET /floor-plans/location/{id}` and `GET /readings/meter/{id}` lack tenant ownership checks. | **Phase 1** |
| `P1-12` | **P1** | Reviewer Rev 1 | **Category mini routes leak across tenants**: `_add_category_mini_route` only checks `company_id`, missing `company_settings_id` used by all 8 `*Category` tables. | **Phase 1** |
| `P1-11` | **P1** | Reviewer Rev 1+2 | **Cross-tenant FK injection & hierarchy cycles**: Generic CRUD `create`/`patch` does not validate that referenced FK IDs belong to the caller's tenant (`company_id` / `company_settings_id`) across `Asset`, `Location`, `AssetDowntime`, `Deprecation`, `FloorPlan`, `Meter`, `Reading`, `WorkOrder`; no cycle detection on `parent_asset_id` / `parent_location_id`. | **Phase 1** |
| `P0-06` | **P0** | Reviewer Rev 1+2 | **Asset identity collision & race condition**: Clone modal copies `customId`, `barCode`, `nfcId`; empty strings stored as `""` instead of `NULL`; no DB-level tenant-scoped partial unique indexes in Alembic. | **Phase 1** |
| `P0-02` | **P0** | Reviewer Rev 1+2 | **File upload crashes (`HTTP 500`) & lacks persistent/tenant-checked storage**: `upload_files` passes invalid kwargs (`url`, `file_type`, `is_demo`) to `File`; bytes must be stored under persistent `envs.DATA_DIR / "uploads"` (never `/tmp` or raw `os.environ`) and download route must enforce tenant ownership. | **Phase 2** |
| `C-01` | **P0** | Original + Rev 2 | **M2M collections & `customFieldValues` dropped on save and `[]` on read**: `create_item` in `_crud.py` commits twice instead of flushing + running hooks + committing once in a single transaction; 6 `t_asset_*_associations` tables and `CustomFieldValue` are never synced or hydrated. | **Phase 2** |
| `P0-04` | **P0** | Reviewer Rev 1 | **`GET /api/assets/part/{part_id}` crashes (`HTTP 500`)**: Imports non-existent `asset_parts` instead of `t_asset_part_associations` (`id_asset`, `id_part`). | **Phase 2** |
| `P0-03` | **P0** | Reviewer Rev 1+2 | **Asset text search (`customFieldValues.value`) & M2M filters crash (`HTTP 500`)**: `find_association_table` fails on plural relation names (`teams`, `customers`, `vendors`, `parts`); `customFieldValues.value` unmapped; `.distinct()` + joined `ORDER BY` fails on PostgreSQL unless filtered via `Asset.id.in_(subquery)`. | **Phase 3** |
| `P1-09` | **P1** | Reviewer Rev 1 | **Hierarchy children pagination (`GET /api/assets/children/{id}/paginated`) ignores `sort` and slices in Python memory**. | **Phase 3** |
| `P0-05` | **P0** | Reviewer Rev 1+2 | **Import/Export broken end-to-end**: `useImport.ts`/`useExport.ts` hang waiting for STOMP `/api/ws`; `Imports/index.tsx` defaults `entity` to `'imports'`; `/api/import/download-template` missing; asset CSV import lacks Java `ImportService` parity (topological parent-before-child ordering, get-or-create category, M2M name/email resolution, intra-batch barcode dedup, `A######` sequence). | **Phase 3** |
| `P1-07` | **P1** | Reviewer Rev 1 | **Downtime edit modal creates duplicate record**: `AssetDowntimes.tsx` calls `createAssetDowntime` instead of `editAssetDowntime`. | **Phase 4** |
| `P1-08` | **P1** | Reviewer Rev 1 | **Frontend Asset form & filter bugs**: `parts` select missing `multiple: true` in `Assets/index.tsx` and `Show/index.tsx`; `Filters.tsx` uses `customersMini` for `vendors` and lacks `?.value` on `archived`. | **Phase 4** |
| `C-03` | **P0** | Original + Rev 2 | **Status $\leftrightarrow$ Downtime & WorkOrder lifecycle does not match Java**: Missing `before_patch` hook; Java treats both `DOWN` (`1`) and `EMERGENCY_SHUTDOWN` (`6`) as down (`isReallyDown`), cascades `triggerDowntime` up to all `parentAsset` ancestors, cascades `stopDowntime` recursively down to all children, triggers/stops downtime on WorkOrder create (`assetStatus`) and last-WorkOrder completion, and rejects overlapping downtimes (`HTTP 406`). | **Phase 4** |
| `P1-10` | **P1** | Reviewer Rev 1+2 | **Hierarchy delete leaves orphaned descendants in Redux**: `AssetRow` has no `hierarchy` array; `deleteAsset` in `frontend/src/slices/asset.ts` must walk `parentAsset?.id` iteratively to remove all descendants. | **Phase 4** |
| `P1-15` | **P1** | Tab Audit (Meters) | **Asset Meters tab (`AssetMeters.tsx`) missing `lastReading`/`nextReading` hydration & trigger `custom_id`**: `_serialize_meter` does not compute `lastReading` and `nextReading` (`lastReading + updateFrequency days`) needed by `canAddReading(meter)`; reading-triggered WorkOrders lack `W######` `custom_id`. | **Phase 4** |
| `C-02` | **P0** | Original + Rev 2 | **Asset Statistics tab (`AssetAnalytics.tsx`) crashes & formulas diverge from Java**: `POST /api/analytics/assets/{id}/overview` hits fallback `[]`; formulas must match Java `AssetService` (`mtbf` in **days** between consecutive downtimes when $\ge 2$ downtimes else `0`, `mttr` from work order labor hours, `uptime` bounded by `max(start, asset.created_at)` and `min(end, now)`); `/assets/costs/overview` must return `totalAcquisitionCost`. | **Phase 5** |
| `P1-13` | **P1** | Reviewer Rev 1+2 | **Fleet `/api/analytics/assets/overview` returns hardcoded `95.0` availability and `0.0` MTBF** and missing sub-routes (`/mtbf`, `/mttr`, `/downtimes/meantime`, `/repair-times`, `/downtimes/costs`, `/downtimes/costs/date`, `/costs/date`). | **Phase 5** |
| `P1-14` | **P1** | Reviewer Rev 1 | **Documentation drift in `atlas-cmms/API_CONTRACTS.md` and `atlas-cmms/DATABASE.md`**. | **Phase 5** |

---

## 2. Detailed Technical Fixes by Phase

### Phase 1: Security Containment, RBAC Enforcement, Tenant Scoping & Identity Uniqueness (`P0-07`, `P0-08`, `P0-01`, `P1-12`, `P1-11`, `P0-06`)

#### 1.1 Harden `apply_patch()` Against Cross-Tenant Hijack & Nullable FK Clearing (`P0-07`)
- **File**: [`atlas-cmms/src/services/serializer.py`](../atlas-cmms/src/services/serializer.py#L361-L398)
- **Root Cause**:
  1. `ignore` is `{"id", "company_id", "created_at", "created_by"}` — missing `"company_settings_id"`, `"updated_at"`, and `"updated_by"`.
  2. When a payload contains `{"company": {"id": 999}}` or `{"companySettings": {"id": 777}}`, `snake_key` is `"company"` / `"company_settings"`, which is not in `ignore`. The nested-object branch (`if isinstance(val, dict) and "id" in val:`) constructs `fk_key = f"{snake_key}_id"` (`"company_id"` / `"company_settings_id"`) and calls `setattr(obj, fk_key, val["id"])` **without checking `fk_key in ignore`**!
  3. When a user clears a nullable relation in an edit form (`{"location": None}`, `{"parentAsset": None}`, `{"primaryUser": None}`, `{"category": None}`, `{"image": None}`), `val` is `None`. Because `snake_key` (`"location"`) is not a column name (`"location_id"` is), `apply_patch` silently skips it and never sets `location_id = None`.
  4. Empty strings (`""`) on optional identity fields (`bar_code`, `nfc_id`, `custom_id`) are stored as `""` instead of `None`, causing blank values to collide under unique indexes.
- **Fix Implementation**:
  ```python
  ignore = {
      "id",
      "company_id",
      "company_settings_id",
      "created_at",
      "created_by",
      "updated_at",
      "updated_by",
  } | (exclude or set())
  ```
  - Inside `for key, val in payload.items():`:
    - Check `fk_key = f"{snake_key}_id"`. If `snake_key in ignore or fk_key in ignore: continue`.
    - If `isinstance(val, dict) and "id" in val`: if `fk_key in valid_cols or hasattr(obj, fk_key)`, set `setattr(obj, fk_key, val["id"])` and `continue`.
    - If `val is None and snake_key not in valid_cols and (fk_key in valid_cols or hasattr(obj, fk_key))`: set `setattr(obj, fk_key, None)` and `continue`.
    - Normalize blank strings (`isinstance(val, str) and val.strip() == ""`) to `None` for nullable unique/identity columns (`custom_id`, `bar_code`, `nfc_id`).

#### 1.2 Wire Role & Entity Permission Checks into `build_crud_router` and Custom Routes (`P0-08`)
- **Files**:
  - [`atlas-cmms/src/deps/permissions.py`](../atlas-cmms/src/deps/permissions.py#L1-L162)
  - [`atlas-cmms/src/routes/_crud.py`](../atlas-cmms/src/routes/_crud.py#L46-L210)
  - [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py)
- **Root Cause**:
  1. `src/deps/permissions.py` defines `PermissionEntity` (`ASSETS`, `LOCATIONS`, `CATEGORIES`, `METERS`, `WORK_ORDERS`, `PARTS_AND_MULTIPARTS`, etc.) and `can_view`, `can_create`, `can_edit`, `can_delete`, but zero routes invoke them.
  2. In `src/deps/permissions.py:52-88`, `can_edit` and `can_delete` only check `role_edit_other_permissions` and `role_delete_other_permissions` when `own=False`.
  3. **Exact Java Ownership Rules (`Asset.java:244-256`, `Location.java:160-175`, `CategoryAbstract.java:80-88`)**:
     - **Edit (`canBeEditedBy`)**:
       - Allowed if role has `edit_other` permission for that `PermissionEntity`, **OR** `obj.created_by == user.id`, **OR** (for non-category entities that have user assignments) the user is assigned to the record (`t_asset_user_associations` for `Asset` — note that in Java `Asset.getUsers()` also includes `primaryUser` and `teams.users`, or specifically `t_asset_user_associations` / `is_assigned_to(obj, user, db)`). To match the Reviewer sign-off strictly: for `Asset`, edit is allowed if `role` has `edit_other`, or `obj.created_by == user.id`, or `user.id` is in `t_asset_user_associations` (`primary_user_id` alone does not grant edit/delete). For `*Category` (`CategoryAbstract.java:80-88`), only `edit_other` or `obj.created_by == user.id` applies. There is **no** extra "while holding view/create permission" condition on edit or delete.
     - **Delete (`canBeDeletedBy`)**:
       - Allowed **only** if role has `delete_other` permission for that `PermissionEntity`, **OR** `obj.created_by == user.id`. Being in `assignedTo` or `primaryUser` never grants delete permission.
- **Fix Implementation**:
  1. Update `can_edit` and `can_delete` in `src/deps/permissions.py` and add `check_entity_permission(user: User, entity: PermissionEntity | str, action: str, db: Session, obj: Any = None) -> None` that raises `HTTPException(status_code=403, detail="Access denied")` when unauthorized:
     - `action == "view"`: checks `can_view(user, entity, db)`.
     - `action == "create"`: checks `can_create(user, entity, db)`.
     - `action == "edit"`: checks `can_edit(user, entity, db, own=is_creator_or_assigned(obj, user, entity, db))` (where `is_creator_or_assigned` checks `obj.created_by == user.id`, plus `t_asset_user_associations` for `Asset` / `t_location_user_associations` for `Location` / `t_meter_user_associations` for `Meter`, and only `obj.created_by == user.id` for `CATEGORIES`).
     - `action == "delete"`: checks `can_delete(user, entity, db, own=(getattr(obj, "created_by", None) == user.id))`.
  2. Add `permission_entity: PermissionEntity | str | None = None` parameter to `build_crud_router` in `src/routes/_crud.py` and wire it across `Asset`, `AssetDowntime`, `Deprecation` (`PermissionEntity.ASSETS`), `Location`, `FloorPlan` (`PermissionEntity.LOCATIONS`), `*Category` (`PermissionEntity.CATEGORIES`), `Meter`, `Reading` (`PermissionEntity.METERS`), etc., plus custom hierarchy/children routes in `assets_locations.py`.

#### 1.3 Generic Cross-Tenant Foreign Key Ownership Check in `build_crud_router` (`P1-11`)
- **Files**:
  - [`atlas-cmms/src/routes/_crud.py`](../atlas-cmms/src/routes/_crud.py#L120-L195)
  - [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py)
- **Root Cause**:
  - `Asset`, `Location`, `AssetDowntime` (`asset_id`), `Deprecation` (`asset_id`), `FloorPlan` (`location_id`, `image_id`), `Meter` (`asset_id`, `location_id`, `image_id`), `Reading` (`meter_id`), and `WorkOrder` accept foreign-key IDs in `POST` and `PATCH` without verifying that the target row belongs to `current_user.company_id` (or `company_settings_id`).
- **Fix Implementation**:
  1. Add `validate_foreign_key_ownership(obj: Any, current_user: User, db: Session) -> None` in `src/routes/_crud.py` and call it in both `create_item` and `patch_item` right after `apply_patch`:
     - **Super-admin bypass**: If `is_super_admin(current_user, db)` (same rule as `assert_company_access`), allow through.
     - Inspect all `ForeignKey` columns on `obj.__class__` (skipping `"company_id"`, `"company_settings_id"`, `"created_by"`, `"updated_by"`).
     - For each non-null FK value on `obj`, resolve the target table from `Base.metadata.tables`:
       - **Global tables rule**: If the target table has **neither** `company_id` **nor** `company_settings_id` (e.g., `currency`, `company_settings`, `subscription`, `subscription_plan`), skip tenant ownership validation.
       - If the target table has `company_id`, verify a row with `id == fk_val` and `company_id == current_user.company_id` exists.
       - If the target table has `company_settings_id`, verify a row with `id == fk_val` and `company_settings_id == cs_id` exists.
       - Otherwise raise `HTTPException(status_code=400, detail=f"Invalid or cross-tenant reference on {col.name}")`.
  2. In `assets_locations.py`, add hierarchy cycle detection on `Asset` (`parent_asset_id`) and `Location` (`parent_location_id`): walk ancestor pointers (up to 50 hops); if `obj.id` is encountered in the ancestor chain, raise `HTTPException(status_code=400, detail="Circular hierarchy detected")`.

#### 1.4 Public Portal (`RequestPortal.uuid`), Category Mini, Floor Plans & Meter Readings Tenant Scoping (`P0-01`, `P1-12`)
- **Files**:
  - [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py#L37-L49) (and lines 103–113, 162–173, 253–272)
  - [`atlas-cmms/src/models/requests.py`](../atlas-cmms/src/models/requests.py#L52-L64) (`RequestPortal`)
  - [`atlas-cmms/src/routes/meters_requests_workflows_misc.py`](../atlas-cmms/src/routes/meters_requests_workflows_misc.py#L119-L130)
- **Fix Implementation**:
  1. **`GET /locations/public/mini/{portal_uuid}` & `GET /assets/public/mini/{portal_uuid}`**:
     - Look up `portal = db.scalars(select(RequestPortal).where(RequestPortal.uuid == portal_uuid)).first()`. If no `RequestPortal` matches `portal_uuid`, return `[]`, never an unfiltered query.
     - In `list_assets_public_mini`, also accept `locationId: int | None = Query(default=None)` (matching Java `AssetService.java:460-473` and `frontend/src/slices/asset.ts:231`), filtering `Asset.company_id == portal.company_id`, `Asset.archived.is_(False)`, and (when `locationId` is provided) `Asset.location_id == locationId`.
  2. **`_add_category_mini_route` (`assets_locations.py:37-49`)**:
     - Filter by `cls.company_settings_id == _ensure_company_settings_id(current_user, db)` when `hasattr(cls, "company_settings_id")`.
  3. **`GET /floor-plans/location/{location_id}` (`assets_locations.py:162-173`)**:
     - Verify `Location` exists with `Location.company_id == current_user.company_id` (else `404`) and filter `FloorPlan.company_id == current_user.company_id`.
  4. **`GET /readings/meter/{meter_id}` (`meters_requests_workflows_misc.py:119-130`)**:
     - Verify `Meter` exists with `Meter.company_id == current_user.company_id` (else `404`) before returning `Reading` rows.

#### 1.5 Production Postgres Migration (`db/migrations/003_*.sql`) + Startup Index Guard & Clone Fix (`P0-06`)
- **Files**:
  - [`atlas-cmms/db/migrations/003_asset_unique_identifiers.sql`](../atlas-cmms/db/migrations/003_asset_unique_identifiers.sql) (**native Canvas SQL migration run automatically on `canvas deploy`**)
  - [`atlas-cmms/src/tasks.py`](../atlas-cmms/src/tasks.py#L19-L64) (`ensure_asset_unique_indexes(db)` idempotent startup hook)
  - [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py)
  - [`frontend/src/content/own/Assets/Show/index.tsx`](../frontend/src/content/own/Assets/Show/index.tsx#L110-L155)
- **Fix Implementation**:
  1. **Production Postgres Migration (`db/migrations/003_asset_unique_identifiers.sql`) & Startup Enforcement (`src/tasks.py::ensure_asset_unique_indexes`)**:
     - Normalize empty strings (`''` or whitespace-only) on `asset.custom_id`, `asset.bar_code`, and `asset.nfc_id` to `NULL`.
     - Deduplicate any pre-existing duplicate `(company_id, custom_id)`, `(company_id, bar_code)`, or `(company_id, nfc_id)` rows in the database (appending `-dup-<id>` to `rn > 1` rows) so index creation cannot fail on existing data.
     - Create partial unique indexes (`CREATE UNIQUE INDEX IF NOT EXISTS`):
       - `uq_asset_company_custom_id` on `asset (company_id, custom_id) WHERE custom_id IS NOT NULL`
       - `uq_asset_company_bar_code` on `asset (company_id, bar_code) WHERE bar_code IS NOT NULL`
       - `uq_asset_company_nfc_id` on `asset (company_id, nfc_id) WHERE nfc_id IS NOT NULL`
     - On Canvas (`aj-cafm`), `db/migrations/003_asset_unique_identifiers.sql` is validated by `canvas validate` and executed automatically by the platform in its own transaction before the new container starts on `canvas deploy`. In addition, `ensure_asset_unique_indexes(db)` runs idempotently at FastAPI startup in `start_background_scheduler()` when `envs.DATABASE_URL` is configured.
  2. **Backend Validation + IntegrityError Handler**:
     - Check uniqueness of non-null `custom_id`, `bar_code`, and `nfc_id` within `current_user.company_id` before flush, and catch `sqlalchemy.exc.IntegrityError` to return a clean `HTTP 400` (`"Asset with this customId/barCode/nfcId already exists"`) on concurrent races.
  3. **Frontend Clone Modal (`Show/index.tsx`)**:
     - Update `getAssetFormValues(assetData, isCopy = false)` and pass `true` in `renderCopyModal` (`line 423`) so `customId`, `barCode`, and `nfcId` are cleared (`undefined`) when cloning an asset.

---

### Phase 2: Single-Transaction CRUD, Persistent File Upload & M2M / Custom Field Sync (`C-01`, `P0-02`, `P0-04`)

#### 2.1 Single-Transaction `create_item` and `before_patch` Hook in `build_crud_router` (`C-01`, `C-03`)
- **File**: [`atlas-cmms/src/routes/_crud.py`](../atlas-cmms/src/routes/_crud.py#L46-L200)
- **Root Cause**:
  1. `create_item` calls `db.commit()` at line 152, then runs `after_create(obj, payload, current_user, db)`, and calls `db.commit()` a second time at line 156. If `after_create` (such as M2M sync) fails, the half-saved `Asset` row is already committed!
  2. `patch_item` has no `before_patch` hook, so `after_patch` runs after `apply_patch` has already overwritten `obj.status`.
- **Fix Implementation**:
  1. In `create_item`:
     - Replace the first `db.commit()` + `db.refresh(obj)` before `after_create` with `db.flush()` (which populates `obj.id` from the sequence inside the open transaction).
     - Run `validate_foreign_key_ownership(obj, current_user, db)` and `after_create(obj, payload, current_user, db)`.
     - Call `db.commit()` and `db.refresh(obj)` **once** at the end.
  2. In `patch_item`:
     - Add `before_patch: Callable[[Any, dict[str, Any], User, Session], None] | None = None` to `build_crud_router`, invoked before `apply_patch(obj, payload)`.
     - After `apply_patch`, run `validate_foreign_key_ownership(obj, current_user, db)` and `after_patch(obj, payload, current_user, db)`, then `db.commit()` and `db.refresh(obj)` once.

#### 2.2 Persistent File Upload via `envs.DATA_DIR`, 25 MB Size Limit & Tenant-Checked Download (`P0-02`)
- **Files**:
  - [`atlas-cmms/src/envs.py`](../atlas-cmms/src/envs.py#L40-L45) (`DATA_DIR`)
  - [`atlas-cmms/src/routes/meters_requests_workflows_misc.py`](../atlas-cmms/src/routes/meters_requests_workflows_misc.py#L494-L603)
  - [`atlas-cmms/src/services/serializer.py`](../atlas-cmms/src/services/serializer.py#L220-L358)
- **Fix Implementation**:
  1. **Unified Deterministic Path (`DATA_DIR/uploads/{company_id}/{file_id}_{safe_name}`) & 25 MB Size Cap**:
     - Enforce `MAX_UPLOAD_FILE_BYTES = 25 * 1024 * 1024` (25 MB per file) on both authenticated `/files/upload` and public `/files/upload/request-portal/{portal_uuid}` by reading `f.file.read(MAX_UPLOAD_FILE_BYTES + 1)` and raising HTTP `413` (`"Uploaded file exceeds 25 MB limit"`) if exceeded.
     - Sanitize `safe_fname = re.sub(r"[^A-Za-z0-9._-]", "_", Path(fname).name) or "upload.bin"`.
     - Base company upload root: `company_dir = (envs.DATA_DIR / "uploads" / str(current_user.company_id)).resolve()`; `company_dir.mkdir(parents=True, exist_ok=True)`.
     - Determine `file_type_ord = 0` (`IMAGE`) if `type.upper() == "IMAGE"` or `(u.content_type or "").startswith("image/")` else `1` (`OTHER`).
     - Instantiate `FileEntity(name=safe_fname, path="", type=file_type_ord, hidden=is_hidden, company_id=current_user.company_id, created_by=current_user.id)`, `db.add(fe)`, and `db.flush()` so `fe.id` is assigned.
     - Compute `disk_path = (company_dir / f"{fe.id}_{safe_fname}").resolve()`, verify `disk_path.is_relative_to(company_dir)`, write `content` to `disk_path`, set `fe.path = f"/api/files/download/{fe.id}"`, and `db.commit()` once after the loop.
  2. **Tenant-Checked Download Route (`GET /api/files/download/{file_id}`)**:
     - Fetch `FileEntity` by `file_id`, verify `fe.company_id == current_user.company_id` (or `is_super_admin`), compute `disk_path = (company_dir / f"{fe.id}_{safe_fname}").resolve()`, verify `disk_path.is_relative_to(company_dir)` and `disk_path.is_file()`, and stream via `FileResponse`.
  3. **Serializer (`serializer.py`)**:
     - Ensure `File` serialization always includes `"url": obj.path` so `asset.image.url` and `asset.files[i].url` work across all React views.

#### 2.3 Asset M2M & `CustomFieldValue` Persistence and Hydration (`C-01`)
- **Files**:
  - [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py#L176-L250)
  - [`atlas-cmms/src/models/associations.py`](../atlas-cmms/src/models/associations.py#L168-L208)
  - [`atlas-cmms/src/models/files_custom.py`](../atlas-cmms/src/models/files_custom.py#L54-L74)
- **Fix Implementation**:
  1. **Synchronization in `_after_create_asset` and `_after_patch_asset` (same transaction before `db.commit()`)**:
     - Map each M2M payload key to its association table and target model:
       - `assignedTo` / `workers` $\rightarrow$ `t_asset_user_associations` (`id_asset`, `id_user`, `OwnUser`)
       - `teams` $\rightarrow$ `t_asset_team_associations` (`id_asset`, `id_team`, `Team`)
       - `vendors` $\rightarrow$ `t_asset_vendor_associations` (`id_asset`, `id_vendor`, `Vendor`)
       - `customers` $\rightarrow$ `t_asset_customer_associations` (`id_asset`, `id_customer`, `Customer`)
       - `parts` $\rightarrow$ `t_asset_part_associations` (`id_asset`, `id_part`, `Part`)
       - `files` $\rightarrow$ `t_asset_file_associations` (`id_asset`, `id_file`, `File`)
     - If a key is present in `payload` (including `[]`), validate all target IDs belong to `current_user.company_id`, delete existing links for `id_asset == asset.id`, and insert the deduplicated links. If omitted on `PATCH`, leave existing links untouched.
     - If `customFieldValues` is present in `payload`, validate each referenced `CustomField` belongs to the tenant's `company_settings_id` and replace/upsert `CustomFieldValue` rows for `asset_id == asset.id`.
  2. **Hydration in `_serialize_asset(obj, db=db)`**:
     - Query the 6 `t_asset_*_associations` tables and `CustomFieldValue` for `obj.id` and hydrate `assignedTo`, `teams`, `vendors`, `customers`, `parts`, `files`, and `customFieldValues` with mini-DTOs (`model_to_dict(item, db=db)`).

#### 2.4 Fix `GET /api/assets/part/{part_id}` Crash (`P0-04`)
- **File**: [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py#L331-L350)
- **Fix Implementation**: Import `t_asset_part_associations` from `src.models.associations` and join on `t_asset_part_associations.c.id_asset == Asset.id` where `t_asset_part_associations.c.id_part == part_id` and `Asset.company_id == current_user.company_id`.

---

### Phase 3: Postgres-Safe Search/M2M Filtering, Hierarchy SQL Sort & Java-Parity Import/Export (`P0-03`, `P0-05`, `P1-09`)

#### 3.1 Fix Asset Text Search (`customFieldValues.value`) & Postgres-Safe M2M Filter Subqueries (`P0-03`)
- **File**: [`atlas-cmms/src/utils/search.py`](../atlas-cmms/src/utils/search.py#L312-L545)
- **Root Cause**:
  1. `find_association_table` checks `f"t_{model_table}_{target_clean}_associations"` with plural `target_clean` (`teams`, `customers`, `vendors`, `parts`), failing to match singular `t_asset_team_associations`, `t_asset_customer_associations`, `t_asset_vendor_associations`, `t_asset_part_associations`.
  2. `resolve_field_and_joins` does not handle 1-to-many `customFieldValues.value` (`CustomFieldValue.asset_id == Asset.id`).
  3. Calling `.distinct()` on a query that has `ORDER BY` on a joined column (e.g., `ORDER BY location.name ASC`) raises `ProgrammingError: for SELECT DISTINCT, ORDER BY expressions must appear in select list` on PostgreSQL!
- **Fix Implementation**:
  1. In `find_association_table`, strip trailing `"s"` (`target_singular = target_clean[:-1] if target_clean.endswith("s") else target_clean`) and include singular candidate table names (`f"t_{model_table}_{target_singular}_associations"`).
  2. In `resolve_field_and_joins`, handle `rel_snake == "custom_field_values"` by outer-joining `CustomFieldValue` on `getattr(CustomFieldValue, f"{model_cls.__tablename__}_id") == model_cls.id` and resolving `.value`.
  3. **Mandatory Subquery Deduplication in `apply_search` / `paginate_search`**:
     - Build the filter query with all `WHERE` clauses (including M2M and `CustomFieldValue` joins) and extract matching primary keys via `matching_ids_subq = filter_stmt.with_only_columns(model_cls.id).distinct().subquery()`.
     - Filter the main query via `model_cls.id.in_(select(matching_ids_subq.c.id))` and apply only the `ORDER BY` joins to the main query. This guarantees zero duplicate rows, exact `totalElements` count, and 100% compatibility with PostgreSQL `ORDER BY` on joined columns.

#### 3.2 Fix Hierarchy Children SQL Sort & Pagination (`P1-09`)
- **File**: [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py#L131-L155) (and lines 290–313)
- **Fix Implementation**:
  - In `get_asset_children_paginated` and `get_location_children_paginated`, accept `sort: list[str] | None = Query(default=None)`, resolve sort expressions (including dotted paths like `location.name,asc`, `primaryUser.firstName,asc`, `category.name,asc`), compute `total` in SQL via `select(func.count())`, and apply `.order_by(...)`, `.offset(page_num * page_size)`, and `.limit(page_size)` in SQL before serializing the page slice.

#### 3.3 Full Java-Parity Import/Export & Template Download (`P0-05`)
- **Files**:
  - [`frontend/src/hooks/useExport.ts`](../frontend/src/hooks/useExport.ts)
  - [`frontend/src/hooks/useImport.ts`](../frontend/src/hooks/useImport.ts)
  - [`frontend/src/content/own/Imports/index.tsx`](../frontend/src/content/own/Imports/index.tsx#L62-L66)
  - [`atlas-cmms/src/routes/meters_requests_workflows_misc.py`](../atlas-cmms/src/routes/meters_requests_workflows_misc.py#L464-L538)
- **Root Cause**:
  1. `useExport.ts` and `useImport.ts` hang waiting on STOMP `/api/ws`, which does not exist in `atlas-cmms` (and even in Java `ExportController.java` is a direct `POST /export/{entity}` HTTP endpoint!).
  2. `Imports/index.tsx` sets `entity` from URL tail `'imports'` instead of defaulting to `'work-orders'`, and calls missing `GET /api/import/download-template`.
  3. Compare Java `ImportService.java:74-96` and `AssetService.java:492-648`:
     - Java topologically orders the CSV rows (`AssetService.orderAssets`) so parent assets referenced by `parentAssetName` in the same CSV batch are imported before their children!
     - Java matches existing assets for update by `(id, company_id)` or `(name, company_id)` (case-insensitive), auto-creates missing `AssetCategory` (`assetCategoryService.getOrCreate`), resolves `locationName`, `parentAssetName`, `primaryUserEmail`, `assignedToEmails`, `teamsNames`, `customersNames`, `vendorsNames`, `partsNames`, tracks `barCodes` seen in the CSV batch to prevent intra-batch duplicates, maps `"yes"`/`"true"` booleans (`archived`), and assigns `A######` `custom_id` when blank.
- **Fix Implementation**:
  1. **Frontend `useExport.ts` & `useImport.ts`**: Execute direct HTTP requests (`GET`/`POST /api/export/...` and `POST /api/import/...`) without waiting on STOMP WebSocket.
  2. **Frontend `Imports/index.tsx`**: Validate `entityFromUrl` against valid entity keys (`'work-orders'`, `'assets'`, `'locations'`, `'parts'`, `'meters'`, `'preventive-maintenances'`), defaulting to `'work-orders'`.
  3. **Backend `GET /api/import/download-template`**: Serve CSV templates with exact headers expected by `headerKeysConfig` in `Imports/index.tsx` for all 6 importable entities.
  4. **Backend `POST /api/import/assets`**: Implement topological ordering (`order_assets` so parent assets in the batch are processed before children), get-or-create `AssetCategory`, resolve `locationName`, `parentAssetName`, `primaryUserEmail`, and M2M lists (`assignedToEmails`, `teamsNames`, `customersNames`, `vendorsNames`, `partsNames`), enforce intra-batch and company barcode uniqueness, parse `"yes"`/`"no"` booleans, and assign `A{obj.id:06d}` when `custom_id` is empty.
  5. **Backend `POST` & `GET /api/export/assets`**: Support both `GET` and `POST` on `/api/export/{entity_name}` and export human-readable relational columns (`location.name`, `parentAsset.name`, `category.name`, `primaryUser.email`, etc.).

---

### Phase 4: Java-Parity Status $\leftrightarrow$ Downtime, WorkOrder Hooks, Meter Hydration & Frontend Fixes (`C-03`, `P1-07`, `P1-08`, `P1-10`, `P1-15`)

#### 4.1 Full Java-Parity Status $\leftrightarrow$ Downtime & WorkOrder Integration (`C-03`)
- **Files**:
  - [`atlas-cmms/src/routes/assets_locations.py`](../atlas-cmms/src/routes/assets_locations.py#L176-L250) (and lines 389–410)
  - [`atlas-cmms/src/routes/work_orders_pm.py`](../atlas-cmms/src/routes/work_orders_pm.py#L140-L220)
- **Java Reference**:
  - `AssetService.java:234-303, 424-428` (`isReallyDown`, `triggerDowntime`, `stopDowntime`, `recursivelyStopChildrenDowntime`)
  - `WorkOrderService.java:119-123, 866-880`
  - `AssetDowntimeService.java:95-107` (`checkOverlapping`)
- **Fix Implementation**:
  1. **`is_really_down(status: int | None) -> bool`**:
     - Return `status in (1, 6)` (`1 = DOWN`, `6 = EMERGENCY_SHUTDOWN`), matching Java `AssetStatus.isReallyDown()`.
  2. **`trigger_downtime(asset: Asset, current_user: User, db: Session, down_status: int = 1) -> None`** (matches `AssetService.java:234-265`, with an explicit intentional guard against creating duplicate running downtimes on parent assets):
     - Walk `current = asset` up the `parent_asset_id` chain (`while current is not None`, with cycle guard):
       - Ensure `current.status` is set to a down status (`down_status` if not already `is_really_down(current.status)`).
       - If no running `AssetDowntime` (`duration == 0`) exists for `current.id` (*intentional improvement over Java, which creates duplicate running downtimes on ancestors when multiple child assets go down*), create `AssetDowntime(asset_id=current.id, starts_on=utcnow(), duration=0, company_id=current_user.company_id, created_by=current_user.id, updated_by=current_user.id)`.
       - Advance `current` to its parent `Asset` (`current.parent_asset_id`).
  3. **`stop_downtime(asset: Asset, current_user: User, db: Session) -> None`** (matches `AssetService.java:267-303`):
     - Find running `AssetDowntime` rows (`asset_id == asset.id` and `duration == 0`) and set `duration = max(1, int((utcnow() - dt.starts_on).total_seconds()))`.
     - Set `asset.status = 0` (`OPERATIONAL`).
     - Recursively call `stop_downtime` on all direct child assets (`Asset.parent_asset_id == asset.id`, `Asset.company_id == asset.company_id`).
  4. **Hook into `PATCH /api/assets/{id}` (`assets_locations.py`)**:
     - Use `before_patch` to capture `was_down = is_really_down(obj.status)`.
     - In `after_patch`, check `now_down = is_really_down(obj.status)`.
     - If `not was_down and now_down`: call `trigger_downtime(obj, current_user, db, down_status=obj.status)`.
     - If `was_down and not now_down`: call `stop_downtime(obj, current_user, db)` (while preserving the user's chosen non-down `obj.status`, e.g. `OPERATIONAL`, `MODERNIZATION`, `STANDBY`).
  5. **Hook into `WorkOrder` Create & Complete (`work_orders_pm.py`)**:
     - On `POST /api/work-orders` (`_after_create_wo`): if `payload.get("assetStatus")` is provided and `wo.asset_id` is set, update the asset's status (and call `trigger_downtime` if `is_really_down`).
     - On `PATCH /api/work-orders/{id}` (`_before_patch_wo` / `_after_patch_wo`): when a work order transitions to `COMPLETE` (`status == 3`) and `wo.asset_id` is set, check if any other non-complete work orders exist for `wo.asset_id`. If none exist and the asset is currently down (`is_really_down(asset.status)`), call `stop_downtime(asset, current_user, db)`.
  6. **Downtime Overlap Validation (`check_overlapping` on `POST`/`PATCH /api/asset-downtimes`)**:
     - Matching `AssetDowntimeService.java:95-107`: when creating or editing an `AssetDowntime` with `duration > 0` (`ends_on = starts_on + timedelta(seconds=duration)`), query existing completed downtimes (`duration > 0`, `id != current_id`) for the same `asset_id`. If any satisfies `starts_on < other_ends_on and ends_on > other_starts_on`, raise `HTTPException(status_code=406, detail="The downtimes can't interweave")`.

#### 4.2 Fix Meter `lastReading` / `nextReading` Hydration & Reading Trigger `custom_id` (`P1-15`)
- **File**: [`atlas-cmms/src/routes/meters_requests_workflows_misc.py`](../atlas-cmms/src/routes/meters_requests_workflows_misc.py#L50-L130)
- **Root Cause**:
  1. `AssetMeters.tsx:192` gates the "Add Reading" button on `canAddReading(meter)` (`frontend/src/utils/overall.ts:17-24`), which compares `new Date()` against `new Date(meter.nextReading)`. `_serialize_meter` never computes `lastReading` or `nextReading`!
  2. In `_after_create_reading` (`meters_requests_workflows_misc.py:98-113`), when a meter reading crosses a `WorkOrderMeterTrigger`, it creates a `WorkOrder` without flushing and setting `wo.custom_id = f"W{wo.id:06d}"`.
- **Fix Implementation**:
  1. In `_serialize_meter(obj: Meter, db: Session | None = None)`:
     - Query the latest `Reading` for `Reading.meter_id == obj.id` ordered by `Reading.created_at.desc()` (or `Reading.id.desc()`).
     - If a latest reading exists, set `d["lastReading"] = latest.created_at.isoformat()` and `d["nextReading"] = (latest.created_at + timedelta(days=obj.update_frequency or 0)).isoformat()`, else `None`.
     - Hydrate `users` (`t_meter_user_associations`) as user mini-DTOs.
  2. In `_after_create_reading`, after `db.flush()` on a triggered `WorkOrder`, set `wo.custom_id = f"W{wo.id:06d}"`.

#### 4.3 Fix Downtime Edit Modal, Asset Form `parts` Multi-Select, Filter Bugs & Hierarchy Delete (`P1-07`, `P1-08`, `P1-10`)
- **Files**:
  - [`frontend/src/content/own/Assets/Show/AssetDowntimes.tsx`](../frontend/src/content/own/Assets/Show/AssetDowntimes.tsx#L240-L266)
  - [`frontend/src/content/own/Assets/index.tsx`](../frontend/src/content/own/Assets/index.tsx#L752)
  - [`frontend/src/content/own/Assets/Show/index.tsx`](../frontend/src/content/own/Assets/Show/index.tsx#L355)
  - [`frontend/src/content/own/Assets/Filters.tsx`](../frontend/src/content/own/Assets/Filters.tsx#L38-L236)
  - [`frontend/src/slices/asset.ts`](../frontend/src/slices/asset.ts#L90-L104)
- **Fix Implementation**:
  1. **`AssetDowntimes.tsx`**: Import `editAssetDowntime` and dispatch `editAssetDowntime(currentDowntime.id, asset.id, values)` in `renderEditModal`.
  2. **`Assets/index.tsx` & `Assets/Show/index.tsx`**: Add `multiple: true` to the `parts` field config (`{ name: 'parts', type: 'select', type2: 'part', label: t('parts'), multiple: true }`).
  3. **`Assets/Filters.tsx`**: Read `vendorsMini` from `state.vendors` (and dispatch `getVendorsMini()`) for the `vendors` filter's `getOptionLabel`, and use optional chaining `?.value` on the `archived` filter lookup.
  4. **`frontend/src/slices/asset.ts` (`deleteAsset` reducer)**:
     - Walk `parentAsset?.id` iteratively to collect `id` and all descendant IDs in `state.assetsHierarchy`:
       ```ts
       const toRemove = new Set<number>([id]);
       let added = true;
       while (added) {
         added = false;
         for (const row of state.assetsHierarchy) {
           if (!toRemove.has(row.id) && row.parentAsset?.id && toRemove.has(row.parentAsset.id)) {
             toRemove.add(row.id);
             added = true;
           }
         }
       }
       state.assets.content = state.assets.content.filter((a) => !toRemove.has(a.id));
       state.assetsHierarchy = state.assetsHierarchy.filter((a) => !toRemove.has(a.id));
       ```

---

### Phase 5: Java-Parity Asset Statistics Tab & Fleet Analytics (`C-02`, `P1-13`, `P1-14`)

#### 5.1 Implement `/api/analytics/assets/{asset_id}/overview` with Exact Java Formulas (`C-02`)
- **Files**:
  - [`atlas-cmms/src/routes/analytics.py`](../atlas-cmms/src/routes/analytics.py#L167-L199)
  - [`frontend/src/content/own/Assets/Show/AssetAnalytics.tsx`](../frontend/src/content/own/Assets/Show/AssetAnalytics.tsx#L35-L65)
- **Java Reference**: [`AssetService.java:654-715`](../atlas-cmms/.canvas/legacy/api/src/main/java/com/grash/service/AssetService.java#L654-L715), [`Labor.java:80-108`](../atlas-cmms/.canvas/legacy/api/src/main/java/com/grash/model/Labor.java#L80-L108), and [`AssetAnalyticsController.java:380-410`](../atlas-cmms/.canvas/legacy/api/src/main/java/com/grash/controller/analytics/AssetAnalyticsController.java#L380-L410)
- **Fix Implementation**:
  1. Register `@router.post("/assets/{asset_id:int}/overview")` and `@router.get("/assets/{asset_id:int}/overview")` **before** `/assets/{subpath:path}` in `atlas-cmms/src/routes/analytics.py`:
     - Verify `Asset` exists with `asset.company_id == current_user.company_id` (and `can_view(current_user, PermissionEntity.ANALYTICS, db)` or `PermissionEntity.ASSETS`).
     - Parse `[start, end]` from `DateRange` payload (`start` defaults to 30 days ago, `end` defaults to `utcnow()`).
     - Compute exact Java-parity metrics (`AssetService.java:665-715` and `Labor.java:80-108`):
       - **`downtime`** (`getDowntime` in seconds, `AssetService.java:695-698`): sum of `dt.duration` for `AssetDowntime` rows of `asset_id` with `starts_on` between `start` and `end` (in Java, a still-running downtime has `duration == 0`, so it contributes `0`).
       - **`uptime`** (`getUptime` in seconds, `AssetService.java:700-708`): `real_created_at = asset.in_service_date or asset.created_at`. Clamp window to `effective_start = max(start, real_created_at)` and `effective_end = min(end, utcnow())`. If `effective_start > effective_end`, `uptime = 0`; else `max(0, int((effective_end - effective_start).total_seconds()) - get_downtime(asset_id, effective_start, effective_end))`.
       - **`mtbf`** (`getMTBF` in **whole days**, `AssetService.java:665-684`): query `AssetDowntime` rows for `asset_id` with `starts_on` between `start` and `end` sorted by `starts_on ASC`. If `len(downtimes) < 2`, return `0`. Otherwise, for each adjacent pair `(curr, next_dt)`, compute whole days via integer truncation `interval = int((next_dt.starts_on - (curr.starts_on + timedelta(seconds=curr.duration))).total_seconds()) // 86400`, sum the intervals, and return `intervals_sum // (len(downtimes) - 1)` (integer division).
       - **`mttr`** (`getMTTR` in **integer minutes**, `AssetService.java:686-693` & `Labor.getTotalWorkDuration`, `Labor.java:80-108`): query `WorkOrder` rows for `asset_id` with `created_at` between `start` and `end`. If none, return `0`. Collect all `Labor` rows across those work orders where `started_at is not None`, sort by `started_at ASC`, merge overlapping intervals (`current_end = started_at + timedelta(seconds=duration)`; if `previous_end` and `current_start < previous_end`, add `max(0, int((current_end - previous_end).total_seconds()))`, else add `duration`; update `previous_end = max(previous_end, current_end)`), and return `(total_duration_seconds // 60) // len(work_orders)`.
       - **`totalCost`** (`getTotalCost`, `AssetService.java:654-663`): sum of labor cost + part quantity cost + additional cost across work orders for `asset_id` in `[start, end]`.
     - Return `{"mtbf": mtbf, "mttr": mttr, "downtime": downtime, "uptime": uptime, "totalCost": round(total_cost, 2)}`.
  2. Add defensive null-coalescing `(assetDetailsOverview?.mtbf ?? 0).toString()` in `AssetAnalytics.tsx`.

#### 5.2 Implement Fleet Asset Analytics Endpoints (`/overview`, `/costs/overview`, Trends) (`C-02`, `P1-13`)
- **File**: [`atlas-cmms/src/routes/analytics.py`](../atlas-cmms/src/routes/analytics.py#L168-L199)
- **Java Reference**: [`AssetAnalyticsController.java:53-378`](../atlas-cmms/.canvas/legacy/api/src/main/java/com/grash/controller/analytics/AssetAnalyticsController.java#L53-L378)
- **Fix Implementation**:
  1. **`POST`/`GET /api/analytics/assets/overview`**: Replace hardcoded `95.0` availability and `0.0` MTBF with real Java-parity calculation over tenant assets in `[start, end]`:
     - `downtime`: sum of `get_downtime` across tenant assets
     - `uptime`: sum of `get_uptime` across tenant assets
     - `availability`: `0` if `uptime + downtime == 0` else `round(uptime * 100.0 / (uptime + downtime), 2)`
     - `crashedAssets`: count of assets with $\ge 1$ downtime in `[start, end]`
     - `mtbf`: mean of `get_mtbf` across tenant assets
     - `mttr`: mean of `get_mttr` across tenant assets
  2. **`POST`/`GET /api/analytics/assets/costs/overview`**: Return `{"totalWOCosts": ..., "totalAcquisitionCost": ..., "rav": ...}` (fixing the `AcquisitionCost` $\rightarrow$ `totalAcquisitionCost` key mismatch).
  3. **Fleet Trend & Meantime Endpoints**: Implement `/assets/mtbf`, `/assets/mttr`, `/assets/downtimes/meantime`, `/assets/repair-times`, `/assets/downtimes/costs`, `/assets/downtimes/costs/date`, `/assets/costs/date`, and `/assets/time-cost` before the catch-all fallback so every chart in `/app/analytics/assets` renders real data.

#### 5.3 Align `API_CONTRACTS.md` and `DATABASE.md` (`P1-14`)
- **Files**: [`atlas-cmms/API_CONTRACTS.md`](../atlas-cmms/API_CONTRACTS.md), [`atlas-cmms/DATABASE.md`](../atlas-cmms/DATABASE.md)
- **Fix Implementation**: Update both docs to reflect the hydrated M2M & `customFieldValues` contracts, `RequestPortal.uuid` public mini scoping, `AssetDowntime` columns (`starts_on`, `duration`), `/api/deprecations` path, and `db/migrations/003_asset_unique_identifiers.sql` + `src/tasks.py::ensure_asset_unique_indexes` partial unique indexes.

---

## 3. Mandatory 10-Step Execution Order

We will execute and verify these changes in the exact dependency order specified by the review:

1. **Step 1 — Patch `apply_patch()` & Generic FK Ownership Validation**:
   - Protect `company_id`, `company_settings_id`, `created_at`, `created_by`, `updated_at`, `updated_by` against nested-dict override in `serializer.py`.
   - Support clearing nullable FKs (`{"location": None}`) and normalizing blank identity strings (`""` $\rightarrow$ `None`).
   - Add `validate_foreign_key_ownership` and `before_patch` + single-transaction `db.flush()` $\rightarrow$ hooks $\rightarrow$ `db.commit()` in `src/routes/_crud.py`.
2. **Step 2 — Wire Role & Entity Permissions (`src/deps/permissions.py` & `src/routes/_crud.py`)**:
   - Update `can_edit`/`can_delete` ownership semantics in `src/deps/permissions.py` and wire `permission_entity` across `build_crud_router` and custom asset/location/meter/analytics routes.
3. **Step 3 — Fix Tenant Leaks (`P0-01`, `P1-12`) & Cycle Detection (`P1-11`)**:
   - Scope public mini routes via `RequestPortal.uuid` (plus optional `locationId`), `_add_category_mini_route` via `company_settings_id`, `get_floor_plans_by_location`, and `list_readings_by_meter`.
   - Add ancestor cycle detection for `Asset.parent_asset_id` and `Location.parent_location_id`.
4. **Step 4 — Production Postgres Migration (`db/migrations/003_*.sql`), Startup Guard & Clone Deduplication (`P0-06`)**:
   - Create `atlas-cmms/db/migrations/003_asset_unique_identifiers.sql` (run automatically by Canvas on `canvas deploy`) and idempotent `ensure_asset_unique_indexes(db)` in `atlas-cmms/src/tasks.py` normalizing blank strings, deduplicating any existing collisions, and creating tenant-scoped partial unique indexes on `(company_id, custom_id)`, `(company_id, bar_code)`, and `(company_id, nfc_id)`.
   - Strip `customId`, `barCode`, and `nfcId` when cloning in `frontend/src/content/own/Assets/Show/index.tsx`.
5. **Step 5 — Fix File Upload, 25 MB Size Cap & Tenant-Scoped Download (`P0-02`)**:
   - Enforce `MAX_UPLOAD_FILE_BYTES = 25 * 1024 * 1024` (HTTP 413), persist uploaded file bytes under `envs.DATA_DIR / "uploads"`, fix `File` model kwargs (`path`, `type`), enforce tenant check on `GET /api/files/download/{file_id}`, and expose `url` in `File` serialization.
6. **Step 6 — Asset M2M & `CustomFieldValue` Sync + Hydration & Part-Assets Route (`C-01`, `P0-04`)**:
   - Sync all 6 `t_asset_*_associations` tables and `CustomFieldValue` in the same transaction on `POST`/`PATCH /api/assets` and hydrate them in `_serialize_asset`.
   - Fix `GET /api/assets/part/{part_id}` to join `t_asset_part_associations`.
7. **Step 7 — Postgres-Safe Search Subquery, Hierarchy SQL Sort & Import/Export Parity (`P0-03`, `P1-09`, `P0-05`)**:
   - Fix `find_association_table` singularization, `customFieldValues.value` join, and mandatory `Asset.id.in_(subquery)` deduplication in `src/utils/search.py`.
   - Implement SQL `ORDER BY` + `OFFSET`/`LIMIT` in `get_asset_children_paginated` and `get_location_children_paginated`.
   - Fix `useImport.ts`, `useExport.ts`, `Imports/index.tsx`, `GET /api/import/download-template`, and topological/relational `POST /api/import/assets`.
8. **Step 8 — Full Java Status $\leftrightarrow$ Downtime & WorkOrder Lifecycle + Meter Hydration (`C-03`, `P1-15`)**:
   - Implement `is_really_down` (`DOWN` / `EMERGENCY_SHUTDOWN`), ancestor-cascading `trigger_downtime`, child-recursive `stop_downtime`, WorkOrder create/complete downtime hooks, and `HTTP 406` downtime overlap validation.
   - Hydrate `lastReading` and `nextReading` in `_serialize_meter` and assign `W######` on reading-triggered WorkOrders.
9. **Step 9 — Frontend Form/Filter/Hierarchy Fixes & Java-Parity Asset Analytics (`P1-07`, `P1-08`, `P1-10`, `C-02`, `P1-13`, `P1-14`)**:
   - Fix `AssetDowntimes.tsx` edit dispatch, `parts` `multiple: true`, `Filters.tsx` vendor/archived bugs, and `deleteAsset` iterative `parentAsset?.id` walk in `slices/asset.ts`.
   - Implement `/api/analytics/assets/{id}/overview` and fleet analytics endpoints with Java-parity formulas, plus update `API_CONTRACTS.md` and `DATABASE.md`.
10. **Step 10 — Granular Contract Test Suite (`tests/test_asset_management_fixes.py`), Lint & Static UI Sync**:
    - Run `.venv/bin/pytest -q && .venv/bin/ruff check .` in `atlas-cmms/` with 12 isolated `test_01_*` through `test_12_*` functions covering all 22 fixes, SQL migration deduplication + partial unique index enforcement, and 25 MB upload size limit.
    - Run `npm run lint && npm run build` in `frontend/` and sync `build/*` to `atlas-cmms/src/static/` and `atlas-cmms/src/static/ui/`.
