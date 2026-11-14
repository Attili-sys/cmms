"""Routes for Parts, PartQuantities, PartConsumption, MultiParts, PurchaseOrders, AdditionalCosts, Tasks, Checklists."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, Depends, Query
from pydantic import Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.deps.permissions import can_edit, can_edit_object, can_view
from src.models._base import utcnow
from src.models.enums import MovementType, PermissionEntity, WFMainCondition
from src.services.workflow_engine import (
    run_part_workflows,
    run_purchase_order_workflows,
    run_task_workflows,
)
from src.models.associations import (
    t_multi_parts_part_associations,
    t_part_customer_associations,
    t_part_file_associations,
    t_part_team_associations,
    t_part_user_associations,
    t_part_vendor_associations,
)
from src.models.files_custom import CustomFieldValue, File as FileEntity
from src.models.parts_po import (
    AdditionalCost,
    Customer,
    MultiParts,
    Part,
    PartQuantity,
    PartTransaction as PartConsumption,
    PurchaseOrder,
    Vendor,
)
from src.models.pm_schedule import PreventiveMaintenance
from src.models.tasks import Checklist, Task, TaskBase, TaskOption
from src.models.users import Team, User
from src.models.work_orders import WorkOrder
from src.routes._crud import (
    _get_user_company_settings_id,
    build_crud_router,
    validate_foreign_key_ownership,
)
from src.routes.assets_locations import (
    _hydrate_custom_field_values,
    _sync_entity_custom_fields,
    _verify_and_sync_m2m,
)
from src.schemas._base import CamelModel
from src.schemas.errors import CustomException
from src.services.serializer import model_to_dict, serialize_value
from src.services.stock import count_stock, lock_part, record_movement

router = APIRouter()


# 6.8 Parts, PartQuantities, PartConsumption, MultiParts
def _serialize_part(part: Part, db: Session) -> dict[str, Any]:
    res = model_to_dict(part, db=db)

    user_ids = db.scalars(
        select(t_part_user_associations.c.id_user).where(
            t_part_user_associations.c.id_part == part.id
        )
    ).all()
    users = db.scalars(select(User).where(User.id.in_(user_ids))).all() if user_ids else []
    user_dtos = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]
    res["assignedTo"] = user_dtos
    res["users"] = user_dtos

    team_ids = db.scalars(
        select(t_part_team_associations.c.id_team).where(
            t_part_team_associations.c.id_part == part.id
        )
    ).all()
    teams = db.scalars(select(Team).where(Team.id.in_(team_ids))).all() if team_ids else []
    res["teams"] = [{"id": t.id, "name": t.name, "description": t.description} for t in teams]

    vendor_ids = db.scalars(
        select(t_part_vendor_associations.c.id_vendor).where(
            t_part_vendor_associations.c.id_part == part.id
        )
    ).all()
    vendors = db.scalars(select(Vendor).where(Vendor.id.in_(vendor_ids))).all() if vendor_ids else []
    res["vendors"] = [
        {"id": v.id, "companyName": v.company_name, "name": v.name} for v in vendors
    ]

    customer_ids = db.scalars(
        select(t_part_customer_associations.c.id_customer).where(
            t_part_customer_associations.c.id_part == part.id
        )
    ).all()
    customers = (
        db.scalars(select(Customer).where(Customer.id.in_(customer_ids))).all()
        if customer_ids
        else []
    )
    res["customers"] = [{"id": c.id, "name": c.name} for c in customers]

    file_ids = db.scalars(
        select(t_part_file_associations.c.id_file).where(
            t_part_file_associations.c.id_part == part.id
        )
    ).all()
    files = (
        db.scalars(select(FileEntity).where(FileEntity.id.in_(file_ids))).all()
        if file_ids
        else []
    )
    res["files"] = [model_to_dict(f, db=db) for f in files]

    res["customFieldValues"] = _hydrate_custom_field_values(
        db, CustomFieldValue.part_id == part.id
    )

    open_wos = db.scalar(
        select(func.count(func.distinct(WorkOrder.id)))
        .select_from(PartQuantity)
        .join(WorkOrder, PartQuantity.work_order_id == WorkOrder.id)
        .where(
            PartQuantity.part_id == part.id,
            WorkOrder.status != 3,
        )
    )
    res["openWorkOrders"] = int(open_wos or 0)
    return res


def _sync_part_relations(
    part: Part, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if "assignedTo" in payload or "users" in payload:
        raw_users = (
            payload.get("assignedTo") if "assignedTo" in payload else payload.get("users")
        )
        _verify_and_sync_m2m(
            db,
            current_user,
            t_part_user_associations,
            "id_part",
            part.id,
            "id_user",
            User,
            raw_users,
        )
    if "teams" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_part_team_associations,
            "id_part",
            part.id,
            "id_team",
            Team,
            payload.get("teams"),
        )
    if "vendors" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_part_vendor_associations,
            "id_part",
            part.id,
            "id_vendor",
            Vendor,
            payload.get("vendors"),
        )
    if "customers" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_part_customer_associations,
            "id_part",
            part.id,
            "id_customer",
            Customer,
            payload.get("customers"),
        )
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_part_file_associations,
            "id_part",
            part.id,
            "id_file",
            FileEntity,
            payload.get("files"),
        )
    if "customFieldValues" in payload or "customFields" in payload:
        _sync_entity_custom_fields(
            db,
            current_user,
            "part_id",
            part.id,
            payload,
        )
    if any(k in payload for k in ("assignedTo", "users", "teams")):
        from src.models.enums import NotificationType
        from src.services.notifications import create_in_app_notifications

        part_user_ids = list(
            db.scalars(
                select(t_part_user_associations.c.id_user).where(
                    t_part_user_associations.c.id_part == part.id
                )
            ).all()
        )
        part_team_ids = list(
            db.scalars(
                select(t_part_team_associations.c.id_team).where(
                    t_part_team_associations.c.id_part == part.id
                )
            ).all()
        )
        create_in_app_notifications(
            db,
            user_ids=part_user_ids,
            team_ids=part_team_ids,
            message=f"You have been assigned to part {part.name}",
            notification_type=NotificationType.PART,
            resource_id=part.id,
            exclude_user_id=current_user.id,
            created_by=current_user.id,
        )
    run_part_workflows(part, db)


def _before_write_part(
    part: Part, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if part.barcode is not None:
        bc = str(part.barcode).strip()
        if bc:
            part.barcode = bc
            dup = db.scalar(
                select(Part.id).where(
                    Part.company_id == current_user.company_id,
                    Part.barcode == bc,
                    Part.id != (part.id or 0),
                )
            )
            if dup is not None:
                raise CustomException(
                    status_code=406,
                    message="A part with this barcode already exists",
                )
        else:
            part.barcode = None


# Session.info key: a part's quantity before a PATCH, read again after the payload is applied.
_QUANTITY_BEFORE_PATCH = "stock_quantity_before_patch"


def _after_create_part(
    part: Part, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    opening = float(part.quantity or 0.0)
    if not part.non_stock and opening > 0:
        # The payload already set the quantity; the ledger applies it so its first row anchors it.
        part.quantity = 0.0
        record_movement(
            db,
            part,
            MovementType.OPENING,
            opening,
            user_id=current_user.id,
            reason="Initial quantity",
            run_workflows=False,  # _sync_part_relations runs them once below
        )
    _sync_part_relations(part, payload, current_user, db)


def _before_patch_part(
    part: Part, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if "quantity" in payload:
        part = lock_part(db, part.id)
        db.info.setdefault(_QUANTITY_BEFORE_PATCH, {})[part.id] = float(part.quantity or 0.0)
    _before_write_part(part, payload, current_user, db)


def _after_patch_part(
    part: Part, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    before = db.info.get(_QUANTITY_BEFORE_PATCH, {}).pop(part.id, None)
    after = float(part.quantity or 0.0)
    if before is not None and not part.non_stock and after != before:
        if after < 0:
            raise CustomException(status_code=406, message="Quantity cannot be negative")
        # apply_patch already wrote the new value; put the old one back so the ledger applies the change once.
        part.quantity = before
        record_movement(
            db,
            part,
            MovementType.ADJUSTMENT,
            after - before,
            user_id=current_user.id,
            reason=str(payload.get("stockReason") or "").strip() or "Edited on part form",
            run_workflows=False,  # _sync_part_relations runs them once below
        )
    _sync_part_relations(part, payload, current_user, db)


parts_router = build_crud_router(
    "/parts",
    Part,
    custom_serializer=_serialize_part,
    before_create=_before_write_part,
    before_patch=_before_patch_part,
    after_create=_after_create_part,
    after_patch=_after_patch_part,
)


@parts_router.get("/mini")
def list_parts_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Part).where(Part.company_id == current_user.company_id)).all()
    return [
        {"id": r.id, "name": r.name, "cost": r.cost, "quantity": r.quantity, "unit": r.unit}
        for r in rows
    ]


@parts_router.get("/barcode/{barcode}")
def get_part_by_barcode(
    barcode: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    part = db.scalar(
        select(Part).where(
            Part.barcode == barcode,
            Part.company_id == current_user.company_id,
        )
    )
    if not part:
        raise CustomException(status_code=404, message="Part not found")
    return _serialize_part(part, db)


_NON_STOCK_MESSAGE = "Stock actions are not available for non-stock parts"


class StockReceiveIn(CamelModel):
    quantity: float = Field(gt=0)
    reason: str | None = None
    unit_cost: float | None = Field(default=None, ge=0)
    purchase_order_id: int | None = None


class StockIssueIn(CamelModel):
    quantity: float = Field(gt=0)
    work_order_id: int | None = None
    reason: str | None = None


class StockCountIn(CamelModel):
    counted: float = Field(ge=0)
    reason: str | None = None


def _lock_part_for_stock(part_id: int, current_user: User, db: Session) -> Part:
    part = lock_part(db, part_id)
    assert_company_access(current_user, part, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.PARTS_AND_MULTIPARTS, part, db):
        raise CustomException(status_code=403, message="Access is denied")
    if part.non_stock:
        raise CustomException(status_code=406, message=_NON_STOCK_MESSAGE)
    return part


def _receive_stock(
    part: Part,
    quantity: float,
    *,
    reason: str | None,
    unit_cost: float | None,
    purchase_order_id: int | None,
    current_user: User,
    db: Session,
) -> dict[str, Any]:
    movement = MovementType.RECEIPT
    if purchase_order_id is not None:
        po = db.get(PurchaseOrder, purchase_order_id)
        if po is None:
            raise CustomException(status_code=404, message="PurchaseOrder not found")
        if po.company_id != part.company_id:
            raise CustomException(status_code=403, message="Access is denied")
        movement = MovementType.PO_RECEIPT
    record_movement(
        db,
        part,
        movement,
        quantity,
        user_id=current_user.id,
        purchase_order_id=purchase_order_id,
        reason=reason,
        unit_cost=unit_cost,
    )
    db.commit()
    db.refresh(part)
    return _serialize_part(part, db)


@parts_router.post("/{part_id:int}/restock")
@parts_router.patch("/{part_id:int}/restock")
def restock_part(
    part_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Backward-compatible alias of POST /parts/{id}/stock/receive."""
    part = _lock_part_for_stock(part_id, current_user, db)
    qty = float(payload.get("quantity", 0) or 0)
    if qty <= 0:
        raise CustomException(status_code=406, message="Quantity must be positive")
    raw_cost = payload.get("unitCost")
    raw_po = payload.get("purchaseOrderId")
    return _receive_stock(
        part,
        qty,
        reason=payload.get("reason"),
        unit_cost=float(raw_cost) if raw_cost is not None else None,
        purchase_order_id=int(raw_po) if raw_po is not None else None,
        current_user=current_user,
        db=db,
    )


