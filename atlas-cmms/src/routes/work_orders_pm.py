"""Routes for WorkOrders, WorkOrderHistories, Labors, Relations, PreventiveMaintenances, Schedules."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models._base import utcnow
from src.models.associations import work_order_assigned_to
from src.models.categories import WorkOrderCategory
from src.models.location_asset import Asset, Location
from src.models.meters import WorkOrderMeterTrigger
from src.models.pm_schedule import PreventiveMaintenance, Schedule
from src.models.settings import WorkOrderConfiguration
from src.models.users import Team, User
from src.models.work_orders import (
    Comment,
    Labor,
    Relation,
    WorkOrder,
    WorkOrderHistory,
)
from src.pdf.work_order_pdf import render_work_order_pdf
from src.routes._crud import apply_model_defaults, build_crud_router
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict
from src.utils.dates import to_iso_utc
from src.utils.search import SearchCriteria, execute_search

router = APIRouter()


def _serialize_wo(wo: WorkOrder, db: Session) -> dict[str, Any]:
    res = model_to_dict(wo, db=db)
    assigned_ids = db.scalars(
        select(work_order_assigned_to.c.assigned_to_id).where(
            work_order_assigned_to.c.work_order_id == wo.id
        )
    ).all()
    users = db.scalars(select(User).where(User.id.in_(assigned_ids))).all() if assigned_ids else []
    res["assignedTo"] = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]
    if wo.asset_id:
        asset = db.get(Asset, wo.asset_id)
        if asset:
            res["asset"] = {"id": asset.id, "name": asset.name, "customId": asset.custom_id}
    if wo.location_id:
        loc = db.get(Location, wo.location_id)
        if loc:
            res["location"] = {"id": loc.id, "name": loc.name, "address": loc.address}
    if wo.category_id:
        cat = db.get(WorkOrderCategory, wo.category_id)
        if cat:
            res["category"] = {"id": cat.id, "name": cat.name}
    if wo.team_id:
        team = db.get(Team, wo.team_id)
        if team:
            res["team"] = {"id": team.id, "name": team.name}
    if wo.primary_user_id:
        pu = db.get(User, wo.primary_user_id)
        if pu:
            res["primaryUser"] = {
                "id": pu.id,
                "firstName": pu.first_name,
                "lastName": pu.last_name,
                "email": pu.email,
            }
    res.setdefault("files", [])
    return res


def _before_create_wo(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if wo.status is None:
        wo.status = 0  # OPEN
    if wo.priority is None:
        wo.priority = 0  # NONE


def _sync_wo_relations(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if not wo.custom_id:
        wo.custom_id = f"WO{wo.id:06d}"
    if "assignedTo" in payload and isinstance(payload["assignedTo"], list):
        db.execute(work_order_assigned_to.delete().where(work_order_assigned_to.c.work_order_id == wo.id))
        for item in payload["assignedTo"]:
            uid = item.get("id") if isinstance(item, dict) else item
            if isinstance(uid, int):
                db.execute(
                    work_order_assigned_to.insert().values(work_order_id=wo.id, assigned_to_id=uid)
                )


wo_router = build_crud_router(
    "/work-orders",
    WorkOrder,
    custom_serializer=_serialize_wo,
    before_create=_before_create_wo,
    after_create=_sync_wo_relations,
    after_patch=_sync_wo_relations,
)


@wo_router.get("/urgent")
def get_urgent_wo_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.company_id == current_user.company_id,
            WorkOrder.priority == 3,
            WorkOrder.status != 3,
        )
    ).all()
    return SuccessResponse(success=True, message=str(len(rows))).model_dump()


@wo_router.post("/search/mini")
def search_wo_mini(
    criteria: SearchCriteria = Body(default_factory=SearchCriteria),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return execute_search(
        db=db,
        model_cls=WorkOrder,
        criteria=criteria,
        company_id=current_user.company_id,
        serializer=lambda r: _serialize_wo(r, db),
    )


@wo_router.post("/events")
def get_wo_events(
    payload: dict[str, Any] = Body(default_factory=dict),
    company_id: int | None = Query(default=None, alias="companyId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrder).where(WorkOrder.company_id == current_user.company_id)
    ).all()
    return [
        {
            "type": "WORK_ORDER",
            "date": to_iso_utc(r.due_date or r.created_at),
            "event": _serialize_wo(r, db),
        }
        for r in rows
    ]


@wo_router.get("/mini")
def list_wo_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(WorkOrder).where(WorkOrder.company_id == current_user.company_id)).all()
    return [{"id": r.id, "title": r.title, "customId": r.custom_id} for r in rows]


@wo_router.get("/asset/{asset_id:int}")
def list_wo_by_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.asset_id == asset_id,
            WorkOrder.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_wo(r, db) for r in rows]


@wo_router.get("/location/{location_id:int}")
def list_wo_by_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.location_id == location_id,
            WorkOrder.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_wo(r, db) for r in rows]


@wo_router.get("/part/{part_id:int}")
def list_wo_by_part(
    part_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return []


@wo_router.patch("/files/{wo_id:int}/add")
def add_wo_files(
    wo_id: int,
    files: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    return _serialize_wo(wo, db)


@wo_router.delete("/files/{wo_id:int}/{file_id:int}/remove")
def remove_wo_file(
    wo_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    return _serialize_wo(wo, db)


@wo_router.get("/pdf/{wo_id:int}")
@wo_router.post("/report/{wo_id:int}/stream")
def get_wo_pdf(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    wo_dict = _serialize_wo(wo, db)
    pdf_bytes = render_work_order_pdf(wo_dict)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="work-order-{wo.id}.pdf"'},
    )


@wo_router.get("/report/{wo_id:int}")
@wo_router.post("/report/{wo_id:int}")
def get_wo_report_url(
    wo_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return SuccessResponse(success=True, message=f"/api/work-orders/pdf/{wo_id}").model_dump()


@wo_router.post("/{wo_id:int}/report/send")
def send_wo_report(
    wo_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return SuccessResponse(success=True, message="Report sent").model_dump()


@wo_router.patch("/{wo_id:int}/change-status")
def change_wo_status(
    wo_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    apply_patch(wo, payload)
    if wo.status == 3 and wo.completed_on is None:  # COMPLETE = 3
        wo.completed_on = utcnow()
        wo.completed_by_id = current_user.id
    hist = WorkOrderHistory(
        name=f"Status changed to {payload.get('status')}",
        work_order_id=wo.id,
        user_id=current_user.id,
    )
    db.add(hist)
    db.commit()
    db.refresh(wo)
    return _serialize_wo(wo, db)


router.include_router(wo_router)

# WorkOrderHistories
woh_router = build_crud_router("/work-order-histories", WorkOrderHistory)


@woh_router.get("/work-order/{wo_id:int}")
def list_histories_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrderHistory).where(
            WorkOrderHistory.work_order_id == wo_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(woh_router)

# Comments
def _serialize_comment(c: Comment, db: Session) -> dict[str, Any]:
    res = model_to_dict(c, db=db)
    u = db.get(User, c.user_id) if c.user_id else None
    if u:
        res["createdBy"] = {
            "id": u.id,
            "firstName": u.first_name,
            "lastName": u.last_name,
            "email": u.email,
        }
    return res


def _before_create_comment(c: Comment, payload: dict[str, Any], current_user: User, db: Session) -> None:
    c.user_id = current_user.id
    if not c.content:
        c.content = payload.get("content") or payload.get("text") or ""


comments_router = build_crud_router(
    "/comments",
    Comment,
    custom_serializer=_serialize_comment,
    before_create=_before_create_comment,
)


@comments_router.post("/search/{wo_id:int}")
def search_comments_by_wo(
    wo_id: int,
    criteria: SearchCriteria = Body(default_factory=SearchCriteria),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from src.utils.pagination import as_spring_page

    rows = db.scalars(
        select(Comment).where(
            Comment.work_order_id == wo_id,
            Comment.company_id == current_user.company_id,
        )
    ).all()
    items = [_serialize_comment(r, db) for r in rows]
    return as_spring_page(
        items, total=len(items), page_num=criteria.pageNum, page_size=criteria.pageSize
    ).model_dump(by_alias=True)


@comments_router.get("/count/{wo_id:int}")
def count_comments_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    rows = db.scalars(
        select(Comment).where(
            Comment.work_order_id == wo_id,
            Comment.company_id == current_user.company_id,
        )
    ).all()
    return len(rows)


router.include_router(comments_router)

# Labors
labors_router = build_crud_router("/labors", Labor)


@labors_router.get("/work-order/{wo_id:int}")
def list_labors_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Labor).where(
            Labor.work_order_id == wo_id,
            Labor.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


@labors_router.post("/work-order/{wo_id:int}")
def create_labor_for_wo(
    wo_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    labor = Labor()
    apply_patch(labor, payload)
    labor.work_order_id = wo_id
    labor.company_id = current_user.company_id
    if labor.assigned_to_id is None:
        labor.assigned_to_id = current_user.id
    apply_model_defaults(labor)
    db.add(labor)
    db.commit()
    db.refresh(labor)
    return model_to_dict(labor, db=db)


@labors_router.post("/controlling-time-timer")
def control_labor_timer(
    action: str = Query(default="START"),
    work_order_id: int = Query(default=0, alias="workOrderId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    labor = db.scalar(
        select(Labor).where(
            Labor.work_order_id == work_order_id,
            Labor.assigned_to_id == current_user.id,
        )
    )
    if not labor:
        labor = Labor(
            work_order_id=work_order_id,
            assigned_to_id=current_user.id,
            company_id=current_user.company_id,
            started_at=utcnow(),
            status=0,  # RUNNING
            duration=0,
            hourly_rate=current_user.rate or 0,
            include_to_total_time=True,
            logged=False,
            is_demo=False,
        )
        db.add(labor)
    else:
        labor.status = 1 if action.upper() == "STOP" else 0
    db.commit()
    db.refresh(labor)
    return model_to_dict(labor, db=db)


router.include_router(labors_router)

# Relations
relations_router = build_crud_router("/relations", Relation)


@relations_router.get("/work-order/{wo_id:int}")
def list_relations_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Relation).where(
            (Relation.parent_id == wo_id) | (Relation.child_id == wo_id),
            Relation.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(relations_router)
router.include_router(build_crud_router("/work-order-configurations", WorkOrderConfiguration))

womt_router = build_crud_router("/work-order-meter-triggers", WorkOrderMeterTrigger)


@womt_router.get("/meter/{meter_id:int}")
def list_triggers_by_meter(
    meter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrderMeterTrigger).where(
            WorkOrderMeterTrigger.meter_id == meter_id,
            WorkOrderMeterTrigger.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(womt_router)


# 6.12 PreventiveMaintenances & Schedules
def _serialize_pm(pm: PreventiveMaintenance, db: Session) -> dict[str, Any]:
    res = model_to_dict(pm, db=db)
    sched = db.scalar(select(Schedule).where(Schedule.preventive_maintenance_id == pm.id))
    res["schedule"] = model_to_dict(sched, db=db) if sched else None
    return res


def _after_create_pm(
    pm: PreventiveMaintenance, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not pm.custom_id:
        pm.custom_id = f"PM{pm.id:06d}"
    sched = db.scalar(select(Schedule).where(Schedule.preventive_maintenance_id == pm.id))
    if not sched:
        sched_data = payload.get("schedule") if isinstance(payload.get("schedule"), dict) else {}
        sched = Schedule(
            preventive_maintenance_id=pm.id,
            company_id=current_user.company_id,
            starts_on=utcnow(),
            frequency=sched_data.get("frequency", 7),
            disabled=False,
            recurrence_type=0,
            recurrence_based_on=0,
            is_demo=False,
        )
        apply_patch(sched, sched_data)
        db.add(sched)


pm_router = build_crud_router(
    "/preventive-maintenances",
    PreventiveMaintenance,
    custom_serializer=_serialize_pm,
    after_create=_after_create_pm,
)


@pm_router.get("/{pm_id:int}/recent-work-orders")
def get_pm_recent_work_orders(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.parent_preventive_maintenance_id == pm_id,
            WorkOrder.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_wo(r, db) for r in rows]


@pm_router.post("/{pm_id:int}/trigger-work-order")
def trigger_pm_work_order(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    pm = db.get(PreventiveMaintenance, pm_id)
    if not pm:
        raise CustomException(status_code=404, message="PreventiveMaintenance not found")
    wo = WorkOrder(
        title=pm.title or pm.name or "PM Work Order",
        description=pm.description,
        priority=pm.priority or 0,
        status=0,
        company_id=current_user.company_id,
        asset_id=pm.asset_id,
        location_id=pm.location_id,
        primary_user_id=pm.primary_user_id,
        team_id=pm.team_id,
        category_id=pm.category_id,
        parent_preventive_maintenance_id=pm.id,
        estimated_duration=pm.estimated_duration or 0.0,
        required_signature=bool(pm.required_signature),
        archived=False,
        is_demo=False,
        created_by=current_user.id,
    )
    db.add(wo)
    db.flush()
    wo.custom_id = f"WO{wo.id:06d}"
    db.commit()
    db.refresh(wo)
    return _serialize_wo(wo, db)


router.include_router(pm_router)

schedules_router = build_crud_router("/schedules", Schedule)


@schedules_router.patch("/{sched_id:int}/reschedule")
def reschedule_pm(
    sched_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    sched = db.get(Schedule, sched_id)
    if not sched:
        raise CustomException(status_code=404, message="Schedule not found")
    assert_company_access(current_user, sched, is_super_admin=is_super_admin(current_user, db))
    apply_patch(sched, payload)
    db.commit()
    db.refresh(sched)
    return model_to_dict(sched, db=db)


router.include_router(schedules_router)


# Workload endpoints
@router.get("/workload/overview")
def get_workload_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return {"users": [], "days": []}


@router.get("/workload/unscheduled")
def get_workload_unscheduled(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.company_id == current_user.company_id,
            WorkOrder.due_date.is_(None),
            WorkOrder.status != 3,
        )
    ).all()
    return [_serialize_wo(r, db) for r in rows]


@router.patch("/workload/work-orders/{wo_id:int}/schedule")
def schedule_workload_wo(
    wo_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    apply_patch(wo, payload)
    db.commit()
    db.refresh(wo)
    return _serialize_wo(wo, db)

