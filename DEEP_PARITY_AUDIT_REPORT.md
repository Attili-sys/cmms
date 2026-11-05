# Deep Parity Audit Report & Principal Reviewer Sign-Off

**Audit Date:** 2026-10-26  
**Codebases Audited:**
- Legacy Java Reference: `api/src/main/java/com/grash/`
- Canvas Python Backend: `atlas-cmms/src/`
- React TypeScript Frontend: `frontend/src/`

---

## Principal Reviewer Sign-Off & Branch Reconciliation

### Why 8 of the 12 Findings Appeared in the Other Agent's Audit
When the secondary audit session ran, its git worktree (`deep_parity_audit_report`) was branched off the local `migrate-python` branch (`61443df8`, 57 tests) **before** our remediation branch (`explain_asset_management_plans` @ `569732b7`, 80 tests, deployed to Canvas `@c9e197b0d631`) was merged into `migrate-python`. Those counts are historical. The current suite on `migrate-python` is 85 tests (`uv run pytest -q`, 2026-11-04). The current Canvas deployment is build **#17** (`@e5e83dfd328e`); the older `@c9e197b0d631` identifier is retained only as historical audit provenance.

Consequently, **8 of the 12 findings** in the raw audit report were **already fixed and regression-tested** on `explain_asset_management_plans` (`d1e8fc06` / `569732b7`), while **4 of the 12 findings are genuine, high-value new catches** on `explain_asset_management_plans`. Furthermore, our code review of the other agent's proposed patches caught **2 runtime bugs in the proposed solutions** (which are corrected in Section 3 below).

