# Database Architecture & Schema Reference (`atlas-cmms/`)

This document is the authoritative reference for the PostgreSQL / SQLAlchemy 2.0 database layer in `atlas-cmms/` (deployed on Canvas as **`aj-cafm`**).

---

## 1. Overview

- **ORM & Driver:** SQLAlchemy 2.0 (`DeclarativeBase` in [`src/models/_base.py`](src/models/_base.py)) using `postgresql+psycopg://` via `ajnkit.db` in production and SQLite (`StaticPool`) in unit/contract tests.
- **Schema Footprint:**
  - **72 ORM Entity Models** across 15 domain modules under [`src/models/`](src/models/__init__.py)
  - **53 Association & `@ElementCollection` Tables** in [`src/models/associations.py`](src/models/associations.py)
  - **44 Ported Java Enums** in [`src/models/enums.py`](src/models/enums.py)
- **Migrations:** Managed by Alembic under [`migrations/`](migrations/env.py) (`0001_initial_schema.py`). Executed automatically by `run.py` on container startup when `DATABASE_URL` is set.
- **Schema Parity Test:** [`tests/test_schema_matches_dump.py`](tests/test_schema_matches_dump.py) verifies that the SQLAlchemy metadata matches the legacy Liquibase/PostgreSQL schema dump.

---

## 2. Base Mixins, Sequences & Default Hooks (`src/models/_base.py`)

### 2.1 Audit & Tenant Mixins

Every entity inherits from one of three base mixins mirroring the legacy Spring JPA `@MappedSuperclass` hierarchy:

| Mixin | Columns Added | Notes |
|---|---|---|
| `DateAuditMixin` | `created_at` (`DateTime`, `NOT NULL`), `updated_at` (`DateTime`, `NOT NULL`) | UTC timestamps auto-populated on insert/update. |
| `AuditMixin` | `DateAuditMixin` + `created_by` (`FK -> own_user.id`, `ON DELETE SET NULL`), `updated_by` (`FK -> own_user.id`, `ON DELETE SET NULL`) | Tracks the user who created or last modified the record. |
| `CompanyAuditMixin` | `AuditMixin` + `company_id` (`FK -> company.id`, `ON DELETE CASCADE`, `NOT NULL`) | Primary multi-tenant isolation key for company-owned entities. |

> **Important Scoping Note (`company_id` vs `company_settings_id`):**
> While most operational tables (`work_order`, `asset`, `location`, `part`, `meter`, `request`, `preventive_maintenance`, etc.) inherit `CompanyAuditMixin` and filter by `company_id`, configuration and catalog tables (`role`, `checklist`, `work_order_category`, `asset_category`, `meter_category`, `part_category`, `purchase_order_category`, `cost_category`, `time_category`) are scoped by **`company_settings_id`** (`FK -> company_settings.id`). Both [`src/routes/_crud.py`](src/routes/_crud.py) and `assert_company_access` handle both scoping patterns automatically.

### 2.2 Primary Key Sequences (`pk_seq`)

To maintain 100% compatibility with Hibernate sequence allocation:
- Most tables use `id = pk_seq("<table_name>_seq", increment=50)` or `mapped_column(BigInteger, primary_key=True, autoincrement=True)`.
- A custom `@compiles(BigInteger, "sqlite")` hook in [`src/models/_base.py`](src/models/_base.py) compiles `BigInteger` to SQLite `INTEGER` so autoincrement primary keys work identically in SQLite test runs.

### 2.3 Java Primitive Default Hook (`_apply_java_primitive_defaults`)

