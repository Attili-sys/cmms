"""Generic SQLAlchemy model serializer and hydration helpers matching Spring Jackson DTOs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from pydantic.alias_generators import to_camel

from src.models import enums as model_enums
from src.utils.dates import to_iso_utc

# Map column names to their Java enum classes when stored as SmallInteger ordinals
_RAW_ENUM_MAP: dict[str, str] = {
    "status": "Status",
    "priority": "Priority",
    "role_type": "RoleType",
    "code": "RoleCode",
    "language": "Language",
    "date_format": "DateFormat",
    "business_type": "BusinessType",
    "type": "TaskType",
    "task_type": "TaskType",
    "notification_type": "NotificationType",
    "recurrence_type": "RecurrenceType",
    "recurrence_based_on": "RecurrenceBasedOn",
    "time_status": "TimeStatus",
    "approval_status": "ApprovalStatus",
    "field_type": "FieldType",
    "asset_status": "AssetStatus",
    "import_entity": "ImportEntity",
    "main_condition": "WFMainCondition",
    "action": "WFAction",
}
COLUMN_ENUM_MAP: dict[str, type[Enum]] = {
    k: getattr(model_enums, v) for k, v in _RAW_ENUM_MAP.items() if hasattr(model_enums, v)
}



def resolve_enum_value(col_name: str, val: Any, model_cls_name: str = "") -> Any:
    if val is None or not isinstance(val, int) or isinstance(val, bool):
        return val

    # Special cases by model class name
    if model_cls_name == "Asset" and col_name == "status":
        members = list(model_enums.AssetStatus)
        return members[val].value if 0 <= val < len(members) else val
    if model_cls_name == "PurchaseOrder" and col_name == "status":
        members = list(model_enums.ApprovalStatus)
        return members[val].value if 0 <= val < len(members) else val
    if model_cls_name == "Labor" and col_name == "status":
        members = list(model_enums.TimeStatus)
        return members[val].value if 0 <= val < len(members) else val
    if model_cls_name == "Relation" and col_name == "relation_type":
        members = list(model_enums.RelationType)
        return members[val].value if 0 <= val < len(members) else val
    if model_cls_name == "WorkflowCondition":
        if col_name == "work_order_condition":
            members = list(model_enums.WorkOrderCondition)
            return members[val].value if 0 <= val < len(members) else val
        if col_name == "request_condition":
            members = list(model_enums.RequestCondition)
            return members[val].value if 0 <= val < len(members) else val
        if col_name == "purchase_order_condition":
            members = list(model_enums.PurchaseOrderCondition)
            return members[val].value if 0 <= val < len(members) else val
        if col_name == "part_condition":
            members = list(model_enums.PartCondition)
            return members[val].value if 0 <= val < len(members) else val
        if col_name == "task_condition":
            members = list(model_enums.TaskCondition)
            return members[val].value if 0 <= val < len(members) else val

    enum_cls = COLUMN_ENUM_MAP.get(col_name)
    if enum_cls is not None:
        members = list(enum_cls)
        if 0 <= val < len(members):
            return members[val].value
    return val


def serialize_value(val: Any) -> Any:
    if isinstance(val, datetime):
        return to_iso_utc(val)
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, Enum):
        return val.value
    return val


_MODEL_DEFAULT_LISTS: dict[str, tuple[str, ...]] = {
    "WorkOrder": ("assignedTo", "customers", "files", "customFieldValues"),
    "PreventiveMaintenance": ("assignedTo", "customers", "files", "customFieldValues"),
    "Request": ("assignedTo", "customers", "files", "customFieldValues"),
    "Asset": (
        "assignedTo",
        "customers",
        "vendors",
        "parts",
        "files",
        "teams",
        "customFieldValues",
    ),
    "Location": ("workers", "teams", "customers", "vendors", "files", "customFieldValues"),
    "Part": (
        "assignedTo",
        "customers",
        "vendors",
        "files",
        "teams",
        "locations",
        "customFieldValues",
    ),
    "Meter": ("users", "locations", "customFieldValues"),
    "PurchaseOrder": ("partQuantities", "customFieldValues"),
    "Vendor": ("files", "customFieldValues"),
    "Customer": ("files", "customFieldValues"),
    "CustomField": ("options",),
    "Task": ("images",),
    "TaskBase": ("options",),
    "Checklist": ("taskBases",),
    "Comment": ("files",),
    "Team": ("users",),
    "MultiParts": ("parts",),
    "Schedule": ("daysOfWeek",),
}


def _hydrate_foreign_key(target_table: str | None, raw_val: Any, db: Session | None) -> dict[str, Any]:
    """Hydrate a foreign key ID into the expected mini-DTO dictionary when db session is available."""
    if db is None or not target_table or raw_val is None:
        return {"id": raw_val}

    try:
        if target_table == "location":
            from src.models.location_asset import Location

            loc = db.get(Location, raw_val)
            if loc:
                return {
                    "id": loc.id,
                    "name": loc.name,
                    "address": loc.address,
                    "customId": loc.custom_id,
                }
        elif target_table == "asset":
            from src.models.location_asset import Asset

            asset = db.get(Asset, raw_val)
            if asset:
                return {
                    "id": asset.id,
                    "name": asset.name,
                    "customId": asset.custom_id,
                    "status": resolve_enum_value("status", asset.status, "Asset"),
                }
        elif target_table == "own_user":
            from src.models.users import User

            u = db.get(User, raw_val)
            if u:
                return {
                    "id": u.id,
                    "firstName": u.first_name,
                    "lastName": u.last_name,
                    "email": u.email,
                    "jobTitle": u.job_title,
                    "hourlyRate": u.rate,
                }
        elif target_table == "team":
            from src.models.users import Team

            t = db.get(Team, raw_val)
            if t:
                return {"id": t.id, "name": t.name, "description": t.description}
        elif target_table == "vendor":
            from src.models.parts_po import Vendor

            v = db.get(Vendor, raw_val)
            if v:
                return {
                    "id": v.id,
                    "name": v.name,
                    "companyName": v.company_name,
                    "email": v.email,
                    "phone": v.phone,
                    "vendorType": v.vendor_type,
                }
        elif target_table == "customer":
            from src.models.parts_po import Customer

            c = db.get(Customer, raw_val)
            if c:
                return {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "customerType": c.customer_type,
                }
        elif target_table == "file":
            from src.models.files_custom import File

            f = db.get(File, raw_val)
            if f:
                return {
                    "id": f.id,
                    "name": f.name,
                    "url": f.url,
                    "type": resolve_enum_value("type", f.type, "File"),
                }
        elif target_table == "part":
            from src.models.parts_po import Part

            p = db.get(Part, raw_val)
            if p:
                return {
                    "id": p.id,
                    "name": p.name,
                    "cost": p.cost,
                    "quantity": p.quantity,
                    "minQuantity": p.min_quantity,
                    "unit": p.unit,
                    "barcode": p.barcode,
                    "area": p.area,
                    "description": p.description,
                    "nonStock": p.non_stock,
                }
        elif target_table == "meter":
            from src.models.meters import Meter

            m = db.get(Meter, raw_val)
            if m:
                return {
                    "id": m.id,
                    "name": m.name,
                    "unit": m.unit,
                    "updateFrequency": m.update_frequency,
                }
        elif target_table == "role":
            from src.models.users import Role

            r = db.get(Role, raw_val)
            if r:
                return {
                    "id": r.id,
                    "name": r.name,
                    "code": resolve_enum_value("code", r.code, "Role"),
                    "roleType": resolve_enum_value("role_type", r.role_type, "Role"),
                }
        elif target_table == "currency":
            from src.models.company import Currency

            cur = db.get(Currency, raw_val)
            if cur:
                return {"id": cur.id, "name": cur.name, "code": cur.code}
        elif target_table == "work_order":
            from src.models.work_orders import WorkOrder

            wo = db.get(WorkOrder, raw_val)
            if wo:
                return {
                    "id": wo.id,
                    "title": wo.title,
                    "customId": wo.custom_id,
                    "status": resolve_enum_value("status", wo.status, "WorkOrder"),
                    "priority": resolve_enum_value("priority", wo.priority, "WorkOrder"),
                }
        elif target_table.endswith("_category"):
            from src.models import categories as cat_models

            cat_map = {
                "asset_category": cat_models.AssetCategory,
                "meter_category": cat_models.MeterCategory,
                "part_category": cat_models.PartCategory,
                "purchase_order_category": cat_models.PurchaseOrderCategory,
                "work_order_category": cat_models.WorkOrderCategory,
                "cost_category": cat_models.CostCategory,
                "time_category": cat_models.TimeCategory,
            }
            cat_cls = cat_map.get(target_table)
            if cat_cls is not None:
                cat = db.get(cat_cls, raw_val)
                if cat:
                    return {
                        "id": cat.id,
                        "name": cat.name,
                        "description": getattr(cat, "description", None),
                    }
    except Exception:
        return {"id": raw_val}

    return {"id": raw_val}


def model_to_dict(
    obj: Any,
    db: Session | None = None,
    exclude: set[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert a SQLAlchemy model instance into a camelCase JSON-ready dictionary."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj

    exclude_cols = {"password"} | (exclude or set())
    mapper = inspect(obj.__class__, raiseerr=False)
    cls_name = obj.__class__.__name__
    result: dict[str, Any] = {}

    if mapper is not None:
        for attr in mapper.column_attrs:
            key = attr.key
            if key in exclude_cols:
                continue
            raw_val = getattr(obj, key, None)
            resolved_val = resolve_enum_value(key, raw_val, cls_name)
            camel_key = to_camel(key)
            result[camel_key] = serialize_value(resolved_val)

            # Expose hydrated nested mini-DTO for *_id foreign keys
            if (
                key.endswith("_id")
                and key not in ("company_id", "custom_id")
                and raw_val is not None
            ):
                rel_name = key[:-3]
                camel_rel = to_camel(rel_name)
                if camel_rel not in result:
                    col = mapper.columns.get(key)
                    target_table = (
                        next(iter(col.foreign_keys)).column.table.name
                        if (col is not None and col.foreign_keys)
                        else None
                    )
                    result[camel_rel] = _hydrate_foreign_key(target_table, raw_val, db)
    else:
        for k, v in vars(obj).items():
            if not k.startswith("_") and k not in exclude_cols:
                result[to_camel(k)] = serialize_value(v)

    for list_field in _MODEL_DEFAULT_LISTS.get(cls_name, ()):
        result.setdefault(list_field, [])

    if extra:
        for k, v in extra.items():
            result[k] = v

    return result


def apply_patch(
    obj: Any,
    payload: dict[str, Any],
    exclude: set[str] | None = None,
) -> Any:
    """Apply a camelCase or snake_case dict payload onto a SQLAlchemy model instance."""
    from src.utils.search import camel_to_snake

    ignore = {"id", "company_id", "created_at", "created_by"} | (exclude or set())
    cls_name = obj.__class__.__name__
    mapper = inspect(obj.__class__, raiseerr=False)
    valid_cols = {attr.key for attr in mapper.column_attrs} if mapper else set()

    for key, val in payload.items():
        snake_key = camel_to_snake(key)
        if snake_key in ignore:
            continue

        # Handle nested object references like {"asset": {"id": 5}} -> asset_id = 5
        if isinstance(val, dict) and "id" in val:
            fk_key = f"{snake_key}_id"
            if fk_key in valid_cols or hasattr(obj, fk_key):
                setattr(obj, fk_key, val["id"])
                continue

        target_col = None
        if snake_key in valid_cols or hasattr(obj, snake_key):
            target_col = snake_key
        elif key in valid_cols or hasattr(obj, key):
            target_col = key

        if target_col:
            # Coerce string enum to ordinal if column is integer/smallint
            coerced = _coerce_for_column(obj, target_col, val, cls_name)
            setattr(obj, target_col, coerced)

    return obj


def _coerce_for_column(obj: Any, col_name: str, val: Any, cls_name: str) -> Any:
    if val is None:
        return None
    if isinstance(val, str):
        # Check if string is an ISO datetime when column expects datetime
        mapper = inspect(obj.__class__, raiseerr=False)
        if mapper and col_name in mapper.columns:
            col_type = mapper.columns[col_name].type.__class__.__name__.lower()
            if "date" in col_type or "time" in col_type:
                from src.utils.dates import parse_iso_datetime

                parsed = parse_iso_datetime(val)
                if parsed is not None:
                    return parsed.replace(tzinfo=None)
            if "smallinteger" in col_type or "integer" in col_type:
                # Try enum lookup
                enum_cls = COLUMN_ENUM_MAP.get(col_name)
                if cls_name == "Asset" and col_name == "status":
                    enum_cls = model_enums.AssetStatus
                elif cls_name == "PurchaseOrder" and col_name == "status":
                    enum_cls = model_enums.ApprovalStatus
                elif cls_name == "Labor" and col_name == "status":
                    enum_cls = model_enums.TimeStatus
                elif cls_name == "Relation" and col_name == "relation_type":
                    enum_cls = model_enums.RelationType

                if enum_cls is not None:
                    members = list(enum_cls)
                    for idx, m in enumerate(members):
                        if m.name == val or m.value == val:
                            return idx
                try:
                    return int(val)
                except ValueError:
                    pass
    return val