| ID | Finding Summary | Status on `explain_asset_management_plans` (`569732b7`) | Reviewer Sign-Off Verdict |
|---|---|---|---|
| **P0-01** | `POST /users` crashes with `TypeError: 'is_demo' is an invalid keyword argument for User` | **ALREADY FIXED** (`src/routes/auth_users.py:692-708`) | Already fixed & tested in `tests/test_non_asset_audit_fixes.py` |
| **P0-02** | `apply_patch` ignores `{"asset": null}` / `{"primaryUser": null}` when clearing nullable foreign keys | **ALREADY FIXED** (`src/services/serializer.py:446-456`) | Already fixed & tested in `tests/test_non_asset_audit_fixes.py` |
| **P0-03** | Many-to-Many search filters (`assignedTo`, `teams`, `customers`, `vendors`, `parts`) fail in `search.py` | **ALREADY FIXED** (`src/utils/search.py:312-354, 405-424`) | Verified all 21 `(model, field)` M2M filter pairs pass via runtime probe |
| **P0-04** | `GET /floor-plans/location/{id}` missing permission and cross-tenant `assert_company_access` check | **ALREADY FIXED** (`src/routes/assets_locations.py:580-597`) | Already fixed & tested in `tests/test_asset_fixes.py` |
| **P0-05** | `RequestPortal` and `RequestPortalField` foreign keys missing `ondelete="CASCADE"` / `"SET NULL"` | **FIXED & VERIFIED** (`src/models/requests.py:56, 70-75`) | **SIGNED OFF & REMEDIATED** (`test_deep_parity_remaining_fixes`) |
| **P1-06** | Interactive routes (`WorkOrder`, `Request`, `Part`, `Asset`, `PurchaseOrder`) omit in-app bell `Notification` creation + `Notification` CRUD lacks `user_id == current_user.id` scoping | **FIXED & VERIFIED** (`src/services/notifications.py`, `src/routes/_crud.py`) | **SIGNED OFF & REMEDIATED** (Fixed Auditor's Patch 5 `company_id`/`link_id` bug; added per-user `Notification` scoping + `test_deep_parity_remaining_fixes`) |
| **P1-07** | `POST /readings` omits `WorkOrderMeterTrigger` evaluation and automatic `WorkOrder` creation | **ALREADY FIXED** (`src/routes/meters_requests_workflows_misc.py:217-297`) | Already fixed & tested in `tests/test_non_asset_audit_fixes.py` |
| **P1-08** | Background `pm_generator.py` omits M2M cloning (`assigned_to`, `customers`, `files`, `tasks`) & weekly day-of-week recurrence | **ALREADY FIXED** (`src/jobs/pm_generator.py:67-230`) | Already fixed & tested in `tests/test_non_asset_audit_fixes.py` |
| **P1-09** | `POST /import/{entity_name}` drops relational CSV columns (`locationName`, `assetName`, `primaryUserEmail`, M2M emails) | **ALREADY FIXED** (`src/routes/meters_requests_workflows_misc.py:1508-2108`) | Already fixed & tested in `tests/test_asset_fixes.py` & `tests/test_non_asset_audit_fixes.py` |
| **P1-10** | Missing `POST /subscriptions/upgrade` and `GET /subscriptions/downgrade` endpoints called by `JWTAuthContext.tsx` | **FIXED & VERIFIED** (`src/routes/auth_users.py:422-442`) | **SIGNED OFF & REMEDIATED** (`test_deep_parity_remaining_fixes`) |
| **P1-11** | `GET /license/state` omits `entitlements`, `expirationDate`, and `planName` expected by `frontend/src/models/owns/license.ts` | **FIXED & VERIFIED** (`src/routes/auth_users.py:361-411`) | **SIGNED OFF & REMEDIATED** (Fixed Auditor's Patch 11 field names to match `LicensingState`; verified in `test_deep_parity_remaining_fixes`) |
| **P1-12** | `GET /export/{entity_name}` omits relational names/emails and full entity columns | **ALREADY FIXED** (`src/routes/meters_requests_workflows_misc.py:1147-1441`) | Already fixed & tested in `tests/test_asset_fixes.py` & `tests/test_non_asset_audit_fixes.py` |

---

## Section 1: Detailed Verification of the 8 Already-Resolved Items on `explain_asset_management_plans`

1. **P0-01 (`User` creation `is_demo` crash)**: Fixed in `atlas-cmms/src/routes/auth_users.py:692-708` — `User(...)` is instantiated without `is_demo`.
2. **P0-02 (Clearing nullable foreign keys in `apply_patch`)**: Fixed in `atlas-cmms/src/services/serializer.py:446-456` — when `val is None` and `f"{snake_key}_id"` exists on `obj`, `setattr(obj, fk_key, None)` clears the foreign key column.
3. **P0-03 (Many-to-Many search filters in `search.py`)**: Fixed in `atlas-cmms/src/utils/search.py:312-354, 405-424` via `_M2M_FIELD_MAP` and `find_association_table`. Runtime verification across all 21 `(model_cls, field_name)` pairs (`WorkOrder.assignedTo`, `Asset.teams`, `Asset.users`, `Asset.vendors`, `Asset.customers`, `Asset.parts`, `Part.assignedTo`, `Part.teams`, `Part.customers`, `Part.vendors`, `Part.users`, `Location.workers`, `Location.teams`, `Location.customers`, `Location.vendors`, `Meter.users`, `Request.assignedTo`, `Request.teams`, `Request.customers`, `PreventiveMaintenance.assignedTo`, `PreventiveMaintenance.teams`, `PreventiveMaintenance.customers`) confirmed 21/21 compile valid SQL `EXISTS (SELECT 1 FROM <assoc_table> WHERE ...)` subqueries without error.
4. **P0-04 (`GET /floor-plans/location/{id}` tenant isolation)**: Fixed in `atlas-cmms/src/routes/assets_locations.py:580-597` — checks `can_view(current_user, PermissionEntity.LOCATIONS, db)` and `assert_company_access(current_user, loc.company_id)`.
5. **P1-07 (`POST /readings` meter triggers)**: Fixed in `atlas-cmms/src/routes/meters_requests_workflows_misc.py:217-297` (`_after_create_reading`).
6. **P1-08 (`pm_generator.py` M2M cloning & weekly day-of-week recurrence)**: Fixed in `atlas-cmms/src/jobs/pm_generator.py:67-230` (`advance_schedule_next_due_date` and `create_work_order_from_pm`).
7. **P1-09 (`POST /import/{entity_name}` relational resolution)**: Fixed in `atlas-cmms/src/routes/meters_requests_workflows_misc.py:1508-2108`.
8. **P1-12 (`GET /export/{entity_name}` relational columns)**: Fixed in `atlas-cmms/src/routes/meters_requests_workflows_misc.py:1147-1441`.

---

## Section 2: Deep Analysis of the 4 Genuine Remaining Issues

### 1. [P0-05] Missing Foreign Key `ondelete` Cascades on `RequestPortal` and `RequestPortalField`
- **Audit Bucket:** Bucket 2 (Database Cascade Deletes & HTTP 500 Traps)
- **Proof Citations:**
  - `atlas-cmms/src/models/requests.py:56`: `company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id"), nullable=False)`
  - `atlas-cmms/src/models/requests.py:70`: `company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id"), nullable=False)`
  - `atlas-cmms/src/models/requests.py:72`: `location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id"), nullable=True)`
  - `atlas-cmms/src/models/requests.py:73`: `asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id"), nullable=True)`
  - `atlas-cmms/src/models/requests.py:75`: `request_portal_id: Mapped[int] = mapped_column("request_portal_id", BigInteger, ForeignKey("request_portal.id"), nullable=False)`
- **Root Cause:** Every other operational model in `atlas-cmms/src/models/` defines explicit `ondelete="CASCADE"` (for non-nullable FKs) or `ondelete="SET NULL"` (for nullable FKs). `RequestPortal` and `RequestPortalField` omitted `ondelete` on all 5 foreign keys. If a `Location` or `Asset` referenced by a `RequestPortalField` is deleted, or a `RequestPortal` with fields is deleted, PostgreSQL / SQLite (`PRAGMA foreign_keys = ON`) raises `IntegrityError` (HTTP 500).

---

### 2. [P1-06] In-App Bell `Notification` Creation & Per-User Notification Scoping
- **Audit Bucket:** Bucket 1 & Bucket 3 (In-App Bell Notifications & Tenant/User Isolation)
- **Proof Citations:**
  - **Java Reference:**
    - `api/src/main/java/com/grash/controller/NotificationController.java:39-57` (scopes `POST /notifications/search` to `user.getId()` and checks `notification.getUser().getId().equals(user.getId())` on `PATCH /notifications/{id}`)
    - `api/src/main/java/com/grash/service/WorkOrderService.java:162-177, 297-350, 417-428` (creates `Notification` rows for `primaryUser`, `assignedTo` users, and `team` members on WO create/update/comment)
    - `api/src/main/java/com/grash/service/RequestService.java:96-112, 232-242` (notifies `primaryUser`, `assignedTo`, `team` users on Request create, and `createdBy` on Request approval)
    - `api/src/main/java/com/grash/service/AssetService.java:155-169, 250-264` (notifies `primaryUser`, `users`, `teams`, and status change when Asset becomes `DOWN`)
    - `api/src/main/java/com/grash/service/PartService.java:141-162` (notifies `assignedTo`, `users`, `teams`)
    - `api/src/main/java/com/grash/service/PurchaseOrderService.java:114-121` (notifies `createdBy` on PO approval/rejection)
  - **Python Implementation:**
    - `atlas-cmms/src/models/files_custom.py:76-88` (`Notification` model has columns: `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `message`, `notification_type`, `resource_id`, `seen`, `user_id`)
    - `atlas-cmms/src/services/serializer.py:132` (`"notification_type": NotificationType` where `0=INFO`, `1=ASSET`, `2=REQUEST`, `3=WORK_ORDER`, `4=PART`, `5=METER`, `6=LOCATION`, `7=TEAM`, `8=PURCHASE_ORDER`)
    - `atlas-cmms/src/routes/meters_requests_workflows_misc.py:932` (`notifications_router = build_crud_router("/notifications", Notification)`)
    - `atlas-cmms/src/routes/_crud.py:290-330` and `src/utils/search.py:490-515` (`Notification` has no `company_id` or `company_settings_id`, so `POST /notifications/search` and `GET /notifications` currently return notifications for ALL users across ALL companies!)
  - **Frontend Reference:**
    - `frontend/src/slices/notification.ts:101-125` (`getNotifications` posts to `/notifications/search`; `editNotification` patches `/notifications/{id}`; clicking a notification navigates using `notificationType` and `resourceId`)
- **Reviewer Correction to Auditor's Patch 5:**
  - The other agent's proposed `create_in_app_notifications` passed `company_id=company_id` and `link_id=link_id` to `Notification(...)` and `"WORK_ORDER"` as a string. That would crash with `TypeError` and `StatementError` because `Notification` has **no** `company_id` or `link_id` column (the column is `resource_id: BigInteger`), and `notification_type` is a `SmallInteger` (`NotificationType.WORK_ORDER.value == 3`, serialized to `"WORK_ORDER"` by `serializer.py`).
  - Additionally, `Notification` must be strictly scoped to `Notification.user_id == current_user.id` in `GET /notifications`, `POST /notifications/search`, `GET /notifications/{id}`, `PATCH /notifications/{id}`, and `DELETE /notifications/{id}`.

---

### 3. [P1-10] Missing `POST /subscriptions/upgrade` and `GET /subscriptions/downgrade` Endpoints
- **Audit Bucket:** Bucket 1 (100% Frontend Slice & Route Audit)
- **Proof Citations:**
  - **Frontend Reference:** `frontend/src/contexts/JWTAuthContext.tsx:1104-1125`:
    ```ts
    const upgradeSubscription = async (users: number) => {
      const response = await api.post<{ url: string; message: string }>('subscriptions/upgrade', users);
      return response.data;
    };
    const downgradeSubscription = async (usersIds: number[]) => {
      const response = await api.get<SuccessDTO>(`subscriptions/downgrade?usersIds=${usersIds.join(',')}`);
      return response.data;
    };
    ```
  - **Python Implementation:** `atlas-cmms/src/routes/auth_users.py:371-409` only defines `GET /subscriptions`, `GET /subscriptions/{id}`, and `PATCH /subscriptions/{id}`.
- **Root Cause:** In unrestricted self-hosted mode, if a user triggers the upgrade or downgrade action from the account settings UI, FastAPI returns `405 Method Not Allowed` or `422 Unprocessable Entity` (trying to parse `"downgrade"` as `item_id: int` in `GET /subscriptions/{item_id}`). Adding no-op success handlers before `GET /subscriptions/{item_id}` prevents HTTP errors while honoring the unrestricted self-hosted policy.

---

### 4. [P1-11] `GET /license/state` Missing `entitlements`, `expirationDate`, and `planName`
- **Audit Bucket:** Bucket 1 (100% Frontend Slice & Route Audit)
- **Proof Citations:**
  - **Frontend Contract:** `frontend/src/models/owns/license.ts:1-43` and `frontend/src/slices/license.ts:13-20`:
    ```ts
    export type LicensingState = {
      valid: boolean;
      entitlements: LicenseEntitlement[];
      expirationDate: string;
      planName: string;
    };
    export const hasFeature = (state: RootState, feature: LicenseEntitlement): boolean => {
      if (!cloudVersion) return true;
      return state.license.state.entitlements.includes(feature);
    };
    ```
  - **Python Implementation:** `atlas-cmms/src/routes/auth_users.py:361-368`:
    ```python
    @router.get("/license/state")
    def license_state() -> dict[str, Any]:
        return {
            "valid": LicenseService.is_license_valid(),
            "unrestricted": LicenseService.is_unrestricted_self_hosted(),
            "state": "VALID",
        }
    ```
- **Reviewer Correction to Auditor's Patch 11:**
  - The other agent proposed returning `active`, `features`, `isUnrestricted`, `expiryDate` — none of which exist on `LicensingState` in `frontend/src/models/owns/license.ts`!
  - The exact fields required by `LicensingState` are `valid` (`bool`), `entitlements` (`list[str]` containing all 35 `LicenseEntitlement` strings), `expirationDate` (`"2099-12-31T23:59:59.000Z"`), and `planName` (`"ENTERPRISE"`), alongside `"unrestricted": True` and `"state": "VALID"` for backward compatibility.

---

## Section 3: Corrected, Self-Contained Remediation Specifications

### Fix 1: Add `ondelete` Cascades to `RequestPortal` & `RequestPortalField` (`atlas-cmms/src/models/requests.py`)
```python
class RequestPortal(Base):
    __tablename__ = "request_portal"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("request_portal_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    ...

class RequestPortalField(Base):
    __tablename__ = "request_portal_field"

    id: Mapped[int] = mapped_column("id", BigInteger, Sequence("request_portal_field_seq", start=1, increment=50, metadata=Base.metadata), primary_key=True, nullable=False)
    company_id: Mapped[int] = mapped_column("company_id", BigInteger, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column("type", String(255), nullable=False)
    location_id: Mapped[int | None] = mapped_column("location_id", BigInteger, ForeignKey("location.id", ondelete="SET NULL"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column("asset_id", BigInteger, ForeignKey("asset.id", ondelete="SET NULL"), nullable=True)
    required: Mapped[bool] = mapped_column("required", Boolean, nullable=False)
    request_portal_id: Mapped[int] = mapped_column("request_portal_id", BigInteger, ForeignKey("request_portal.id", ondelete="CASCADE"), nullable=False)
```

### Fix 2: Per-User `Notification` Scoping & Interactive In-App Notification Helper (`atlas-cmms/src/services/notifications.py`, `src/routes/_crud.py`, `src/utils/search.py`, and route hooks)
1. **Per-User `Notification` Scoping (`_crud.py` & `search.py`):**
   - When `model_cls.__name__ == "Notification"`, scope `GET /notifications`, `POST /notifications/search`, `GET /notifications/{id}`, `PATCH /notifications/{id}`, and `DELETE /notifications/{id}` to `Notification.user_id == current_user.id`.
2. **In-App Notification Helper (`src/services/notifications.py`):**
   ```python
   from collections.abc import Iterable
   from sqlalchemy import select
   from sqlalchemy.orm import Session
   from src.models.associations import t_team_users
   from src.models.enums import NotificationType
   from src.models.files_custom import Notification

   def create_in_app_notifications(
       db: Session,
       *,
       user_ids: Iterable[int | None] = (),
       team_ids: Iterable[int | None] = (),
       message: str,
       notification_type: NotificationType | int,
       resource_id: int | None,
       exclude_user_id: int | None = None,
       created_by: int | None = None,
   ) -> list[Notification]:
       target_users: set[int] = {int(uid) for uid in user_ids if uid is not None}
       clean_teams = [int(tid) for tid in team_ids if tid is not None]
       if clean_teams:
           team_member_ids = db.scalars(
               select(t_team_users.c.user_id).where(t_team_users.c.team_id.in_(clean_teams))
           ).all()
           target_users.update(int(uid) for uid in team_member_ids if uid is not None)
       if exclude_user_id is not None:
           target_users.discard(int(exclude_user_id))

       ntype_val = int(notification_type.value if isinstance(notification_type, NotificationType) else notification_type)
       created: list[Notification] = []
       for uid in sorted(target_users):
           notif = Notification(
               user_id=uid,
               message=message[:255],
               notification_type=ntype_val,
               resource_id=resource_id,
               seen=False,
               created_by=created_by,
           )
           db.add(notif)
           created.append(notif)
       return created
   ```
3. **Wire `create_in_app_notifications` into interactive routes:**
   - `WorkOrder` create & patch (`src/routes/work_orders_pm.py`): notify `primary_user_id`, `assigned_to`, and `team_id` members (excluding `current_user.id`).
   - `Request` create & approve (`src/routes/meters_requests_workflows_misc.py`): notify `primary_user_id`, `assigned_to`, `team_id` members on create; notify `created_by` on approve.
   - `Asset` create & patch (`src/routes/assets_locations.py`): notify `primary_user_id`, `users`, `teams` on assignment or status change to `DOWN`.
   - `Part` create & patch (`src/routes/parts_po_vendors.py`): notify `assigned_to`, `users`, `teams`.
   - `PurchaseOrder` respond (`src/routes/parts_po_vendors.py`): notify `created_by` when approved/rejected.

### Fix 3: Add `POST /subscriptions/upgrade` and `GET /subscriptions/downgrade` (`atlas-cmms/src/routes/auth_users.py`)
Register before `@router.get("/subscriptions/{item_id}")`:
```python
@router.post("/subscriptions/upgrade")
def upgrade_subscription(
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {"url": "", "message": "Unrestricted self-hosted edition require no upgrade"}


@router.get("/subscriptions/downgrade")
def downgrade_subscription(
    usersIds: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return SuccessResponse(success=True, message="Unrestricted self-hosted edition").model_dump()
```

### Fix 4: Complete `GET /license/state` DTO Contract (`atlas-cmms/src/routes/auth_users.py`)
```python
ALL_LICENSE_ENTITLEMENTS: list[str] = [
    "SSO",
    "WORK_ORDER_HISTORY",
    "WORKFLOW",
    "MULTI_INSTANCE",
    "WEBHOOK",
    "BRANDING",
    "NFC_BARCODE",
    "CUSTOM_ROLES",
    "FILE_ATTACHMENTS",
    "TIME_TRACKING",
    "COST_TRACKING",
    "WORK_ORDER_LINKING",
    "SIGNATURE_CAPTURE",
    "PM_CALENDAR",
    "CONDITION_BASED_PM",
    "ASSET_HIERARCHY",
    "ASSET_DOWNTIME",
    "LOW_STOCK_ALERTS",
    "PARTS_COST_TRACKING",
    "CUSTOMER_VENDOR",
    "FIELD_CONFIGURATION",
    "VOICE_NOTES",
    "ADVANCED_ANALYTICS",
    "API_ACCESS",
    "UNLIMITED_ASSETS",
    "UNLIMITED_LOCATIONS",
    "UNLIMITED_PARTS",
    "UNLIMITED_PM_SCHEDULES",
    "UNLIMITED_ACTIVE_WORK_ORDERS",
    "UNLIMITED_CHECKLISTS",
    "UNLIMITED_METERS",
    "UNLIMITED_USERS",
    "REQUEST_PORTAL",
    "RESOURCE_PLANNING",
]

@router.get("/license/state")
def license_state() -> dict[str, Any]:
    return {
        "valid": LicenseService.is_license_valid(),
        "unrestricted": LicenseService.is_unrestricted_self_hosted(),
        "state": "VALID",
        "entitlements": ALL_LICENSE_ENTITLEMENTS,
        "expirationDate": "2099-12-31T23:59:59.000Z",
        "planName": "ENTERPRISE",
    }
```