In Java/Hibernate, uninitialized primitive fields on JPA entities (`boolean`, `int`, `long`, `double`, `float`) automatically default to `false`, `0`, or `0.0` before `INSERT`.
- [`_apply_java_primitive_defaults`](src/models/_base.py) is registered on `Base` for the SQLAlchemy `before_insert` event (`propagate=True`) and sets non-nullable primitive columns (`Boolean -> False`, `Integer/SmallInteger/BigInteger -> 0`, `Float/Numeric -> 0.0`, `DateTime -> utcnow()`) when omitted by the caller.
- [`apply_model_defaults`](src/routes/_crud.py) in `src/routes/_crud.py` applies business-specific defaults (e.g., `include_to_total_cost=True`, `include_to_total_time=True`, `logged=True`, `enabled=True`, `frequency=1`, `update_frequency=1`) prior to flush.

---

## 3. Enum Storage Semantics (`src/models/enums.py`)

Legacy Hibernate mapped `@Enumerated` fields in two different ways depending onwhether `@Enumerated(EnumType.STRING)` was present in Java:

1. **`OrdinalEnum(TypeDecorator)` (`SMALLINT` in PostgreSQL):**
   - Stores the 0-based declaration index of the enum in PostgreSQL (`0, 1, 2, ...`), while exposing the `StrEnum` string value in Python and JSON responses.
   - Used for columns such as `WorkOrder.status` (`0="OPEN"`, `1="IN_PROGRESS"`, `2="ON_HOLD"`, `3="COMPLETE"`), `WorkOrder.priority` (`0="NONE"`, `1="LOW"`, `2="MEDIUM"`, `3="HIGH"`), `Asset.status` (`0="OPERATIONAL"`, `1="DOWN"`, etc.), `TaskBase.task_type`, `Role.role_type`, `Role.code`, `GeneralPreferences.language`, `GeneralPreferences.date_format`, `GeneralPreferences.business_type`.
   - Also mapped in [`_RAW_ENUM_MAP`](src/services/serializer.py) inside `src/services/serializer.py` so raw integer columns are always serialized as their string enum name (e.g. `"OPERATIONAL"`, `"OPEN"`, `"HIGH"`) and accepted as either string names or integers in `apply_patch()`.

2. **`StringEnum(TypeDecorator)` / `String(255)` (`VARCHAR` in PostgreSQL):**
   - Stores the string name directly in PostgreSQL.
   - **Critical Example — `Schedule`:** In [`src/models/pm_schedule.py`](src/models/pm_schedule.py), `Schedule.recurrence_type` (`"DAILY"`, `"WEEKLY"`, `"MONTHLY"`, `"YEARLY"`) and `Schedule.recurrence_based_on` (`"SCHEDULED_DATE"`, `"COMPLETED_DATE"`) are `String(255)` columns (`NOT NULL`), **not** integer ordinals, and `Schedule` does **not** have a `company_id` column (it links to `PreventiveMaintenance` via `preventive_maintenance_id`).

---

## 4. Domain Model Catalog (`src/models/`)

### 4.1 Company, Licensing & Settings (`company.py`, `settings.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `Company` | `company` | `id` (root) | Organization record (`name`, `address`, `phone`, `website`, `logo_id`, `company_settings_id`, `subscription_id`). |
| `Currency` | `currency` | Global | Currency catalog (`id`, `code`, `name`). |
| `SubscriptionPlan` | `subscription_plan` | Global | Subscription tier definition. In unrestricted self-hosted mode, always exposes all `PlanFeatures`. |
| `Subscription` | `subscription` | `company` (1:1) | Active subscription linked to `Company`. |
| `SubscriptionChangeRequest` | `subscription_change_request` | — | Legacy subscription change tracking. |
| `CompanySettings` | `company_settings` | `company_id` | Container linking `GeneralPreferences`, `WorkOrderConfiguration`, `WorkOrderRequestConfiguration`, `UiConfiguration`, and `ShiftConfiguration`. |
| `GeneralPreferences` | `general_preferences` | `company_settings_id` | Language, timezone, date format, currency, auto-assign rules, PM notification lead days. |
| `WorkOrderConfiguration` | `work_order_configuration` | `company_settings_id` | Work order form rules and field configurations. |
| `WorkOrderRequestConfiguration` | `work_order_request_configuration` | `company_settings_id` | Service request form rules and field configurations. |
| `FieldConfiguration` | `field_configuration` | `work_order_configuration_id` / `work_order_request_configuration_id` | Controls whether each form field (`description`, `asset`, `priority`, `dueDate`, etc.) is `OPTIONAL`, `REQUIRED`, or `HIDDEN`. |
| `UiConfiguration` | `ui_configuration` | `company_settings_id` | Sidebar/feature visibility toggles (`requests`, `preventive_maintenance`, `locations`, `assets`, `parts_and_inventory`, `purchase_orders`, `meters`, `people_and_teams`, `vendors_and_customers`). |
| `ShiftConfiguration` | `shift_configuration` | `company_settings_id` | Working hours and shift availability for workload planning. |
| `CustomSequence` | `custom_sequence` | `company_id` | Per-company sequence counters for `WO000001`, `PM000001`, etc. |