@parts_router.post("/{part_id:int}/stock/receive")
def receive_part_stock(
    part_id: int,
    body: StockReceiveIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    part = _lock_part_for_stock(part_id, current_user, db)
    return _receive_stock(
        part,
        body.quantity,
        reason=body.reason,
        unit_cost=body.unit_cost,
        purchase_order_id=body.purchase_order_id,
        current_user=current_user,
        db=db,
    )


@parts_router.post("/{part_id:int}/stock/issue")
def issue_part_stock(
    part_id: int,
    body: StockIssueIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    part = _lock_part_for_stock(part_id, current_user, db)
    if body.work_order_id is not None:
        wo = db.get(WorkOrder, body.work_order_id)
        if wo is None:
            raise CustomException(status_code=404, message="WorkOrder not found")
        if wo.company_id != part.company_id or not can_view(
            current_user, PermissionEntity.WORK_ORDERS, db
        ):
            raise CustomException(status_code=403, message="Access is denied")
    elif not (body.reason or "").strip():
        raise CustomException(
            status_code=406, message="A reason is required when no work order is given"
        )
    record_movement(
        db,
        part,
        MovementType.ISSUE,
        body.quantity,
        user_id=current_user.id,
        work_order_id=body.work_order_id,
        reason=body.reason,
    )
    db.commit()
    db.refresh(part)
    return _serialize_part(part, db)


@parts_router.post("/{part_id:int}/stock/count")
def count_part_stock(
    part_id: int,
    body: StockCountIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    part = _lock_part_for_stock(part_id, current_user, db)
    _tx, variance = count_stock(
        db, part, body.counted, user_id=current_user.id, reason=body.reason
    )
    db.commit()
    db.refresh(part)
    res = _serialize_part(part, db)
    res["variance"] = variance
    return res


@parts_router.get("/{part_id:int}/stock/movements")
def list_part_stock_movements(
    part_id: int,
    page: int = Query(default=0, ge=0),
    size: int = Query(default=20, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    part = db.get(Part, part_id)
    if not part:
        raise CustomException(status_code=404, message="Part not found")
    assert_company_access(current_user, part, is_super_admin=is_super_admin(current_user, db))
    if not can_view(current_user, PermissionEntity.PARTS_AND_MULTIPARTS, db):
        raise CustomException(status_code=403, message="Access is denied")
    size = min(size, 100)
    scope = (
        PartConsumption.part_id == part.id,
        PartConsumption.company_id == part.company_id,
    )
    total = db.scalar(select(func.count()).select_from(PartConsumption).where(*scope)) or 0
    rows = db.scalars(
        select(PartConsumption)
        .where(*scope)
        .order_by(PartConsumption.created_at.desc(), PartConsumption.id.desc())
        .offset(page * size)
        .limit(size)
    ).all()

    user_ids = {r.created_by for r in rows if r.created_by is not None}
    wo_ids = {r.work_order_id for r in rows if r.work_order_id is not None}
    po_ids = {r.purchase_order_id for r in rows if r.purchase_order_id is not None}
    users = (
        {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids)))}
        if user_ids
        else {}
    )
    wos = (
        {
            w.id: w
            for w in db.scalars(
                select(WorkOrder).where(
                    WorkOrder.id.in_(wo_ids), WorkOrder.company_id == part.company_id
                )
            )
        }
        if wo_ids
        else {}
    )
    pos = (
        {
            p.id: p
            for p in db.scalars(
                select(PurchaseOrder).where(
                    PurchaseOrder.id.in_(po_ids), PurchaseOrder.company_id == part.company_id
                )
            )
        }
        if po_ids
        else {}
    )

    content: list[dict[str, Any]] = []
    for r in rows:
        u = users.get(r.created_by)
        w = wos.get(r.work_order_id)
        p = pos.get(r.purchase_order_id)
        content.append(
            {
                "id": r.id,
                "createdAt": serialize_value(r.created_at),
                "movementType": r.movement_type,
                "change": r.change,
                "balanceAfter": r.balance_after,
                "quantity": r.quantity,
                "reason": r.reason,
                "unitCost": r.unit_cost,
                "createdBy": (
                    {"id": u.id, "firstName": u.first_name, "lastName": u.last_name}
                    if u
                    else None
                ),
                "workOrder": (
                    {"id": w.id, "title": w.title, "customId": w.custom_id} if w else None
                ),
                "purchaseOrder": {"id": p.id, "name": p.name} if p else None,
            }
        )
    return {"content": content, "totalElements": int(total), "page": page, "size": size}


router.include_router(parts_router)


def _serialize_part_quantity(pq: PartQuantity, db: Session) -> dict[str, Any]:
    res = model_to_dict(pq, db=db)
    if pq.part_id:
        p = db.get(Part, pq.part_id)
        if p:
            res["part"] = _serialize_part(p, db)
    return res


def _extract_part_id(item: dict[str, Any]) -> int | None:
    part_ref = item.get("part")
    if isinstance(part_ref, dict) and isinstance(part_ref.get("id"), int):
        return part_ref["id"]
    if isinstance(part_ref, int):
        return part_ref
    if isinstance(item.get("partId"), int):
        return item["partId"]
    if isinstance(item.get("part_id"), int):
        return item["part_id"]
    return None


def _consume_or_restore_part_stock(
    part_id: int,
    delta_qty: float,
    wo_id: int | None,
    current_user: User,
    db: Session,
) -> Part:
    part = lock_part(db, part_id)
    assert_company_access(current_user, part, is_super_admin=is_super_admin(current_user, db))
    if delta_qty > 0:
        record_movement(
            db, part, MovementType.WO_CONSUMPTION, delta_qty,
            user_id=current_user.id, work_order_id=wo_id,
        )
    elif delta_qty < 0:
        record_movement(
            db, part, MovementType.WO_RETURN, -delta_qty,
            user_id=current_user.id, work_order_id=wo_id,
        )
    return part


def _assert_pq_parent_edit_access(pq: PartQuantity, current_user: User, db: Session) -> None:
    if pq.work_order_id is not None:
        wo = db.get(WorkOrder, pq.work_order_id)
        if wo is not None:
            assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
            if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
                raise CustomException(status_code=403, message="Access is denied")
    if pq.purchase_order_id is not None:
        po = db.get(PurchaseOrder, pq.purchase_order_id)
        if po is not None:
            assert_company_access(current_user, po, is_super_admin=is_super_admin(current_user, db))
            if not can_edit_object(current_user, PermissionEntity.PURCHASE_ORDERS, po, db):
                raise CustomException(status_code=403, message="Access is denied")


def _before_create_pq(
    pq: PartQuantity, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _assert_pq_parent_edit_access(pq, current_user, db)


def _after_create_pq(
    pq: PartQuantity, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if pq.work_order_id and pq.part_id and (pq.quantity or 0.0) > 0:
        _consume_or_restore_part_stock(
            pq.part_id,
            float(pq.quantity),
            pq.work_order_id,
            current_user,
            db,
        )


def _before_patch_pq(
    pq: PartQuantity, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _assert_pq_parent_edit_access(pq, current_user, db)
    if pq.work_order_id is not None and pq.part_id is not None and "quantity" in payload:
        old_qty = float(pq.quantity or 0.0)
        new_qty = float(payload.get("quantity") or 0.0)
        delta = new_qty - old_qty
        if delta != 0:
            _consume_or_restore_part_stock(
                pq.part_id,
                delta,
                pq.work_order_id,
                current_user,
                db,
            )


def _before_delete_pq(
    pq: PartQuantity, current_user: User, db: Session
) -> None:
    _assert_pq_parent_edit_access(pq, current_user, db)
    if pq.work_order_id is not None and pq.part_id is not None and (pq.quantity or 0.0) > 0:
        _consume_or_restore_part_stock(
            pq.part_id,
            -float(pq.quantity or 0.0),
            pq.work_order_id,
            current_user,
            db,
        )


pq_router = build_crud_router(
    "/part-quantities",
    PartQuantity,
    custom_serializer=_serialize_part_quantity,
    before_create=_before_create_pq,
    after_create=_after_create_pq,
    before_patch=_before_patch_pq,
    before_delete=_before_delete_pq,
)


@pq_router.get("/work-order/{wo_id:int}")
def get_pq_by_work_order(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(PartQuantity).where(
            PartQuantity.work_order_id == wo_id,
            PartQuantity.company_id == wo.company_id,
        )
    ).all()
    return [_serialize_part_quantity(r, db) for r in rows]


@pq_router.patch("/work-order/{wo_id:int}")
def update_pq_for_work_order(
    wo_id: int,
    payload: list[Any] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")

    existing_rows = list(
        db.scalars(
            select(PartQuantity).where(
                PartQuantity.work_order_id == wo_id,
                PartQuantity.company_id == wo.company_id,
            )
        ).all()
    )
    existing_by_id = {r.id: r for r in existing_rows}
    existing_by_part_id: dict[int, PartQuantity] = {}
    for r in existing_rows:
        if r.part_id not in existing_by_part_id:
            existing_by_part_id[r.part_id] = r

    seen_ids: set[int] = set()
    result_rows: list[PartQuantity] = []

    for item in payload:
        if isinstance(item, int):
            item_id = None
            part_id = int(item)
            existing_match = existing_by_part_id.get(part_id)
            if existing_match is not None and existing_match.id not in seen_ids:
                seen_ids.add(existing_match.id)
                result_rows.append(existing_match)
                continue
            new_qty = 1.0
        elif isinstance(item, dict):
            item_id = item.get("id") if isinstance(item.get("id"), int) else None
            part_id = _extract_part_id(item)
            new_qty = float(item.get("quantity", 0) or 0)
        else:
            continue

        pq: PartQuantity | None = None
        if item_id is not None and item_id in existing_by_id:
            pq = existing_by_id[item_id]
        elif part_id is not None and part_id in existing_by_part_id and existing_by_part_id[part_id].id not in seen_ids:
            pq = existing_by_part_id[part_id]

        if pq is not None:
            seen_ids.add(pq.id)
            target_part_id = part_id or pq.part_id
            if target_part_id != pq.part_id:
                # Restore old part and consume new part
                _consume_or_restore_part_stock(
                    pq.part_id, -float(pq.quantity or 0.0), wo.id, current_user, db
                )
                _consume_or_restore_part_stock(
                    target_part_id, new_qty, wo.id, current_user, db
                )
                pq.part_id = target_part_id
            else:
                delta = new_qty - float(pq.quantity or 0.0)
                if delta != 0:
                    _consume_or_restore_part_stock(
                        pq.part_id, delta, wo.id, current_user, db
                    )
            pq.quantity = new_qty
            pq.updated_by = current_user.id
            result_rows.append(pq)
        elif part_id is not None:
            _consume_or_restore_part_stock(part_id, new_qty, wo.id, current_user, db)
            new_pq = PartQuantity(
                part_id=part_id,
                work_order_id=wo.id,
                quantity=new_qty,
                company_id=wo.company_id,
                created_by=current_user.id,
                updated_by=current_user.id,
                is_demo=False,
            )
            db.add(new_pq)
            db.flush()
            seen_ids.add(new_pq.id)
            result_rows.append(new_pq)

    for old_pq in existing_rows:
        if old_pq.id not in seen_ids:
            _consume_or_restore_part_stock(
                old_pq.part_id, -float(old_pq.quantity or 0.0), wo.id, current_user, db
            )
            db.delete(old_pq)

    db.commit()
    return [_serialize_part_quantity(r, db) for r in result_rows]


@pq_router.get("/purchase-order/{po_id:int}")
def get_pq_by_purchase_order(
    po_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise CustomException(status_code=404, message="PurchaseOrder not found")
    assert_company_access(current_user, po, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(PartQuantity).where(
            PartQuantity.purchase_order_id == po_id,
            PartQuantity.company_id == po.company_id,
        )
    ).all()
    return [_serialize_part_quantity(r, db) for r in rows]


def _reconcile_po_part_quantities(
    po: PurchaseOrder,
    payload: list[dict[str, Any]],
    current_user: User,
    db: Session,
) -> list[PartQuantity]:
    existing_rows = list(
        db.scalars(
            select(PartQuantity).where(
                PartQuantity.purchase_order_id == po.id,
                PartQuantity.company_id == po.company_id,
            )
        ).all()
    )
    existing_by_id = {r.id: r for r in existing_rows}
    existing_by_part_id = {r.part_id: r for r in existing_rows}
    seen_ids: set[int] = set()
    result_rows: list[PartQuantity] = []

    for item in payload:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") if isinstance(item.get("id"), int) else None
        part_id = _extract_part_id(item)
        new_qty = float(item.get("quantity", 0) or 0)

        pq: PartQuantity | None = None
        if item_id is not None and item_id in existing_by_id:
            pq = existing_by_id[item_id]
        elif part_id is not None and part_id in existing_by_part_id and existing_by_part_id[part_id].id not in seen_ids:
            pq = existing_by_part_id[part_id]

        if pq is not None:
            seen_ids.add(pq.id)
            if part_id is not None:
                part = db.get(Part, part_id)
                if not part:
                    raise CustomException(status_code=404, message=f"Part {part_id} not found")
                assert_company_access(current_user, part, is_super_admin=is_super_admin(current_user, db))
                pq.part_id = part_id
            pq.quantity = new_qty
            pq.updated_by = current_user.id
            result_rows.append(pq)
        elif part_id is not None:
            part = db.get(Part, part_id)
            if not part:
                raise CustomException(status_code=404, message=f"Part {part_id} not found")
            assert_company_access(current_user, part, is_super_admin=is_super_admin(current_user, db))
            new_pq = PartQuantity(
                part_id=part_id,
                purchase_order_id=po.id,
                quantity=new_qty,
                company_id=po.company_id,
                created_by=current_user.id,
                updated_by=current_user.id,
                is_demo=False,
            )
            db.add(new_pq)
            db.flush()
            seen_ids.add(new_pq.id)
            result_rows.append(new_pq)

    for old_pq in existing_rows:
        if old_pq.id not in seen_ids:
            db.delete(old_pq)

    return result_rows


@pq_router.patch("/purchase-order/{po_id:int}")
def update_pq_for_purchase_order(
    po_id: int,
    payload: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise CustomException(status_code=404, message="PurchaseOrder not found")
    assert_company_access(current_user, po, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.PURCHASE_ORDERS, po, db):
        raise CustomException(status_code=403, message="Access is denied")
    rows = _reconcile_po_part_quantities(po, payload, current_user, db)
    db.commit()
    return [_serialize_part_quantity(r, db) for r in rows]


router.include_router(pq_router)
router.include_router(build_crud_router("/part-consumptions", PartConsumption))


def _serialize_multi_parts(mp: MultiParts, db: Session) -> dict[str, Any]:
    res = model_to_dict(mp, db=db)
    part_ids = db.scalars(
        select(t_multi_parts_part_associations.c.id_part).where(
            t_multi_parts_part_associations.c.id_multi_parts == mp.id
        )
    ).all()
    parts = (
        db.scalars(
            select(Part).where(
                Part.id.in_(part_ids),
                Part.company_id == mp.company_id,
            )
        ).all()
        if part_ids
        else []
    )
    res["parts"] = [_serialize_part(p, db) for p in parts]
    return res


def _sync_multi_parts(mp: MultiParts, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if "parts" in payload and isinstance(payload["parts"], list):
        db.execute(
            t_multi_parts_part_associations.delete().where(
                t_multi_parts_part_associations.c.id_multi_parts == mp.id
            )
        )
        for item in payload["parts"]:
            pid = item.get("id") if isinstance(item, dict) else item
            if isinstance(pid, int):
                part = db.get(Part, pid)
                if part is None:
                    raise CustomException(status_code=404, message=f"Part {pid} not found")
                assert_company_access(
                    current_user, part, is_super_admin=is_super_admin(current_user, db)
                )
                db.execute(
                    t_multi_parts_part_associations.insert().values(
                        id_multi_parts=mp.id, id_part=pid
                    )
                )


mp_router = build_crud_router(
    "/multi-parts",
    MultiParts,
    custom_serializer=_serialize_multi_parts,
    after_create=_sync_multi_parts,
    after_patch=_sync_multi_parts,
)


@mp_router.get("/mini")
def list_multi_parts_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(MultiParts).where(MultiParts.company_id == current_user.company_id)).all()
    return [{"id": r.id, "name": r.name} for r in rows]


router.include_router(mp_router)


# 6.9 PurchaseOrders & AdditionalCosts
def _serialize_po(po: PurchaseOrder, db: Session) -> dict[str, Any]:
    res = model_to_dict(po, db=db)
    pqs = db.scalars(
        select(PartQuantity).where(
            PartQuantity.purchase_order_id == po.id,
            PartQuantity.company_id == po.company_id,
        )
    ).all()
    res["partQuantities"] = [_serialize_part_quantity(pq, db) for pq in pqs]
    res["customFieldValues"] = []
    return res


def _after_create_po(
    po: PurchaseOrder, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if isinstance(payload.get("partQuantities"), list):
        _reconcile_po_part_quantities(po, payload["partQuantities"], current_user, db)
    run_purchase_order_workflows(po, WFMainCondition.PURCHASE_ORDER_CREATED, db)


def _after_patch_po(
    po: PurchaseOrder, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if isinstance(payload.get("partQuantities"), list):
        _reconcile_po_part_quantities(po, payload["partQuantities"], current_user, db)
    run_purchase_order_workflows(po, WFMainCondition.PURCHASE_ORDER_UPDATED, db)


po_router = build_crud_router(
    "/purchase-orders",
    PurchaseOrder,
    custom_serializer=_serialize_po,
    after_create=_after_create_po,
    after_patch=_after_patch_po,
)


@po_router.patch("/{po_id:int}/respond")
def respond_purchase_order(
    po_id: int,
    approved: bool | None = Query(default=None),
    payload: dict[str, Any] | bool | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise CustomException(status_code=404, message="PurchaseOrder not found")
    assert_company_access(current_user, po, is_super_admin=is_super_admin(current_user, db))
    if not can_edit(current_user, PermissionEntity.PURCHASE_ORDERS, db):
        raise CustomException(status_code=403, message="Access is denied")

    if approved is not None:
        is_approved = bool(approved)
    elif isinstance(payload, dict):
        is_approved = bool(payload.get("approved", True))
    elif isinstance(payload, bool):
        is_approved = payload
    else:
        is_approved = True

    pqs = db.scalars(
        select(PartQuantity).where(
            PartQuantity.purchase_order_id == po.id,
            PartQuantity.company_id == po.company_id,
        )
    ).all()

    if is_approved and po.status != 0:
        for pq in pqs:
            if pq.part_id and (pq.quantity or 0.0) > 0:
                part = lock_part(db, pq.part_id)
                if part.company_id == po.company_id:
                    record_movement(
                        db, part, MovementType.PO_RECEIPT, float(pq.quantity),
                        user_id=current_user.id, purchase_order_id=po.id,
                    )
    elif not is_approved and po.status == 0:
        for pq in pqs:
            if pq.part_id and (pq.quantity or 0.0) > 0:
                part = lock_part(db, pq.part_id)
                if part.company_id == po.company_id:
                    # The stock may already have been used; the ledger still records the reversal.
                    record_movement(
                        db, part, MovementType.PO_REVERSAL, float(pq.quantity),
                        user_id=current_user.id, purchase_order_id=po.id,
                        allow_negative=True,
                    )

    po.status = 0 if is_approved else 1  # APPROVED=0, REJECTED=1, PENDING=2 in ApprovalStatus
    if po.created_by is not None:
        from src.models.enums import NotificationType
        from src.services.notifications import create_in_app_notifications

        status_word = "approved" if is_approved else "rejected"
        create_in_app_notifications(
            db,
            user_ids=[po.created_by],
            message=f"Purchase order {po.name} has been {status_word}",
            notification_type=NotificationType.PURCHASE_ORDER,
            resource_id=po.id,
            exclude_user_id=current_user.id,
            created_by=current_user.id,
        )
    run_purchase_order_workflows(po, WFMainCondition.PURCHASE_ORDER_UPDATED, db)
    db.commit()
    db.refresh(po)
    return _serialize_po(po, db)


router.include_router(po_router)


def _assert_ac_wo_access(ac: AdditionalCost, current_user: User, db: Session) -> None:
    if ac.work_order_id is None:
        raise CustomException(status_code=400, message="workOrder is required")
    wo = db.get(WorkOrder, ac.work_order_id)
    if wo is None:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
    if wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()


def _before_write_ac(
    ac: AdditionalCost, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _assert_ac_wo_access(ac, current_user, db)


def _before_delete_ac(ac: AdditionalCost, current_user: User, db: Session) -> None:
    _assert_ac_wo_access(ac, current_user, db)


ac_router = build_crud_router(
    "/additional-costs",
    AdditionalCost,
    before_create=_before_write_ac,
    before_patch=_before_write_ac,
    before_delete=_before_delete_ac,
)


@ac_router.get("/work-order/{wo_id:int}")
def list_additional_costs_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(AdditionalCost).where(
            AdditionalCost.work_order_id == wo_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(ac_router)


# 6.10 Tasks, TaskBases, Checklists
def _resolve_task_type(raw_type: Any) -> int:
    from src.models.enums import TaskType

    if isinstance(raw_type, int):
        return raw_type
    if isinstance(raw_type, str):
        s = raw_type.strip().upper()
        for idx, member in enumerate(TaskType):
            if member.name == s or member.value == s:
                return idx
        if s.isdigit():
            return int(s)
    return 0


def _serialize_task_base(tb: TaskBase, db: Session) -> dict[str, Any]:
    res = model_to_dict(tb, db=db)
    opts = db.scalars(select(TaskOption).where(TaskOption.task_base_id == tb.id)).all()
    res["options"] = [{"id": o.id, "label": o.label} for o in opts if o.label is not None]
    return res


def _serialize_task(task: Task, db: Session) -> dict[str, Any]:
    res = model_to_dict(task, db=db)
    if task.task_base_id:
        tb = db.get(TaskBase, task.task_base_id)
        if tb:
            res["taskBase"] = _serialize_task_base(tb, db)
    imgs = db.scalars(select(FileEntity).where(FileEntity.task_id == task.id)).all()
    res["images"] = [model_to_dict(img, db=db) for img in imgs]
    return res


def _sync_task_images(task: Task, item: dict[str, Any], company_id: int, db: Session) -> None:
    if "images" not in item or not isinstance(item["images"], list):
        return
    old_imgs = db.scalars(select(FileEntity).where(FileEntity.task_id == task.id)).all()
    for img in old_imgs:
        img.task_id = None
    for raw_img in item["images"]:
        fid = raw_img.get("id") if isinstance(raw_img, dict) else raw_img
        if isinstance(fid, int):
            fe = db.get(FileEntity, fid)
            if fe and fe.company_id == company_id:
                fe.task_id = task.id


def _reconcile_tasks(
    existing_tasks: list[Task],
    payload: list[dict[str, Any]],
    company_id: int,
    current_user: User,
    db: Session,
    *,
    work_order_id: int | None = None,
    preventive_maintenance_id: int | None = None,
) -> list[Task]:
    existing_by_id = {t.id: t for t in existing_tasks}
    seen_ids: set[int] = set()
    result_tasks: list[Task] = []

    for item in payload:
        if not isinstance(item, dict):
            continue
        tb_data = item.get("taskBase") if isinstance(item.get("taskBase"), dict) else item
        task_id = item.get("id") if isinstance(item.get("id"), int) else None
        task = existing_by_id.get(task_id) if task_id is not None else None

        asset_id = (
            tb_data.get("asset", {}).get("id")
            if isinstance(tb_data.get("asset"), dict)
            else tb_data.get("assetId")
        )
        user_id = (
            tb_data.get("user", {}).get("id")
            if isinstance(tb_data.get("user"), dict)
            else tb_data.get("userId")
        )
        meter_id = (
            tb_data.get("meter", {}).get("id")
            if isinstance(tb_data.get("meter"), dict)
            else tb_data.get("meterId")
        )

        if task is not None:
            seen_ids.add(task.id)
            if "value" in item:
                task.value = str(item["value"]) if item["value"] is not None else None
            if "notes" in item:
                task.notes = item["notes"]
            task.updated_by = current_user.id

            tb = db.get(TaskBase, task.task_base_id) if task.task_base_id else None
            if tb is not None:
                if "label" in tb_data and tb_data["label"] is not None:
                    tb.label = str(tb_data["label"])
                if "taskType" in tb_data and tb_data["taskType"] is not None:
                    tb.task_type = _resolve_task_type(tb_data["taskType"])
                if asset_id is not None or "asset" in tb_data or "assetId" in tb_data:
                    tb.asset_id = asset_id
                if user_id is not None or "user" in tb_data or "userId" in tb_data:
                    tb.user_id = user_id
                if meter_id is not None or "meter" in tb_data or "meterId" in tb_data:
                    tb.meter_id = meter_id
                validate_foreign_key_ownership(tb, current_user, db)
                if "options" in tb_data and isinstance(tb_data["options"], list):
                    db.execute(delete(TaskOption).where(TaskOption.task_base_id == tb.id))
                    for opt in tb_data["options"]:
                        opt_label = opt.get("label") if isinstance(opt, dict) else str(opt)
                        if opt_label:
                            db.add(
                                TaskOption(
                                    label=opt_label,
                                    task_base_id=tb.id,
                                    company_id=company_id,
                                )
                            )
            _sync_task_images(task, item, company_id, db)
            result_tasks.append(task)
        else:
            tb = TaskBase(
                label=str(tb_data.get("label") or "Task"),
                task_type=_resolve_task_type(tb_data.get("taskType", 0)),
                company_id=company_id,
                asset_id=asset_id,
                user_id=user_id,
                meter_id=meter_id,
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            validate_foreign_key_ownership(tb, current_user, db)
            db.add(tb)
            db.flush()
            for opt in tb_data.get("options") or []:
                opt_label = opt.get("label") if isinstance(opt, dict) else str(opt)
                if opt_label:
                    db.add(
                        TaskOption(
                            label=opt_label,
                            task_base_id=tb.id,
                            company_id=company_id,
                        )
                    )
            db.flush()
            new_task = Task(
                task_base_id=tb.id,
                work_order_id=work_order_id,
                preventive_maintenance_id=preventive_maintenance_id,
                company_id=company_id,
                value=str(item["value"]) if item.get("value") is not None else None,
                notes=item.get("notes"),
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.add(new_task)
            db.flush()
            _sync_task_images(new_task, item, company_id, db)
            seen_ids.add(new_task.id)
            result_tasks.append(new_task)

    for old_task in existing_tasks:
        if old_task.id not in seen_ids:
            db.delete(old_task)

    return result_tasks


def _assert_task_parent_access(task: Task, current_user: User, db: Session) -> None:
    if task.work_order_id is not None:
        wo = db.get(WorkOrder, task.work_order_id)
        if wo is None:
            raise CustomException(status_code=404, message="WorkOrder not found")
        assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
        if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
            raise CustomException(status_code=403, message="Access is denied")
        if wo.first_time_to_react is None:
            wo.first_time_to_react = utcnow()
    elif task.preventive_maintenance_id is not None:
        pm = db.get(PreventiveMaintenance, task.preventive_maintenance_id)
        if pm is None:
            raise CustomException(status_code=404, message="PreventiveMaintenance not found")
        assert_company_access(current_user, pm, is_super_admin=is_super_admin(current_user, db))
        if not can_edit_object(current_user, PermissionEntity.PREVENTIVE_MAINTENANCES, pm, db):
            raise CustomException(status_code=403, message="Access is denied")


def _before_write_task(
    task: Task, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _assert_task_parent_access(task, current_user, db)


def _before_delete_task(task: Task, current_user: User, db: Session) -> None:
    _assert_task_parent_access(task, current_user, db)


def _after_patch_task(
    task: Task, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    run_task_workflows(task, db)


tasks_router = build_crud_router(
    "/tasks",
    Task,
    custom_serializer=_serialize_task,
    before_create=_before_write_task,
    before_patch=_before_write_task,
    before_delete=_before_delete_task,
    after_patch=_after_patch_task,
)


@tasks_router.get("/work-order/{wo_id:int}")
def list_tasks_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Task).where(
            Task.work_order_id == wo_id,
            Task.company_id == wo.company_id,
        )
    ).all()
    return [_serialize_task(r, db) for r in rows]


@tasks_router.patch("/work-order/{wo_id:int}")
def create_tasks_for_wo(
    wo_id: int,
    payload: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
    if wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
    existing = list(
        db.scalars(
            select(Task).where(
                Task.work_order_id == wo_id,
                Task.company_id == wo.company_id,
            )
        ).all()
    )
    reconciled = _reconcile_tasks(
        existing,
        payload,
        wo.company_id,
        current_user,
        db,
        work_order_id=wo_id,
    )
    for t in reconciled:
        run_task_workflows(t, db)
    db.commit()
    return [_serialize_task(t, db) for t in reconciled]


@tasks_router.get("/preventive-maintenance/{pm_id:int}")
def list_tasks_by_pm(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    pm = db.get(PreventiveMaintenance, pm_id)
    if not pm:
        raise CustomException(status_code=404, message="PreventiveMaintenance not found")
    assert_company_access(current_user, pm, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Task).where(
            Task.preventive_maintenance_id == pm_id,
            Task.company_id == pm.company_id,
        )
    ).all()
    return [_serialize_task(r, db) for r in rows]


@tasks_router.patch("/preventive-maintenance/{pm_id:int}")
def patch_tasks_for_pm(
    pm_id: int,
    payload: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    pm = db.get(PreventiveMaintenance, pm_id)
    if not pm:
        raise CustomException(status_code=404, message="PreventiveMaintenance not found")
    assert_company_access(current_user, pm, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.PREVENTIVE_MAINTENANCES, pm, db):
        raise CustomException(status_code=403, message="Access is denied")
    existing = list(
        db.scalars(
            select(Task).where(
                Task.preventive_maintenance_id == pm_id,
                Task.company_id == pm.company_id,
            )
        ).all()
    )
    reconciled = _reconcile_tasks(
        existing,
        payload,
        pm.company_id,
        current_user,
        db,
        preventive_maintenance_id=pm_id,
    )
    db.commit()
    return [_serialize_task(t, db) for t in reconciled]


router.include_router(tasks_router)


def _serialize_checklist(cl: Checklist, db: Session) -> dict[str, Any]:
    from src.models.associations import checklist_task_bases

    res = model_to_dict(cl, db=db)
    tb_ids = db.scalars(
        select(checklist_task_bases.c.task_bases_id).where(
            checklist_task_bases.c.checklist_id == cl.id
        )
    ).all()
    tbs = db.scalars(select(TaskBase).where(TaskBase.id.in_(tb_ids))).all() if tb_ids else []
    res["taskBases"] = [_serialize_task_base(tb, db) for tb in tbs]
    return res


def _sync_checklist_task_bases(
    cl: Checklist, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    from sqlalchemy import insert
    from src.models.associations import checklist_task_bases

    if "taskBases" not in payload or not isinstance(payload["taskBases"], list):
        return
    old_tb_ids = list(
        db.scalars(
            select(checklist_task_bases.c.task_bases_id).where(
                checklist_task_bases.c.checklist_id == cl.id
            )
        ).all()
    )
    db.execute(delete(checklist_task_bases).where(checklist_task_bases.c.checklist_id == cl.id))
    for old_tb_id in old_tb_ids:
        referenced = db.scalar(select(Task.id).where(Task.task_base_id == old_tb_id).limit(1))
        if referenced is None:
            db.execute(delete(TaskOption).where(TaskOption.task_base_id == old_tb_id))
            db.execute(delete(TaskBase).where(TaskBase.id == old_tb_id))

    for item in payload["taskBases"]:
        tb_data = item.get("taskBase") if isinstance(item, dict) and "taskBase" in item else item
        if not isinstance(tb_data, dict):
            continue
        tb = TaskBase(
            label=tb_data.get("label", "Task"),
            task_type=_resolve_task_type(tb_data.get("taskType", 0)),
            company_id=current_user.company_id,
            asset_id=tb_data.get("asset", {}).get("id") if isinstance(tb_data.get("asset"), dict) else tb_data.get("assetId"),
            user_id=tb_data.get("user", {}).get("id") if isinstance(tb_data.get("user"), dict) else tb_data.get("userId"),
            meter_id=tb_data.get("meter", {}).get("id") if isinstance(tb_data.get("meter"), dict) else tb_data.get("meterId"),
        )
        validate_foreign_key_ownership(tb, current_user, db)
        db.add(tb)
        db.flush()
        for opt in tb_data.get("options") or []:
            opt_label = opt.get("label") if isinstance(opt, dict) else str(opt)
            if opt_label:
                db.add(TaskOption(label=opt_label, task_base_id=tb.id, company_id=current_user.company_id))
        db.flush()
        db.execute(
            insert(checklist_task_bases).values(
                checklist_id=cl.id,
                task_bases_id=tb.id,
            )
        )


checklists_router = build_crud_router(
    "/checklists",
    Checklist,
    custom_serializer=_serialize_checklist,
    after_create=_sync_checklist_task_bases,
    after_patch=_sync_checklist_task_bases,
)


@checklists_router.get("/mini")
def list_checklists_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    cs_id = _get_user_company_settings_id(current_user, db)
    rows = db.scalars(
        select(Checklist).where(Checklist.company_settings_id == cs_id)
    ).all()
    return [{"id": r.id, "name": r.name} for r in rows]


router.include_router(checklists_router)
