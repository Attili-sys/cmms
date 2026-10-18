"""Routes for Parts, PartQuantities, PartConsumption, MultiParts, PurchaseOrders, AdditionalCosts, Tasks, Checklists."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models.associations import t_multi_parts_part_associations
from src.models.parts_po import (
    AdditionalCost,
    MultiParts,
    Part,
    PartQuantity,
    PartTransaction as PartConsumption,
    PurchaseOrder,
)
from src.models.tasks import Checklist, Task, TaskBase, TaskOption
from src.models.users import User
from src.routes._crud import build_crud_router
from src.schemas.errors import CustomException
from src.services.serializer import model_to_dict

router = APIRouter()


# 6.8 Parts, PartQuantities, PartConsumption, MultiParts
def _serialize_part(part: Part, db: Session) -> dict[str, Any]:
    res = model_to_dict(part, db=db)
    res["openWorkOrders"] = 0
    return res


parts_router = build_crud_router("/parts", Part, custom_serializer=_serialize_part)


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


router.include_router(parts_router)


def _serialize_part_quantity(pq: PartQuantity, db: Session) -> dict[str, Any]:
    res = model_to_dict(pq, db=db)
    if pq.part_id:
        p = db.get(Part, pq.part_id)
        if p:
            res["part"] = _serialize_part(p, db)
    return res


pq_router = build_crud_router("/part-quantities", PartQuantity, custom_serializer=_serialize_part_quantity)


@pq_router.get("/work-order/{wo_id:int}")
def get_pq_by_work_order(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(PartQuantity).where(
            PartQuantity.work_order_id == wo_id,
            PartQuantity.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_part_quantity(r, db) for r in rows]


@pq_router.patch("/work-order/{wo_id:int}")
def update_pq_for_work_order(
    wo_id: int,
    payload: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(PartQuantity).where(
            PartQuantity.work_order_id == wo_id,
            PartQuantity.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_part_quantity(r, db) for r in rows]


@pq_router.get("/purchase-order/{po_id:int}")
def get_pq_by_purchase_order(
    po_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(PartQuantity).where(
            PartQuantity.purchase_order_id == po_id,
            PartQuantity.company_id == current_user.company_id,
        )
    ).all()
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
    parts = db.scalars(select(Part).where(Part.id.in_(part_ids))).all() if part_ids else []
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
po_router = build_crud_router("/purchase-orders", PurchaseOrder)


@po_router.patch("/{po_id:int}/respond")
def respond_purchase_order(
    po_id: int,
    approved: bool = Body(default=True, embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise CustomException(status_code=404, message="PurchaseOrder not found")
    assert_company_access(current_user, po, is_super_admin=is_super_admin(current_user, db))
    po.status = 0 if approved else 2  # APPROVED=0, REJECTED=2 in ApprovalStatus
    db.commit()
    db.refresh(po)
    return model_to_dict(po, db=db)


router.include_router(po_router)

ac_router = build_crud_router("/additional-costs", AdditionalCost)


@ac_router.get("/work-order/{wo_id:int}")
def list_additional_costs_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(AdditionalCost).where(
            AdditionalCost.work_order_id == wo_id,
            AdditionalCost.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(ac_router)


# 6.10 Tasks, TaskBases, Checklists
def _serialize_task_base(tb: TaskBase, db: Session) -> dict[str, Any]:
    res = model_to_dict(tb, db=db)
    opts = db.scalars(select(TaskOption).where(TaskOption.task_base_id == tb.id)).all()
    res["options"] = [o.value for o in opts if o.value is not None]
    return res


def _serialize_task(task: Task, db: Session) -> dict[str, Any]:
    res = model_to_dict(task, db=db)
    if task.task_base_id:
        tb = db.get(TaskBase, task.task_base_id)
        if tb:
            res["taskBase"] = _serialize_task_base(tb, db)
    return res


tasks_router = build_crud_router("/tasks", Task, custom_serializer=_serialize_task)


@tasks_router.get("/work-order/{wo_id:int}")
def list_tasks_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Task).where(
            Task.work_order_id == wo_id,
            Task.company_id == current_user.company_id,
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
    # Replace or append tasks for work order
    created: list[Task] = []
    for item in payload:
        tb_data = item.get("taskBase") or item
        tb = TaskBase(
            label=tb_data.get("label", "Task"),
            task_type=0,
            company_id=current_user.company_id,
        )
        db.add(tb)
        db.flush()
        t = Task(
            task_base_id=tb.id,
            work_order_id=wo_id,
            company_id=current_user.company_id,
            value=item.get("value"),
            notes=item.get("notes"),
        )
        db.add(t)
        db.flush()
        created.append(t)
    db.commit()
    return [_serialize_task(t, db) for t in created]


@tasks_router.get("/preventive-maintenance/{pm_id:int}")
def list_tasks_by_pm(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Task).where(
            Task.preventive_maintenance_id == pm_id,
            Task.company_id == current_user.company_id,
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
    rows = db.scalars(
        select(Task).where(
            Task.preventive_maintenance_id == pm_id,
            Task.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_task(r, db) for r in rows]


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


checklists_router = build_crud_router("/checklists", Checklist, custom_serializer=_serialize_checklist)


@checklists_router.get("/mini")
def list_checklists_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Checklist)).all()
    return [{"id": r.id, "name": r.name} for r in rows]


router.include_router(checklists_router)