### 4.2 Users, RBAC Roles & Teams (`users.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `User` | `own_user` | `company_id` | User account (`email`, `first_name`, `last_name`, `phone`, `job_title`, `rate`, `role_id`, `image_id`, `enabled`, `owns_company`, `ui_configuration_id`). Note table name is **`own_user`** (since `user` is reserved in PostgreSQL). |
| `Role` | `role` | `company_settings_id` | RBAC role (`name`, `code`, `role_type`, `paid`). Permissions are stored in 5 association tables (`role_create_permissions`, `role_view_permissions`, `role_view_other_permissions`, `role_edit_other_permissions`, `role_delete_other_permissions`). |
| `Team` | `team` | `company_id` | Maintenance team (`name`, `description`). Members linked via `t_team_user_associations`. |
| `UserSettings` | `user_settings` | 1:1 with `own_user` | Personal email/notification preferences (`email_notified`, `email_updates_for_work_orders`, etc.). |
| `UserInvitation` | `user_invitation` | `role_id` / `user_id` | Pending invitation records. |
| `SuperAccountRelation` | `super_account_relation` | `super_user_id` / `child_user_id` | Links a super-admin user to child accounts across companies. |
| `UserAppStats` | `user_app_stats` | 1:1 with `own_user` | Mobile/app login statistics. |
| `VerificationToken` | `verification_token` | `user_id` | Email verification / password reset token. |
| `RefreshToken` | `refresh_token` | `user_id` | JWT refresh token storage. |
| `PushNotificationToken` | `push_notification_token` | `user_id` | Expo/Firebase mobile push token. |

### 4.3 Locations & Assets (`location_asset.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `Location` | `location` | `company_id` | Physical site/building/room (`name`, `address`, `longitude`, `latitude`, `parent_location_id`, `image_id`, `custom_id`). Supports recursive hierarchy via `parent_location_id`. |
| `FloorPlan` | `floor_plan` | `location_id` | Floor plan image and area attached to a `Location`. |
| `Asset` | `asset` | `company_id` | Equipment or machine (`name`, `description`, `model`, `serial_number`, `bar_code`, `status`, `area`, `acquisition_cost`, `in_service_date`, `warranty_expiration_date`, `location_id`, `parent_asset_id`, `category_id`, `primary_user_id`, `image_id`, `custom_id`). Supports recursive hierarchy via `parent_asset_id`. |
| `AssetDowntime` | `asset_downtime` | `company_id` | Downtime intervals (`starts_on`, `duration`, `downtime_reason`, `asset_id`). `duration=0` indicates an ongoing downtime. |
| `Deprecation` | `deprecation` | `company_id` | Asset financial depreciation schedule. |

