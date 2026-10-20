"""Generic CRUD router factory for Company-scoped entities matching Spring controllers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models.company import Company
from src.models.settings import CompanySettings
from src.models.users import User
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict
from src.utils.search import SearchCriteria, execute_search


def apply_model_defaults(obj: Any) -> None:
    """Ensure non-nullable boolean/numeric columns have sensible defaults when omitted by frontend."""
    bool_defaults = {
        "is_demo": False,
        "archived": False,
        "required_signature": False,
        "cancelled": False,
        "non_stock": False,
        "include_to_total_cost": True,
        "include_to_total_time": True,
        "logged": True,
        "disabled": False,
        "recurrent": False,
        "required": False,
        "copy_on_repeat": False,
        "enabled": True,
        "hidden": False,
        "seen": False,
    }
    num_defaults: dict[str, int | float] = {
        "estimated_duration": 0.0,
        "cost": 0.0,
        "min_quantity": 0.0,
        "quantity": 0.0,
        "version": 0,
        "rate": 0,
        "duration": 0,
        "hourly_rate": 0,
        "frequency": 1,
        "update_frequency": 1,
        "trigger_condition": 0,
        "value": 0,
        "wait_before": 0,
        "field_order": 0,
        "current_value": 0,
        "purchase_price": 0,
        "area": 0,
    }
    for attr_name, default_val in bool_defaults.items():
        if hasattr(obj, attr_name) and getattr(obj, attr_name, None) is None:
            setattr(obj, attr_name, default_val)
    for attr_name, default_val in num_defaults.items():
        if hasattr(obj, attr_name) and getattr(obj, attr_name, None) is None:
            # Only set numeric default if column is non-nullable (e.g. FloorPlan.area vs Asset.area)
            col = obj.__class__.__table__.columns.get(attr_name) if hasattr(obj.__class__, "__table__") else None
            if col is not None and not col.nullable:
                setattr(obj, attr_name, default_val)
    if hasattr(obj, "company_name") and getattr(obj, "company_name", None) is None:
        obj.company_name = getattr(obj, "name", None) or "Vendor"
    if hasattr(obj, "path") and getattr(obj, "path", None) is None and hasattr(obj, "url"):
        obj.path = getattr(obj, "url", None) or "/media/file"


def _ensure_company_settings_id(current_user: User, db: Session) -> int:
    comp = db.get(Company, current_user.company_id) if current_user.company_id else None
    if comp is not None and comp.company_settings_id is not None:
        cs = db.get(CompanySettings, comp.company_settings_id)
        if cs is not None:
            if cs.company_id is None:
                cs.company_id = comp.id
                db.flush()
            return cs.id
    cs = db.scalar(select(CompanySettings).where(CompanySettings.company_id == current_user.company_id))
    if cs is None:
        cs = CompanySettings(company_id=current_user.company_id)
        db.add(cs)
        db.flush()
    if comp is not None and comp.company_settings_id is None:
        comp.company_settings_id = cs.id
        db.flush()
    return cs.id


_get_user_company_settings_id = _ensure_company_settings_id


from src.deps.permissions import (  # noqa: E402
    can_create,
    can_delete_object,
    can_edit_object,
    can_view,
)
from src.models.enums import PermissionEntity  # noqa: E402

_MODEL_PERMISSION_MAP: dict[str, PermissionEntity] = {
    "Asset": PermissionEntity.ASSETS,
    "AssetDowntime": PermissionEntity.ASSETS,
    "Deprecation": PermissionEntity.ASSETS,
    "Location": PermissionEntity.LOCATIONS,
    "FloorPlan": PermissionEntity.LOCATIONS,
    "AssetCategory": PermissionEntity.CATEGORIES,
    "LocationCategory": PermissionEntity.CATEGORIES,
    "MeterCategory": PermissionEntity.CATEGORIES,
    "PartCategory": PermissionEntity.CATEGORIES,
    "PurchaseOrderCategory": PermissionEntity.CATEGORIES,
    "WorkOrderCategory": PermissionEntity.CATEGORIES,
    "CostCategory": PermissionEntity.CATEGORIES,
    "TimeCategory": PermissionEntity.CATEGORIES,
    "WorkOrder": PermissionEntity.WORK_ORDERS,
    "Task": PermissionEntity.WORK_ORDERS,
    "Labor": PermissionEntity.WORK_ORDERS,
    "AdditionalCost": PermissionEntity.WORK_ORDERS,
    "Relation": PermissionEntity.WORK_ORDERS,
    "PreventiveMaintenance": PermissionEntity.PREVENTIVE_MAINTENANCES,
    "Part": PermissionEntity.PARTS_AND_MULTIPARTS,
    "MultiParts": PermissionEntity.PARTS_AND_MULTIPARTS,
    "PurchaseOrder": PermissionEntity.PURCHASE_ORDERS,
    "Meter": PermissionEntity.METERS,
    "Reading": PermissionEntity.METERS,
    "WorkOrderMeterTrigger": PermissionEntity.METERS,
    "Vendor": PermissionEntity.VENDORS_AND_CUSTOMERS,
    "Customer": PermissionEntity.VENDORS_AND_CUSTOMERS,
    "File": PermissionEntity.FILES,
    "Request": PermissionEntity.REQUESTS,
    "Team": PermissionEntity.PEOPLE_AND_TEAMS,
    "Checklist": PermissionEntity.SETTINGS,
    "Workflow": PermissionEntity.SETTINGS,
    "CustomField": PermissionEntity.SETTINGS,
    "WebhookEndpoint": PermissionEntity.SETTINGS,
    "ApiKey": PermissionEntity.SETTINGS,
}


def validate_foreign_key_ownership(obj: Any, current_user: User, db: Session) -> None:
    """Verify every populated foreign key on obj belongs to current_user's tenant.

    Global tables without company_id or company_settings_id (currency, company_settings,
    subscription, subscription_plan) are skipped, and platform super-admins bypass tenant checks.
    """
    if current_user.company_id is None and is_super_admin(current_user, db):
        return
    table = getattr(obj.__class__, "__table__", None)
    if table is None:
        return

    cs_id: int | None = None
    for col in table.columns:
        if col.name in ("id", "company_id", "company_settings_id") or not col.foreign_keys:
            continue
        fk_val = getattr(obj, col.name, None)
        if fk_val is None:
            continue
        target_col = next(iter(col.foreign_keys)).column
        target_table = target_col.table

        has_company_id = "company_id" in target_table.c
        has_cs_id = "company_settings_id" in target_table.c
        if not has_company_id and not has_cs_id:
            # Global table (e.g. currency, company_settings, subscription)
            continue

        row = db.execute(select(target_table).where(target_table.c.id == fk_val)).mappings().first()
        if row is None:
            raise CustomException(status_code=404, message=f"Referenced {target_table.name} not found")

        if has_company_id:
            if row["company_id"] is not None and row["company_id"] != current_user.company_id:
                raise CustomException(
                    status_code=403,
                    message=f"Cross-tenant reference to {target_table.name} is forbidden",
                )
        elif has_cs_id:
            if cs_id is None:
                cs_id = _ensure_company_settings_id(current_user, db)
            if row["company_settings_id"] is not None and row["company_settings_id"] != cs_id:
                raise CustomException(
                    status_code=403,
                    message=f"Cross-tenant reference to {target_table.name} is forbidden",
                )


def _build_auxiliary_tenant_predicate(model_cls: type, company_id: int) -> Any:
    """Build a SQLAlchemy tenant-scoping predicate for auxiliary models lacking company_id."""
    from sqlalchemy import or_
    from src.models.meters import Meter
    from src.models.parts_po import PurchaseOrder
    from src.models.pm_schedule import PreventiveMaintenance
    from src.models.work_orders import WorkOrder

    preds: list[Any] = []
    if hasattr(model_cls, "work_order_id"):
        preds.append(
            model_cls.work_order_id.in_(
                select(WorkOrder.id).where(WorkOrder.company_id == company_id)
            )
        )
    if hasattr(model_cls, "purchase_order_id"):
        preds.append(
            model_cls.purchase_order_id.in_(
                select(PurchaseOrder.id).where(PurchaseOrder.company_id == company_id)
            )
        )
    if hasattr(model_cls, "preventive_maintenance_id"):
        preds.append(
            model_cls.preventive_maintenance_id.in_(
                select(PreventiveMaintenance.id).where(
                    PreventiveMaintenance.company_id == company_id
                )
            )
        )
        if model_cls.__name__ == "Schedule":
            preds.append(
                model_cls.id.in_(
                    select(PreventiveMaintenance.schedule_id).where(
                        PreventiveMaintenance.company_id == company_id,
                        PreventiveMaintenance.schedule_id.is_not(None),
                    )
                )
            )
    if hasattr(model_cls, "meter_id"):
        preds.append(
            model_cls.meter_id.in_(
                select(Meter.id).where(Meter.company_id == company_id)
            )
        )
    if not preds:
        return None
    return or_(*preds) if len(preds) > 1 else preds[0]


def _assert_entity_tenant_access(obj: Any, current_user: User, db: Session) -> None:
    if current_user.company_id is None and is_super_admin(current_user, db):
        return
    if hasattr(obj, "company_id") and getattr(obj, "company_id", None) is not None:
        assert_company_access(current_user, obj, is_super_admin=False, db=db)
    elif hasattr(obj, "company_settings_id") and getattr(obj, "company_settings_id", None) is not None:
        cs_id = _ensure_company_settings_id(current_user, db)
        if obj.company_settings_id != cs_id:
            raise CustomException(status_code=403, message="Access is denied")
    else:
        validate_foreign_key_ownership(obj, current_user, db)
        if obj.__class__.__name__ == "Schedule" and getattr(obj, "preventive_maintenance_id", None) is None:
            from src.models.pm_schedule import PreventiveMaintenance

            pm = db.scalar(
                select(PreventiveMaintenance).where(
                    PreventiveMaintenance.schedule_id == obj.id
                )
            )
            if pm is not None and pm.company_id != current_user.company_id:
                raise CustomException(
                    status_code=403,
                    message="Cross-tenant reference to preventive_maintenance is forbidden",
                )


def build_crud_router(
    prefix: str,
    model_cls: type,
    tags: list[str] | None = None,
    custom_serializer: Callable[[Any, Session], dict[str, Any]] | None = None,
    before_create: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
    after_create: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
    before_patch: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
    after_patch: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
    before_delete: Callable[[Any, User, Session], None] | None = None,
    permission_entity: PermissionEntity | str | None = None,
) -> APIRouter:
    """Create a standard Spring-compatible CRUD + /search router for model_cls."""
    router = APIRouter(prefix=prefix, tags=tags or [prefix.strip("/")])
    perm_entity = permission_entity or _MODEL_PERMISSION_MAP.get(model_cls.__name__)

    def _serialize(obj: Any, db: Session) -> dict[str, Any]:
        if custom_serializer is not None:
            return custom_serializer(obj, db)
        return model_to_dict(obj, db=db)

    @router.post("/search")
    def search_items(
        criteria: SearchCriteria = Body(default_factory=SearchCriteria),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        if perm_entity is not None and not can_view(current_user, perm_entity, db):
            raise CustomException(status_code=403, message="Access is denied")
        cs_id = (
            _ensure_company_settings_id(current_user, db)
            if hasattr(model_cls, "company_settings_id") and current_user.company_id is not None
            else None
        )
        return execute_search(
            db=db,
            model_cls=model_cls,
            criteria=criteria,
            company_id=current_user.company_id,
            company_settings_id=cs_id,
            serializer=lambda row: _serialize(row, db),
        )

    @router.get("")
    def list_items(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[dict[str, Any]]:
        if perm_entity is not None and not can_view(current_user, perm_entity, db):
            raise CustomException(status_code=403, message="Access is denied")
        stmt = select(model_cls)
        if hasattr(model_cls, "company_id") and current_user.company_id is not None:
            stmt = stmt.where(model_cls.company_id == current_user.company_id)
        elif hasattr(model_cls, "company_settings_id") and current_user.company_id is not None:
            cs_id = _ensure_company_settings_id(current_user, db)
            stmt = stmt.where(model_cls.company_settings_id == cs_id)
        elif current_user.company_id is not None:
            aux_pred = _build_auxiliary_tenant_predicate(model_cls, current_user.company_id)
            if aux_pred is not None:
                stmt = stmt.where(aux_pred)
        rows = db.scalars(stmt).all()
        return [_serialize(r, db) for r in rows]

    @router.post("")
    def create_item(
        payload: dict[str, Any] = Body(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        if perm_entity is not None and not can_create(current_user, perm_entity, db):
            raise CustomException(status_code=403, message="Access is denied")
        obj = model_cls()
        apply_patch(obj, payload)
        apply_model_defaults(obj)
        if hasattr(obj, "company_id") and getattr(obj, "company_id", None) is None:
            obj.company_id = current_user.company_id
        if hasattr(obj, "company_settings_id") and getattr(obj, "company_settings_id", None) is None:
            obj.company_settings_id = _ensure_company_settings_id(current_user, db)
        if hasattr(obj, "created_by") and getattr(obj, "created_by", None) is None:
            obj.created_by = current_user.id
        validate_foreign_key_ownership(obj, current_user, db)
        if before_create is not None:
            before_create(obj, payload, current_user, db)
            validate_foreign_key_ownership(obj, current_user, db)
        apply_model_defaults(obj)
        db.add(obj)
        db.flush()
        if after_create is not None:
            after_create(obj, payload, current_user, db)
        db.commit()
        db.refresh(obj)
        return _serialize(obj, db)

    @router.get("/{item_id:int}")
    def get_item(
        item_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        if perm_entity is not None and not can_view(current_user, perm_entity, db):
            raise CustomException(status_code=403, message="Access is denied")
        obj = db.get(model_cls, item_id)
        if obj is None:
            raise CustomException(status_code=404, message=f"{model_cls.__name__} not found")
        _assert_entity_tenant_access(obj, current_user, db)
        return _serialize(obj, db)

    @router.patch("/{item_id:int}")
    def patch_item(
        item_id: int,
        payload: dict[str, Any] = Body(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        obj = db.get(model_cls, item_id)
        if obj is None:
            raise CustomException(status_code=404, message=f"{model_cls.__name__} not found")
        _assert_entity_tenant_access(obj, current_user, db)
        if perm_entity is not None and not can_edit_object(current_user, perm_entity, obj, db):
            raise CustomException(status_code=403, message="Access is denied")
        if before_patch is not None:
            before_patch(obj, payload, current_user, db)
        apply_patch(obj, payload)
        validate_foreign_key_ownership(obj, current_user, db)
        if hasattr(obj, "updated_by"):
            obj.updated_by = current_user.id
        if after_patch is not None:
            after_patch(obj, payload, current_user, db)
        db.commit()
        db.refresh(obj)
        return _serialize(obj, db)

    @router.delete("/{item_id:int}")
    def delete_item(
        item_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        obj = db.get(model_cls, item_id)
        if obj is None:
            raise CustomException(status_code=404, message=f"{model_cls.__name__} not found")
        _assert_entity_tenant_access(obj, current_user, db)
        if perm_entity is not None and not can_delete_object(current_user, perm_entity, obj, db):
            raise CustomException(status_code=403, message="Access is denied")
        if before_delete is not None:
            before_delete(obj, current_user, db)
        db.delete(obj)
        db.commit()
        return SuccessResponse(success=True, message="Deleted successfully").model_dump()

    return router

