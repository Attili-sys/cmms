"""Routes for WorkOrders, WorkOrderHistories, Labors, Relations, PreventiveMaintenances, Schedules."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, Query, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.deps.permissions import can_edit_object
from src.jobs.pm_generator import (
    advance_schedule_next_due_date,
    create_work_order_from_pm,
    get_schedule_days_of_week,
    normalize_day_of_week,
)
from src.models._base import utcnow
from src.models.associations import (
    preventive_maintenance_assigned_to,
    preventive_maintenance_customers,
    preventive_maintenance_files,
    schedule_days_of_week,
    t_work_order_file_associations,
    work_order_assigned_to,
    work_order_customers,
    work_order_files,
)
from src.models.categories import WorkOrderCategory
from src.models.enums import PermissionEntity, WFMainCondition
from src.models.files_custom import CustomFieldValue, File as FileEntity
from src.models.location_asset import Asset, Location
from src.models.meters import WorkOrderMeterTrigger
from src.models.parts_po import Customer, Part, PartQuantity
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
from src.routes.assets_locations import (
    _hydrate_custom_field_values,
    _sync_entity_custom_fields,
    _verify_and_sync_m2m,
)
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict
from src.services.workflow_engine import run_work_order_workflows
from src.utils.dates import ensure_utc, parse_iso_utc, to_iso_utc
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

    customer_ids = db.scalars(
        select(work_order_customers.c.customers_id).where(
            work_order_customers.c.work_order_id == wo.id
        )
    ).all()
    customers = (
        db.scalars(select(Customer).where(Customer.id.in_(customer_ids))).all()
        if customer_ids
        else []
    )
    res["customers"] = [{"id": c.id, "name": c.name} for c in customers]

    file_ids_1 = db.scalars(
        select(work_order_files.c.files_id).where(work_order_files.c.work_order_id == wo.id)
    ).all()
    file_ids_2 = db.scalars(
        select(t_work_order_file_associations.c.id_file).where(
            t_work_order_file_associations.c.id_work_order == wo.id
        )
    ).all()
    all_file_ids = list(dict.fromkeys([*file_ids_1, *file_ids_2]))
    files = (
        db.scalars(select(FileEntity).where(FileEntity.id.in_(all_file_ids))).all()
        if all_file_ids
        else []
    )
    res["files"] = [model_to_dict(f, db=db) for f in files]

    res["customFieldValues"] = _hydrate_custom_field_values(
        db, CustomFieldValue.work_order_id == wo.id
    )

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
    res.setdefault("completedBy", None)
    return res


def _before_create_wo(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if wo.status is None:
        wo.status = 0  # OPEN
    if wo.priority is None:
        wo.priority = 0  # NONE


def _resolve_asset_status_val(raw_status: Any) -> int | None:
    from src.models.enums import AssetStatus

    if raw_status is None:
        return None
    if isinstance(raw_status, int):
        return raw_status
    s = str(raw_status).strip().upper().replace(" ", "_").replace("-", "_")
    for idx, member in enumerate(AssetStatus):
        if member.name == s or member.value == s:
            return idx
    if s.isdigit():
        return int(s)
    return None


def _stop_running_labors_for_wo(wo: WorkOrder, db: Session) -> None:
    now = utcnow()
    running_labors = db.scalars(
        select(Labor).where(
            Labor.work_order_id == wo.id,
            Labor.status == 1,  # TimeStatus.RUNNING == 1
        )
    ).all()
    for lb in running_labors:
        if lb.started_at is not None:
            elapsed = max(0, int((now - ensure_utc(lb.started_at)).total_seconds()))
            lb.duration = int(lb.duration or 0) + elapsed
        lb.status = 0  # TimeStatus.STOPPED == 0


def _handle_wo_completion_side_effects(
    wo: WorkOrder, current_user: User, db: Session
) -> None:
    from src.routes.assets_locations import stop_asset_downtime

    if wo.completed_on is None:
        wo.completed_on = utcnow()
        wo.completed_by_id = current_user.id

    _stop_running_labors_for_wo(wo, db)

    if wo.asset_id is not None:
        other_incomplete = db.scalar(
            select(WorkOrder.id).where(
                WorkOrder.asset_id == wo.asset_id,
                WorkOrder.id != wo.id,
                WorkOrder.status != 3,
            )
        )
        if other_incomplete is None:
            stop_asset_downtime(wo.asset_id, db)

    if wo.parent_preventive_maintenance_id is not None:
        pm = db.get(PreventiveMaintenance, wo.parent_preventive_maintenance_id)
        if pm is not None:
            sched = (
                db.get(Schedule, pm.schedule_id)
                if pm.schedule_id
                else db.scalar(
                    select(Schedule).where(Schedule.preventive_maintenance_id == pm.id)
                )
            )
            if (
                sched is not None
                and not sched.disabled
                and (sched.recurrence_based_on or "").strip().upper() == "COMPLETED_DATE"
            ):
                base_dt = ensure_utc(wo.completed_on or utcnow())
                sched.next_due_date = advance_schedule_next_due_date(sched, base_dt, db)
                if sched.ends_on and ensure_utc(sched.next_due_date) > ensure_utc(sched.ends_on):
                    sched.disabled = True


def _sync_wo_relations(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    from src.routes.assets_locations import (
        is_really_down,
        stop_asset_downtime,
        trigger_asset_downtime,
    )

    if not wo.custom_id:
        wo.custom_id = f"WO{wo.id:06d}"
    if "assignedTo" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            work_order_assigned_to,
            "work_order_id",
            wo.id,
            "assigned_to_id",
            User,
            payload.get("assignedTo"),
        )
    if "customers" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            work_order_customers,
            "work_order_id",
            wo.id,
            "customers_id",
            Customer,
            payload.get("customers"),
        )
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            work_order_files,
            "work_order_id",
            wo.id,
            "files_id",
            FileEntity,
            payload.get("files"),
        )
    if "customFieldValues" in payload or "customFields" in payload:
        _sync_entity_custom_fields(
            db,
            current_user,
            "work_order_id",
            wo.id,
            payload,
        )

    if wo.asset_id is not None and "assetStatus" in payload and payload["assetStatus"] is not None:
        asset = db.get(Asset, wo.asset_id)
        new_status = _resolve_asset_status_val(payload["assetStatus"])
        if asset is not None and new_status is not None and asset.company_id == current_user.company_id:
            was_down = is_really_down(asset.status)
            now_down = is_really_down(new_status)
            if not was_down and now_down:
                trigger_asset_downtime(asset.id, db, user_id=current_user.id)
                asset.status = new_status
            elif was_down and not now_down:
                stop_asset_downtime(asset.id, db)
                asset.status = new_status
            else:
                asset.status = new_status
    if wo.status == 1 and wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
    if "status" in payload and wo.status != 1:
        _stop_running_labors_for_wo(wo, db)
    if wo.status == 3:
        _handle_wo_completion_side_effects(wo, current_user, db)
    elif "status" in payload:
        wo.completed_on = None
        wo.completed_by_id = None


def _after_create_wo(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    _sync_wo_relations(wo, payload, current_user, db)
    run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_CREATED, db)


def _after_patch_wo(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    _sync_wo_relations(wo, payload, current_user, db)
    if wo.status == 3:
        run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_CLOSED, db)
    if wo.archived:
        run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_ARCHIVED, db)


wo_router = build_crud_router(
    "/work-orders",
    WorkOrder,
    custom_serializer=_serialize_wo,
    before_create=_before_create_wo,
    after_create=_after_create_wo,
    after_patch=_after_patch_wo,
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
    part = db.get(Part, part_id)
    if not part:
        raise CustomException(status_code=404, message="Part not found")
    assert_company_access(current_user, part, is_super_admin=is_super_admin(current_user, db))
    wo_ids = db.scalars(
        select(PartQuantity.work_order_id).where(
            PartQuantity.part_id == part_id,
            PartQuantity.work_order_id.is_not(None),
            PartQuantity.company_id == part.company_id,
        )
    ).all()
    unique_ids = list(dict.fromkeys([wid for wid in wo_ids if wid is not None]))
    if not unique_ids:
        return []
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.id.in_(unique_ids),
            WorkOrder.company_id == part.company_id,
        )
    ).all()
    return [_serialize_wo(r, db) for r in rows]


@wo_router.patch("/files/{wo_id:int}/add")
def add_wo_files(
    wo_id: int,
    files: list[dict[str, Any] | int] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    existing_ids = set(
        db.scalars(
            select(work_order_files.c.files_id).where(work_order_files.c.work_order_id == wo.id)
        ).all()
    )
    for item in files:
        fid = item.get("id") if isinstance(item, dict) else item
        if isinstance(fid, int):
            fe = db.get(FileEntity, fid)
            if fe is None or fe.company_id != wo.company_id:
                raise CustomException(status_code=400, message=f"Invalid file reference {fid}")
            if fid not in existing_ids:
                db.execute(
                    work_order_files.insert().values(work_order_id=wo.id, files_id=fid)
                )
                existing_ids.add(fid)
    db.commit()
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
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    db.execute(
        delete(work_order_files).where(
            work_order_files.c.work_order_id == wo.id,
            work_order_files.c.files_id == file_id,
        )
    )
    db.execute(
        delete(t_work_order_file_associations).where(
            t_work_order_file_associations.c.id_work_order == wo.id,
            t_work_order_file_associations.c.id_file == file_id,
        )
    )
    db.commit()
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
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
    old_status = wo.status
    apply_patch(wo, payload)
    if wo.status == 3 and wo.required_signature and wo.signature_id is None:
        raise CustomException(
            status_code=406,
            message="Signature is required to complete this work order",
        )
    if wo.status == 1 and wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
    if old_status == 1 and wo.status != 1:
        _stop_running_labors_for_wo(wo, db)
    if wo.status == 3:  # COMPLETE = 3
        _handle_wo_completion_side_effects(wo, current_user, db)
        if old_status != 3:
            run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_CLOSED, db)
    elif old_status == 3:
        wo.completed_on = None
        wo.completed_by_id = None
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
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
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
def _before_create_labor(
    labor: Labor, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if labor.assigned_to_id is None:
        labor.assigned_to_id = current_user.id
    if labor.hourly_rate is None:
        assigned = db.get(User, labor.assigned_to_id) if labor.assigned_to_id else current_user
        labor.hourly_rate = int((assigned.rate if assigned else current_user.rate) or 0)
    if labor.status is None:
        labor.status = 0  # TimeStatus.STOPPED == 0
    if labor.logged is None:
        labor.logged = False


labors_router = build_crud_router("/labors", Labor, before_create=_before_create_labor)


def _toggle_labor_timer(
    wo: WorkOrder,
    should_start: bool,
    current_user: User,
    db: Session,
) -> Labor:
    now = utcnow()
    labor = db.scalar(
        select(Labor).where(
            Labor.work_order_id == wo.id,
            Labor.assigned_to_id == current_user.id,
            Labor.logged.is_(True),
        )
    )
    if labor is None:
        labor = db.scalar(
            select(Labor).where(
                Labor.work_order_id == wo.id,
                Labor.assigned_to_id == current_user.id,
            )
        )

    if should_start:
        if labor is None:
            labor = Labor(
                work_order_id=wo.id,
                assigned_to_id=current_user.id,
                company_id=wo.company_id,
                started_at=now,
                status=1,  # TimeStatus.RUNNING == 1
                duration=0,
                hourly_rate=int(current_user.rate or 0),
                include_to_total_time=True,
                logged=True,
                is_demo=False,
                created_by=current_user.id,
                updated_by=current_user.id,
            )
            db.add(labor)
        else:
            labor.started_at = now
            labor.status = 1  # TimeStatus.RUNNING == 1
            labor.logged = True
            labor.updated_by = current_user.id

        if wo.first_time_to_react is None:
            wo.first_time_to_react = now
        if (wo.status or 0) == 0:
            wo.status = 1  # IN_PROGRESS
    else:
        if labor is None:
            raise CustomException(status_code=404, message="Running labor timer not found")
        if labor.status == 1 and labor.started_at is not None:
            elapsed = max(0, int((now - ensure_utc(labor.started_at)).total_seconds()))
            labor.duration = int(labor.duration or 0) + elapsed
        labor.status = 0  # TimeStatus.STOPPED == 0
        labor.updated_by = current_user.id

    db.commit()
    db.refresh(labor)
    return labor


@labors_router.get("/work-order/{wo_id:int}")
def list_labors_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Labor).where(
            Labor.work_order_id == wo_id,
            Labor.company_id == wo.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


@labors_router.post("/work-order/{wo_id:int}")
def create_or_control_labor_for_wo(
    wo_id: int,
    start: bool | None = Query(default=None),
    payload: dict[str, Any] | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))

    if start is not None:
        labor = _toggle_labor_timer(wo, bool(start), current_user, db)
        return model_to_dict(labor, db=db)

    body = payload if isinstance(payload, dict) else {}
    labor = Labor()
    apply_patch(labor, body)
    labor.work_order_id = wo_id
    labor.company_id = wo.company_id
    if labor.assigned_to_id is None:
        labor.assigned_to_id = current_user.id
    if labor.hourly_rate is None:
        assigned = db.get(User, labor.assigned_to_id) if labor.assigned_to_id else current_user
        labor.hourly_rate = int((assigned.rate if assigned else current_user.rate) or 0)
    if "status" not in body or labor.status is None:
        labor.status = 0  # TimeStatus.STOPPED == 0
    if "logged" not in body or labor.logged is None:
        labor.logged = False
    apply_model_defaults(labor)
    db.add(labor)
    db.commit()
    db.refresh(labor)
    return model_to_dict(labor, db=db)


@labors_router.post("/controlling-time-timer")
def control_labor_timer(
    action: str = Query(default="START"),
    start: bool | None = Query(default=None),
    work_order_id: int = Query(default=0, alias="workOrderId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, work_order_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    should_start = bool(start) if start is not None else (action.strip().upper() != "STOP")
    labor = _toggle_labor_timer(wo, should_start, current_user, db)
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
def _serialize_schedule(sched: Schedule, db: Session) -> dict[str, Any]:
    sched_dict = model_to_dict(sched, db=db)
    sched_dict["daysOfWeek"] = get_schedule_days_of_week(sched.id, db) if sched.id else []
    return sched_dict


def _sync_schedule_days_of_week(
    sched: Schedule, sched_data: dict[str, Any], db: Session
) -> None:
    if "daysOfWeek" not in sched_data or not isinstance(sched_data["daysOfWeek"], list):
        return
    db.execute(
        delete(schedule_days_of_week).where(schedule_days_of_week.c.schedule_id == sched.id)
    )
    seen: set[int] = set()
    for raw in sched_data["daysOfWeek"]:
        d = normalize_day_of_week(raw)
        if d is not None and d not in seen:
            seen.add(d)
            db.execute(
                schedule_days_of_week.insert().values(schedule_id=sched.id, days_of_week=d)
            )


def _serialize_pm(pm: PreventiveMaintenance, db: Session) -> dict[str, Any]:
    res = model_to_dict(pm, db=db)

    assigned_ids = db.scalars(
        select(preventive_maintenance_assigned_to.c.assigned_to_id).where(
            preventive_maintenance_assigned_to.c.preventive_maintenance_id == pm.id
        )
    ).all()
    users = db.scalars(select(User).where(User.id.in_(assigned_ids))).all() if assigned_ids else []
    res["assignedTo"] = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]

    customer_ids = db.scalars(
        select(preventive_maintenance_customers.c.customers_id).where(
            preventive_maintenance_customers.c.preventive_maintenance_id == pm.id
        )
    ).all()
    customers = (
        db.scalars(select(Customer).where(Customer.id.in_(customer_ids))).all()
        if customer_ids
        else []
    )
    res["customers"] = [{"id": c.id, "name": c.name} for c in customers]

    file_ids = db.scalars(
        select(preventive_maintenance_files.c.files_id).where(
            preventive_maintenance_files.c.preventive_maintenance_id == pm.id
        )
    ).all()
    files = (
        db.scalars(select(FileEntity).where(FileEntity.id.in_(file_ids))).all()
        if file_ids
        else []
    )
    res["files"] = [model_to_dict(f, db=db) for f in files]

    res["customFieldValues"] = _hydrate_custom_field_values(
        db, CustomFieldValue.preventive_maintenance_id == pm.id
    )

    sched = None
    if pm.schedule_id:
        sched = db.get(Schedule, pm.schedule_id)
    if not sched:
        sched = db.scalar(select(Schedule).where(Schedule.preventive_maintenance_id == pm.id))
    if sched:
        sched_dict = _serialize_schedule(sched, db)
        res["schedule"] = sched_dict
        res["nextWorkOrderDate"] = sched_dict.get("startsOn")
    else:
        res["schedule"] = {
            "id": pm.id,
            "startsOn": res.get("createdAt"),
            "endsOn": None,
            "frequency": 7,
            "dueDateDelay": None,
            "disabled": False,
            "recurrenceType": "DAILY",
            "recurrenceBasedOn": "SCHEDULED_DATE",
            "daysOfWeek": [],
        }
        res["nextWorkOrderDate"] = res.get("createdAt")
    return res


def _sync_pm_relations(
    pm: PreventiveMaintenance, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if "assignedTo" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            preventive_maintenance_assigned_to,
            "preventive_maintenance_id",
            pm.id,
            "assigned_to_id",
            User,
            payload.get("assignedTo"),
        )
    if "customers" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            preventive_maintenance_customers,
            "preventive_maintenance_id",
            pm.id,
            "customers_id",
            Customer,
            payload.get("customers"),
        )
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            preventive_maintenance_files,
            "preventive_maintenance_id",
            pm.id,
            "files_id",
            FileEntity,
            payload.get("files"),
        )
    if "customFieldValues" in payload or "customFields" in payload:
        _sync_entity_custom_fields(
            db,
            current_user,
            "preventive_maintenance_id",
            pm.id,
            payload,
        )


def _after_create_pm(
    pm: PreventiveMaintenance, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not pm.custom_id:
        pm.custom_id = f"PM{pm.id:06d}"
    sched = db.scalar(select(Schedule).where(Schedule.preventive_maintenance_id == pm.id))
    sched_data = payload.get("schedule") if isinstance(payload.get("schedule"), dict) else {}
    if not sched:
        sched = Schedule(
            preventive_maintenance_id=pm.id,
            starts_on=utcnow(),
            frequency=int(sched_data.get("frequency") or 7),
            disabled=bool(sched_data.get("disabled", False)),
            recurrence_type=str(sched_data.get("recurrenceType") or "DAILY"),
            recurrence_based_on=str(sched_data.get("recurrenceBasedOn") or "SCHEDULED_DATE"),
            is_demo=False,
        )
        apply_patch(sched, sched_data)
        db.add(sched)
        db.flush()
    else:
        apply_patch(sched, sched_data)
    _sync_schedule_days_of_week(sched, sched_data, db)
    pm.schedule_id = sched.id
    _sync_pm_relations(pm, payload, current_user, db)


def _after_patch_pm(
    pm: PreventiveMaintenance, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    sched_data = payload.get("schedule")
    if isinstance(sched_data, dict):
        sched = (
            db.get(Schedule, pm.schedule_id)
            if pm.schedule_id
            else db.scalar(select(Schedule).where(Schedule.preventive_maintenance_id == pm.id))
        )
        if sched:
            apply_patch(sched, sched_data)
            _sync_schedule_days_of_week(sched, sched_data, db)
    _sync_pm_relations(pm, payload, current_user, db)


def _before_create_pm(
    pm: PreventiveMaintenance, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not pm.name and pm.title:
        pm.name = pm.title
    if not pm.title and pm.name:
        pm.title = pm.name


pm_router = build_crud_router(
    "/preventive-maintenances",
    PreventiveMaintenance,
    custom_serializer=_serialize_pm,
    before_create=_before_create_pm,
    after_create=_after_create_pm,
    after_patch=_after_patch_pm,
)


@pm_router.get("/{pm_id:int}/recent-work-orders")
def get_pm_recent_work_orders(
    pm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    pm = db.get(PreventiveMaintenance, pm_id)
    if not pm:
        raise CustomException(status_code=404, message="PreventiveMaintenance not found")
    assert_company_access(current_user, pm, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.parent_preventive_maintenance_id == pm_id,
            WorkOrder.company_id == pm.company_id,
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
    assert_company_access(current_user, pm, is_super_admin=is_super_admin(current_user, db))
    sched = (
        db.get(Schedule, pm.schedule_id)
        if pm.schedule_id
        else db.scalar(select(Schedule).where(Schedule.preventive_maintenance_id == pm.id))
    )
    wo = create_work_order_from_pm(
        pm, sched, db, created_by_id=current_user.id, now=utcnow()
    )
    db.commit()
    db.refresh(wo)
    return _serialize_wo(wo, db)


@pm_router.post("/workload")
def get_pm_workload(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    pms = db.scalars(
        select(PreventiveMaintenance).where(
            PreventiveMaintenance.company_id == current_user.company_id
        )
    ).all()
    return [_serialize_pm(pm, db) for pm in pms]


router.include_router(pm_router)


def _after_create_or_patch_schedule(
    sched: Schedule, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _sync_schedule_days_of_week(sched, payload, db)


schedules_router = build_crud_router(
    "/schedules",
    Schedule,
    custom_serializer=_serialize_schedule,
    after_create=_after_create_or_patch_schedule,
    after_patch=_after_create_or_patch_schedule,
)


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
    pm = (
        db.get(PreventiveMaintenance, sched.preventive_maintenance_id)
        if sched.preventive_maintenance_id is not None
        else db.scalar(
            select(PreventiveMaintenance).where(PreventiveMaintenance.schedule_id == sched.id)
        )
    )
    if pm is not None:
        assert_company_access(current_user, pm, is_super_admin=is_super_admin(current_user, db))
        if not can_edit_object(current_user, PermissionEntity.PREVENTIVE_MAINTENANCES, pm, db):
            raise CustomException(status_code=403, message="Access is denied")
    else:
        assert_company_access(current_user, sched, is_super_admin=is_super_admin(current_user, db))
    apply_patch(sched, payload)
    _sync_schedule_days_of_week(sched, payload, db)
    db.commit()
    db.refresh(sched)
    return _serialize_schedule(sched, db)


router.include_router(schedules_router)


# Workload endpoints
_WO_STATUS_NAMES = {0: "OPEN", 1: "IN_PROGRESS", 2: "ON_HOLD", 3: "COMPLETE"}
_WEEKDAY_NAMES = [
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
]


def _to_workload_wo_dto(wo: WorkOrder) -> dict[str, Any]:
    return {
        "id": wo.id,
        "customId": wo.custom_id or f"WO{wo.id:06d}",
        "title": wo.title,
        "status": _WO_STATUS_NAMES.get(wo.status or 0, "OPEN"),
        "estimatedDuration": float(wo.estimated_duration or 0.0),
        "estimatedStartDate": to_iso_utc(wo.estimated_start_date) if wo.estimated_start_date else "",
        "dueDate": to_iso_utc(wo.due_date) if wo.due_date else "",
    }


@router.get("/workload/overview")
def get_workload_overview(
    startDate: str | None = Query(default=None),
    endDate: str | None = Query(default=None),
    userIds: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    now = utcnow()
    start_dt = parse_iso_utc(startDate) if startDate else now
    end_dt = parse_iso_utc(endDate) if endDate else (start_dt + timedelta(days=6))
    if start_dt is None:
        start_dt = now
    if end_dt is None or end_dt < start_dt:
        end_dt = start_dt + timedelta(days=6)

    user_stmt = select(User).where(
        User.company_id == current_user.company_id,
        User.enabled.is_(True),
    )
    if userIds:
        parsed_ids = [
            int(part.strip()) for part in userIds.split(",") if part.strip().isdigit()
        ]
        if parsed_ids:
            user_stmt = user_stmt.where(User.id.in_(parsed_ids))
    users = list(db.scalars(user_stmt).all())

    wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == current_user.company_id,
                WorkOrder.status != 3,
            )
        ).all()
    )

    days_list: list[dict[str, Any]] = []
    total_team_cap = 0
    total_team_alloc = 0
    num_days = max(1, min(60, (end_dt.date() - start_dt.date()).days + 1))

    for offset in range(num_days):
        day_date = (start_dt + timedelta(days=offset)).date()
        date_str = day_date.strftime("%Y-%m-%d")
        dow_name = _WEEKDAY_NAMES[day_date.weekday()]
        is_weekend = day_date.weekday() >= 5
        default_cap = 0 if is_weekend else 480

        day_users: list[dict[str, Any]] = []
        day_cap = 0
        day_alloc = 0

        for u in users:
            u_wos: list[dict[str, Any]] = []
            u_alloc = 0
            for w in wos:
                target_dt = w.estimated_start_date or w.due_date
                if (
                    w.primary_user_id == u.id
                    and target_dt is not None
                    and ensure_utc(target_dt).date() == day_date
                ):
                    u_wos.append(_to_workload_wo_dto(w))
                    u_alloc += int(round(float(w.estimated_duration or 0.0) * 60))

            day_cap += default_cap
            day_alloc += u_alloc
            day_users.append(
                {
                    "userId": u.id,
                    "fullName": f"{u.first_name or ''} {u.last_name or ''}".strip(),
                    "capacityMinutes": default_cap,
                    "allocatedMinutes": u_alloc,
                    "workOrders": u_wos,
                }
            )

        total_team_cap += day_cap
        total_team_alloc += day_alloc
        days_list.append(
            {
                "date": date_str,
                "dayOfWeek": dow_name,
                "teamCapacityMinutes": day_cap,
                "teamAllocatedMinutes": day_alloc,
                "users": day_users,
            }
        )

    return {
        "startDate": start_dt.date().strftime("%Y-%m-%d"),
        "endDate": end_dt.date().strftime("%Y-%m-%d"),
        "teamCapacityMinutes": total_team_cap,
        "teamAllocatedMinutes": total_team_alloc,
        "days": days_list,
        "users": [
            {"id": u.id, "firstName": u.first_name, "lastName": u.last_name}
            for u in users
        ],
    }


@router.get("/workload/unscheduled")
def get_workload_unscheduled(
    statuses: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == current_user.company_id,
                WorkOrder.estimated_start_date.is_(None),
                WorkOrder.status != 3,
            )
        ).all()
    )
    if statuses:
        allowed = {s.strip().upper() for s in statuses.split(",") if s.strip()}
        rows = [
            r for r in rows if _WO_STATUS_NAMES.get(r.status or 0, "OPEN") in allowed
        ]

    now = utcnow()
    soon_cutoff = now + timedelta(days=3)
    status_counts: dict[str, int] = {}
    overdue_count = 0
    due_soon_count = 0
    wo_dtos: list[dict[str, Any]] = []

    for r in rows:
        st_name = _WO_STATUS_NAMES.get(r.status or 0, "OPEN")
        status_counts[st_name] = status_counts.get(st_name, 0) + 1
        if r.due_date is not None:
            due_utc = ensure_utc(r.due_date)
            if due_utc < now:
                overdue_count += 1
            elif due_utc <= soon_cutoff:
                due_soon_count += 1
        wo_dtos.append(_to_workload_wo_dto(r))

    return {
        "statusCounts": status_counts,
        "overdueCount": overdue_count,
        "dueSoonCount": due_soon_count,
        "workOrders": wo_dtos,
    }


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
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))

    if "localDate" in payload:
        local_date = payload.get("localDate")
        wo.estimated_start_date = parse_iso_utc(local_date) if local_date else None
    elif "estimatedStartDate" in payload:
        est = payload.get("estimatedStartDate")
        wo.estimated_start_date = parse_iso_utc(est) if est else None

    if "primaryUserId" in payload:
        puid = payload.get("primaryUserId")
        if puid is not None:
            pu_check = db.get(User, int(puid))
            if pu_check is None or pu_check.company_id != wo.company_id:
                raise CustomException(status_code=400, message="Invalid primaryUserId")
            wo.primary_user_id = int(puid)
        else:
            wo.primary_user_id = None

    if "estimatedDuration" in payload and payload.get("estimatedDuration") is not None:
        wo.estimated_duration = float(payload["estimatedDuration"])

    if "dueDate" in payload:
        dd = payload.get("dueDate")
        wo.due_date = parse_iso_utc(dd) if dd else None

    db.commit()
    db.refresh(wo)
    pu = db.get(User, wo.primary_user_id) if wo.primary_user_id else None
    res = _serialize_wo(wo, db)
    res["userId"] = pu.id if pu else None
    res["userFirstName"] = pu.first_name if pu else ""
    res["userLastName"] = pu.last_name if pu else ""
    res["estimatedStartDate"] = (
        to_iso_utc(wo.estimated_start_date) if wo.estimated_start_date else None
    )
    return res