### 4.4 Work Orders, Preventive Maintenance & Schedules (`work_orders.py`, `pm_schedule.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `WorkOrder` | `work_order` | `company_id` | Maintenance work order (`title`, `description`, `priority`, `status`, `due_date`, `estimated_start_date`, `estimated_duration`, `completed_on`, `completed_by_id`, `asset_id`, `location_id`, `primary_user_id`, `team_id`, `category_id`, `image_id`, `signature_id`, `parent_preventive_maintenance_id`, `parent_request_id`, `feedback`, `required_signature`, `archived`, `custom_id`). |
| `WorkOrderHistory` | `work_order_history` | `company_id` | Audit log of changes to a `WorkOrder` (`name`, `work_order_id`, `user_id`). |
| `Labor` | `labor` | `company_id` | Time tracking entry on a `WorkOrder` (`duration`, `hourly_rate`, `started_at`, `status`, `include_to_total_time`, `user_id`, `work_order_id`, `time_category_id`). |
| `Relation` | `relation` | `company_id` | Directional link between two work orders (`parent_id`, `child_id`, `relation_type`). |
| `Comment` | `comment` | `company_id` | Discussion comment on a work order (`text`, `work_order_id`). Attached files via `comment_files`. |
| `PreventiveMaintenance` | `preventive_maintenance` | `company_id` | Recurring maintenance template (`name`, `title`, `description`, `priority`, `estimated_duration`, `asset_id`, `location_id`, `primary_user_id`, `team_id`, `category_id`, `schedule_id`, `custom_id`). |
| `Schedule` | `schedule` | `preventive_maintenance_id` | Recurrence schedule for a `PreventiveMaintenance` (`starts_on`, `ends_on`, `frequency`, `due_date_delay`, `disabled`, `recurrence_type`, `recurrence_based_on`). Days of week stored in `schedule_days_of_week`. |

### 4.5 Tasks & Checklists (`tasks.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `Checklist` | `checklist` | `company_settings_id` | Reusable template of tasks (`name`, `description`). Linked to `TaskBase` via `checklist_task_bases`. |
| `TaskBase` | `task_base` | `company_id` | Task definition (`label`, `task_type`, `user_id`, `asset_id`, `meter_id`). |
| `TaskOption` | `task_option` | `company_id` | Choice option for `MULTIPLE` / `INSPECTION` tasks (`label`, `task_base_id`). Note column is **`label`** (not `value`). |
| `Task` | `task` | `company_id` | Instantiated task on a `WorkOrder` or `PreventiveMaintenance` (`task_base_id`, `work_order_id`, `preventive_maintenance_id`, `value`, `notes`). |

### 4.6 Parts, Inventory, Purchase Orders, Vendors & Customers (`parts_po.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `Part` | `part` | `company_id` | Spare part / inventory item (`name`, `description`, `barcode`, `cost`, `quantity`, `min_quantity`, `non_stock`, `area`, `unit`, `category_id`, `image_id`, `custom_id`). |
| `MultiParts` | `multi_parts` | `company_id` | Set/bundle of parts (`name`). Linked to `Part` via `t_multi_parts_part_associations`. |
| `PartQuantity` | `part_quantity` | `company_id` | Quantity of a `Part` allocated to a `Part`, `PurchaseOrder`, or `WorkOrder` (`part_id`, `purchase_order_id`, `work_order_id`, `quantity`). |
| `PartTransaction` | `part_transaction` | `company_id` | Inventory consumption/addition log. |
| `PurchaseOrder` | `purchase_order` | `company_id` | Purchase order (`name`, `status`, `shipping_due_date`, `shipping_Additional_detail`, `vendor_id`, `category_id`, `company_id`). |
| `AdditionalCost` | `additional_cost` | `company_id` | Non-part/non-labor cost on a `WorkOrder` (`description`, `cost`, `include_to_total_cost`, `work_order_id`, `assigned_to_id`, `category_id`). |
| `Vendor` | `vendor` | `company_id` | External supplier/contractor (`company_name`, `name`, `address`, `phone`, `email`, `website`, `vendor_type`, `rate`, `description`, `custom_id`). |
| `Customer` | `customer` | `company_id` | Client/customer (`name`, `address`, `phone`, `email`, `website`, `customer_type`, `rate`, `description`, `billing_name`, `billing_address`, `custom_id`). |

### 4.7 Meters, Requests, Workflows, Categories, Files & Audit (`meters.py`, `requests.py`, `workflows.py`, `categories.py`, `files_custom.py`, `integrations.py`, `envers.py`)

| ORM Class | SQL Table | Tenant Key | Purpose |
|---|---|---|---|
| `Meter` | `meter` | `company_id` | Sensor/gauge (`name`, `unit`, `update_frequency`, `next_reading`, `asset_id`, `location_id`, `meter_category_id`, `image_id`). |
| `Reading` | `reading` | `company_id` | Timestamped meter measurement (`value`, `meter_id`). |
| `WorkOrderMeterTrigger` | `work_order_meter_trigger` | `company_id` | Rule that triggers a `WorkOrder` when a `Meter` reading crosses `value` (`trigger_condition`, `meter_id`). |
| `Request` | `request` | `company_id` | Maintenance service request (`title`, `description`, `priority`, `due_date`, `asset_id`, `location_id`, `primary_user_id`, `team_id`, `category_id`, `work_order_id`, `cancelled`, `cancellation_reason`, `custom_id`). |
| `RequestPortal` / `RequestPortalField` | `request_portal`, `request_portal_field` | `company_id` | Public/internal portal configuration for submitting requests. |
| `Workflow` / `WorkflowCondition` / `WorkflowAction` | `workflow`, `workflow_condition`, `workflow_action` | `company_id` | Event-driven automation rules on Work Orders, Requests, Purchase Orders, Parts, and Tasks. |
| `*Category` (7 tables) | `work_order_category`, `asset_category`, `meter_category`, `part_category`, `purchase_order_category`, `cost_category`, `time_category` | `company_settings_id` | Taxonomies for Work Orders, Assets, Meters, Parts, Purchase Orders, Additional Costs, and Labor Time. |
| `File` | `file` | `company_id` | Uploaded attachment metadata (`name`, `path`, `file_type`, `task_id`). |
| `CustomField` / `CustomFieldValue` | `custom_field`, `custom_field_value` | `company_id` | User-defined custom fields and values on entities. |
| `Notification` | `notification` | `user_id` | In-app notification feed item (`message`, `notification_type`, `resource_id`, `seen`). |
| `ApiKey` / `WebhookEndpoint` / `KeygenRequestTracker` | `api_key`, `webhook_endpoint`, `keygen_request_tracker` | `company_id` | External API keys and outgoing webhook subscriptions. |
| `RevInfo` / `WorkOrderAud` | `revinfo`, `work_order_aud` | — | Hibernate Envers historical revision tables. |

---

## 5. First-Sign-In Auto-Provisioning (`src/deps/current_user.py`)

When an authenticated Canvas SSO user (`X-authentik-email`) accesses `aj-cafm` on a fresh database:
1. [`get_current_user`](src/deps/current_user.py) creates the default `Company` (`"AJ CAFM"`), `Currency` (`"$"` / `"USD"`), `SubscriptionPlan` (`"SELF_HOSTED"`), and `Subscription`.
2. [`_ensure_company_settings`](src/deps/current_user.py) provisions:
   - `CompanySettings`
   - `GeneralPreferences`
   - `WorkOrderConfiguration` + **18 default `FieldConfiguration` rows** (`DEFAULT_WO_FIELDS`)
   - `WorkOrderRequestConfiguration` + **6 default `FieldConfiguration` rows** (`DEFAULT_WOR_FIELDS`)
   - `UiConfiguration` (all modules enabled)
3. Provisions the default `Role` (`ROLE_SUPER_ADMIN`, `RoleCode.ADMIN`) with all `PermissionEntity` permissions (`create`, `view`, `view_other`, `edit_other`, `delete_other`).
4. Creates the `User` (`own_user`) and `UserSettings` linked to the company and role.
