"""Routes for WorkOrders, WorkOrderHistories, Labors, Relations, PreventiveMaintenances, Schedules."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any
from ajnkit.email import EmailRefused, send as send_email
from fastapi import APIRouter, Body, Depends, Query, Response
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.deps.permissions import can_create, can_edit_object, can_view
from src.jobs.pm_generator import (
    advance_schedule_next_due_date,
    create_work_order_from_pm,
    get_schedule_days_of_week,
    normalize_day_of_week,
)
from src.models._base import utcnow
from src.models.associations import (
    comment_files,
    preventive_maintenance_assigned_to,
    preventive_maintenance_customers,
    preventive_maintenance_files,
    schedule_days_of_week,
    t_work_order_file_associations,
    work_order_assigned_to,
    work_order_customers,
    work_order_files,
    work_order_meter_trigger_assigned_to,
    work_order_meter_trigger_customers,
    work_order_meter_trigger_files,
)
from src.models.categories import WorkOrderCategory
from src.models.company import Company
from src.models.enums import PermissionEntity, WFMainCondition
from src.models.files_custom import CustomFieldValue, File as FileEntity
from src.models.location_asset import Asset, Location
from src.models.meters import WorkOrderMeterTrigger
from src.models.parts_po import AdditionalCost, Customer, Part, PartQuantity
from src.models.pm_schedule import PreventiveMaintenance, Schedule
from src.models.settings import FieldConfiguration, GeneralPreferences, WorkOrderConfiguration
from src.models.tasks import Task
from src.models.users import Team, User
from src.models.work_orders import (
    Comment,
    Labor,
    Relation,
    WorkOrder,
    WorkOrderHistory,
)
from src.pdf.work_order_pdf import render_work_order_pdf
from src.routes._crud import (
    apply_model_defaults,
    build_crud_router,
    validate_foreign_key_ownership,
)
from src.routes.assets_locations import (
    _hydrate_custom_field_values,
    _sync_entity_custom_fields,
    _verify_and_sync_m2m,
)
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict, resolve_enum_value
from src.services.workflow_engine import run_work_order_workflows
from src.utils.dates import ensure_utc, parse_iso_utc, to_iso_utc
from src.utils.search import SearchCriteria, apply_search_criteria, execute_search

router = APIRouter()
logger = logging.getLogger(__name__)


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
    if wo.primary_user_id is None and current_user.company_id is not None:
        comp = db.get(Company, current_user.company_id)
        if comp and comp.company_settings_id:
            gp = db.scalar(
                select(GeneralPreferences).where(
                    GeneralPreferences.company_settings_id == comp.company_settings_id
                )
            )
            if gp and gp.auto_assign_work_orders:
                wo.primary_user_id = current_user.id


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
                WorkOrder.archived.is_(False),
            )
        )
        if other_incomplete is None:
            stop_asset_downtime(wo.asset_id, db)
            asset = db.get(Asset, wo.asset_id)
            if asset is not None:
                asset.status = 0  # OPERATIONAL

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


def _notify_wo_assignees(
    wo: WorkOrder, current_user: User, db: Session, *, message: str
) -> None:
    from src.models.enums import NotificationType
    from src.services.notifications import create_in_app_notifications

    assigned_ids = list(
        db.scalars(
            select(work_order_assigned_to.c.assigned_to_id).where(
                work_order_assigned_to.c.work_order_id == wo.id
            )
        ).all()
    )
    if wo.primary_user_id is not None:
        assigned_ids.append(wo.primary_user_id)
    create_in_app_notifications(
        db,
        user_ids=assigned_ids,
        team_ids=[wo.team_id] if wo.team_id else (),
        message=message,
        notification_type=NotificationType.WORK_ORDER,
        resource_id=wo.id,
        exclude_user_id=current_user.id,
        created_by=current_user.id,
    )


def _after_create_wo(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    _sync_wo_relations(wo, payload, current_user, db)
    _notify_wo_assignees(
        wo,
        current_user,
        db,
        message=f"You have been assigned to work order {wo.title}",
    )
    run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_CREATED, db)


def _after_patch_wo(wo: WorkOrder, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
    _sync_wo_relations(wo, payload, current_user, db)
    if any(k in payload for k in ("primaryUser", "assignedTo", "team", "status")):
        _notify_wo_assignees(
            wo,
            current_user,
            db,
            message=f"Work order {wo.title} has been updated",
        )
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
    cutoff = utcnow() + timedelta(days=2)
    rows = db.scalars(
        select(WorkOrder).where(
            WorkOrder.company_id == current_user.company_id,
            WorkOrder.archived.is_(False),
            WorkOrder.status != 3,
            (WorkOrder.priority == 3)
            | ((WorkOrder.due_date.is_not(None)) & (WorkOrder.due_date <= cutoff)),
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


def _naive_utc(dt: datetime) -> datetime:
    return ensure_utc(dt).replace(tzinfo=None)


def _optional_company_id(raw: str | None) -> int | None:
    """Treat a missing or blank companyId query as 'the caller's company'."""
    if raw is None or not str(raw).strip():
        return None
    try:
        return int(str(raw).strip())
    except ValueError as exc:
        raise CustomException(status_code=422, message="Invalid companyId") from exc


def _event_bounds(
    start: datetime | None, due: datetime | None, hours: float | None
) -> tuple[datetime, datetime] | None:
    duration = timedelta(hours=float(hours or 0))
    if duration <= timedelta(0):
        duration = timedelta(hours=1)
    if start is not None:
        return start, start + duration
    if due is not None:
        return due - duration, due
    return None


def _calendar_subject(obj: Any, model_name: str) -> dict[str, Any]:
    title = getattr(obj, "title", None) or getattr(obj, "name", None) or ""
    return {
        "id": obj.id,
        "title": title,
        "description": getattr(obj, "description", None),
        "priority": resolve_enum_value("priority", getattr(obj, "priority", None), model_name),
        "status": resolve_enum_value("status", getattr(obj, "status", None), model_name),
    }


def _schedule_fires(
    schedule: Schedule, db: Session, window_start: datetime, window_end: datetime
) -> list[datetime]:
    if schedule.disabled or schedule.starts_on is None:
        return []
    cursor = _naive_utc(schedule.starts_on)
    end_cap = _naive_utc(schedule.ends_on) if schedule.ends_on is not None else None
    fires: list[datetime] = []
    for _ in range(400):
        if cursor > window_end:
            break
        if cursor >= window_start and (end_cap is None or cursor <= end_cap):
            fires.append(cursor)
        nxt = advance_schedule_next_due_date(schedule, cursor, db)
        nxt = _naive_utc(nxt)
        if nxt <= cursor:
            break
        cursor = nxt
    return fires


@wo_router.post("/events")
def get_wo_events(
    payload: dict[str, Any] = Body(default_factory=dict),
    company_id: str | None = Query(default=None, alias="companyId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Work-order and preventive-maintenance events for the visible calendar range.

    An empty ``companyId`` query (the React calendar sends ``companyId=`` when no
    company filter is selected) is the caller's own company. Each event includes
    both ``date`` and ``endDate`` so FullCalendar can place it.
    """
    if not can_view(current_user, PermissionEntity.WORK_ORDERS, db):
        raise CustomException(status_code=403, message="Access Denied")

    requested_company = _optional_company_id(company_id)
    target_company = current_user.company_id
    if requested_company is not None and requested_company != current_user.company_id:
        if not is_super_admin(current_user, db):
            raise CustomException(status_code=403, message="Access denied")
        target_company = requested_company

    start = parse_iso_utc(payload.get("start"))
    end = parse_iso_utc(payload.get("end"))
    if start is None or end is None:
        raise CustomException(status_code=400, message="start and end are required")
    range_start = _naive_utc(start)
    range_end = _naive_utc(end)
    if range_end < range_start:
        raise CustomException(status_code=400, message="end is before start")

    criteria = SearchCriteria.model_validate(
        {"filterFields": payload.get("filterFields") or []}
    )
    in_range = or_(
        and_(
            WorkOrder.estimated_start_date.is_not(None),
            WorkOrder.estimated_start_date >= range_start,
            WorkOrder.estimated_start_date <= range_end,
        ),
        and_(
            WorkOrder.estimated_start_date.is_(None),
            WorkOrder.due_date.is_not(None),
            WorkOrder.due_date >= range_start,
            WorkOrder.due_date <= range_end,
        ),
    )
    stmt = apply_search_criteria(
        select(WorkOrder).where(in_range),
        WorkOrder,
        criteria,
        company_id=target_company,
        paginate=False,
    )
    rows = db.scalars(stmt).unique().all()

    events: list[dict[str, Any]] = []
    for wo in rows:
        bounds = _event_bounds(wo.estimated_start_date, wo.due_date, wo.estimated_duration)
        if bounds is None:
            continue
        event_start, event_end = bounds
        events.append(
            {
                "type": "WORK_ORDER",
                "date": to_iso_utc(event_start),
                "endDate": to_iso_utc(event_end),
                "event": _calendar_subject(wo, "WorkOrder"),
            }
        )

    now = _naive_utc(utcnow())
    pm_window_start = max(range_start, now)
    if pm_window_start <= range_end and can_view(
        current_user, PermissionEntity.PREVENTIVE_MAINTENANCES, db
    ):
        pms = db.scalars(
            select(PreventiveMaintenance).where(
                PreventiveMaintenance.company_id == target_company
            )
        ).all()
        for pm in pms:
            if pm.created_at is not None and _naive_utc(pm.created_at) > range_end:
                continue
            schedule = (
                db.get(Schedule, pm.schedule_id) if pm.schedule_id is not None else None
            )
            if schedule is None and pm.id is not None:
                schedule = db.scalar(
                    select(Schedule).where(Schedule.preventive_maintenance_id == pm.id)
                )
            if schedule is None:
                continue
            delay = timedelta(days=int(schedule.due_date_delay or 0))
            for fire in _schedule_fires(schedule, db, pm_window_start, range_end):
                event_end = fire + delay
                duration = timedelta(hours=float(pm.estimated_duration or 0))
                if duration <= timedelta(0):
                    duration = timedelta(hours=1)
                event_start = event_end - duration
                events.append(
                    {
                        "type": "PREVENTIVE_MAINTENANCE",
                        "date": to_iso_utc(event_start),
                        "endDate": to_iso_utc(event_end),
                        "event": _calendar_subject(pm, "PreventiveMaintenance"),
                    }
                )
    return events


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
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
    existing_ids = set(
        db.scalars(
            select(work_order_files.c.files_id).where(work_order_files.c.work_order_id == wo.id)
        ).all()
    )
    added_files: list[FileEntity] = []
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
            added_files.append(fe)
    if wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
    db.commit()
    return [model_to_dict(f, db=db) for f in added_files]


@wo_router.delete("/files/{wo_id:int}/{file_id:int}/remove")
def remove_wo_file(
    wo_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
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
    return _serialize_wo(wo, db)["files"]


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
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wo = db.get(WorkOrder, wo_id)
    if wo is None:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_view(current_user, PermissionEntity.WORK_ORDERS, db):
        raise CustomException(status_code=403, message="Access is denied")

    requested = payload.get("customers")
    if not isinstance(requested, list) or not requested:
        raise CustomException(status_code=400, message="At least one customer is required")
    customer_ids = list(
        dict.fromkeys(
            item.get("id") for item in requested if isinstance(item, dict) and isinstance(item.get("id"), int)
        )
    )
    if not customer_ids or len(customer_ids) != len(requested):
        raise CustomException(status_code=400, message="Every customer must have a valid id")
    if len(customer_ids) > 20:
        raise CustomException(status_code=400, message="A report can be sent to at most 20 customers")

    customers = db.scalars(
        select(Customer).where(
            Customer.id.in_(customer_ids),
            Customer.company_id == wo.company_id,
        )
    ).all()
    by_id = {customer.id: customer for customer in customers}
    missing = [customer_id for customer_id in customer_ids if customer_id not in by_id]
    if missing:
        raise CustomException(status_code=400, message="A selected customer is not available")
    addresses = [by_id[customer_id].email for customer_id in customer_ids]
    if any(not address for address in addresses):
        raise CustomException(
            status_code=400,
            message="Every selected customer must have an email address",
        )

    summary = _work_order_email_summary(wo, payload, db)
    try:
        left = send_email(
            [str(address) for address in addresses],
            f"AJ CAFM work order: {wo.title}"[:200],
            summary,
        )
    except EmailRefused as exc:
        logger.warning("work-order report email refused for work_order_id=%s", wo.id)
        return SuccessResponse(success=False, message=str(exc)).model_dump()
    return SuccessResponse(
        success=True,
        message=f"Report sent; {left} recipient slots remain this hour",
    ).model_dump()


def _work_order_email_summary(
    wo: WorkOrder, payload: dict[str, Any], db: Session
) -> str:
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    lines = [f"Work order: {wo.title}", f"ID: {wo.custom_id or f'WO{wo.id:06d}'}"]
    if config.get("workOrderInformation", True):
        lines.extend(
            [
                f"Status: {resolve_enum_value('status', wo.status, 'WorkOrder')}",
                f"Description: {wo.description or '—'}",
                f"Due: {to_iso_utc(wo.due_date) or '—'}",
            ]
        )
    if config.get("priority", True):
        lines.append(f"Priority: {resolve_enum_value('priority', wo.priority, 'WorkOrder')}")
    if config.get("estimatedTime", True):
        lines.append(f"Estimated duration: {float(wo.estimated_duration or 0):g} hours")
    if config.get("locationAddress", True) and wo.location_id:
        location = db.get(Location, wo.location_id)
        if location:
            lines.append(f"Location: {location.name} — {location.address or 'no address'}")
    if wo.asset_id:
        asset = db.get(Asset, wo.asset_id)
        if asset:
            lines.append(f"Asset: {asset.name}")
    custom_message = payload.get("message")
    if isinstance(custom_message, str) and custom_message.strip():
        lines.extend(["", custom_message.strip()])
    lines.extend(["", "Sent by AJ CAFM · Powered by Canvas"])
    return "\n".join(lines)


def _required_completion_fields(wo: WorkOrder, db: Session) -> set[str]:
    company = db.get(Company, wo.company_id)
    if company is None or company.company_settings_id is None:
        return set()
    configuration = db.scalar(
        select(WorkOrderConfiguration).where(
            WorkOrderConfiguration.company_settings_id == company.company_settings_id
        )
    )
    if configuration is None:
        return set()
    rows = db.scalars(
        select(FieldConfiguration).where(
            FieldConfiguration.work_order_configuration_id == configuration.id,
            FieldConfiguration.field_type == 2,  # REQUIRED
        )
    ).all()
    return {row.field_name for row in rows}


def _enforce_completion_guards(wo: WorkOrder, db: Session) -> None:
    required = _required_completion_fields(wo, db)
    if not required:
        return

    if "completeFiles" in required:
        work_order_file_count = len(
            set(
                db.scalars(
                    select(work_order_files.c.files_id).where(
                        work_order_files.c.work_order_id == wo.id
                    )
                ).all()
            )
            | set(
                db.scalars(
                    select(t_work_order_file_associations.c.id_file).where(
                        t_work_order_file_associations.c.id_work_order == wo.id
                    )
                ).all()
            )
        )
        comment_file_count = db.scalar(
            select(func.count())
            .select_from(comment_files)
            .join(Comment, Comment.id == comment_files.c.comment_id)
            .where(Comment.work_order_id == wo.id)
        ) or 0
        if work_order_file_count + comment_file_count == 0:
            raise CustomException(
                status_code=406,
                message="A file is required to complete this work order",
            )

    if "completeTasks" in required:
        tasks = db.scalars(select(Task).where(Task.work_order_id == wo.id)).all()
        if any(not str(task.value or "").strip() for task in tasks):
            raise CustomException(
                status_code=406,
                message="All tasks must be completed before closing this work order",
            )

    if "completeTime" in required:
        time_count = db.scalar(
            select(func.count()).select_from(Labor).where(
                Labor.work_order_id == wo.id,
                Labor.duration > 0,
            )
        ) or 0
        if time_count == 0:
            raise CustomException(
                status_code=406,
                message="Logged time is required to complete this work order",
            )

    if "completeParts" in required:
        part_count = db.scalar(
            select(func.count()).select_from(PartQuantity).where(
                PartQuantity.work_order_id == wo.id
            )
        ) or 0
        if part_count == 0:
            raise CustomException(
                status_code=406,
                message="A part is required to complete this work order",
            )

    if "completeCost" in required:
        cost_count = db.scalar(
            select(func.count()).select_from(AdditionalCost).where(
                AdditionalCost.work_order_id == wo.id
            )
        ) or 0
        if cost_count == 0:
            raise CustomException(
                status_code=406,
                message="An additional cost is required to complete this work order",
            )


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
    sig_raw = payload.get("signature")
    if isinstance(sig_raw, str) and sig_raw.strip():
        sig_file = FileEntity(
            name="signature.png",
            path=sig_raw.strip(),
            company_id=wo.company_id,
            created_by=current_user.id,
            updated_by=current_user.id,
            type=0,
            is_demo=False,
        )
        db.add(sig_file)
        db.flush()
        wo.signature_id = sig_file.id
    patch_data = {k: v for k, v in payload.items() if not (k == "signature" and isinstance(v, str))}
    apply_patch(wo, patch_data)
    validate_foreign_key_ownership(wo, current_user, db)
    if wo.status == 3 and wo.required_signature and wo.signature_id is None:
        raise CustomException(
            status_code=406,
            message="Signature is required to complete this work order",
        )
    if wo.status == 3:
        _enforce_completion_guards(wo, db)
    if wo.status != 2 and wo.first_time_to_react is None:
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
def _hydrate_user_mini_with_image(u: User | None, db: Session) -> dict[str, Any] | None:
    if u is None:
        return None
    img = db.get(FileEntity, u.image_id) if getattr(u, "image_id", None) else None
    return {
        "id": u.id,
        "firstName": u.first_name,
        "lastName": u.last_name,
        "email": u.email,
        "jobTitle": u.job_title,
        "hourlyRate": u.rate,
        "image": model_to_dict(img, db=db) if img else None,
    }


def _serialize_comment(c: Comment, db: Session) -> dict[str, Any]:
    res = model_to_dict(c, db=db)
    u = db.get(User, c.user_id) if c.user_id else None
    user_dto = _hydrate_user_mini_with_image(u, db)
    if user_dto:
        res["user"] = user_dto
        res["createdBy"] = user_dto
    res["text"] = c.content or ""
    res["system"] = False
    file_ids = db.scalars(
        select(comment_files.c.files_id).where(comment_files.c.comment_id == c.id)
    ).all()
    files = (
        db.scalars(select(FileEntity).where(FileEntity.id.in_(file_ids))).all()
        if file_ids
        else []
    )
    res["files"] = [model_to_dict(f, db=db) for f in files]
    return res


def _before_create_comment(c: Comment, payload: dict[str, Any], current_user: User, db: Session) -> None:
    c.user_id = current_user.id
    if not c.content:
        c.content = payload.get("content") or payload.get("text") or ""
    if c.work_order_id:
        wo = db.get(WorkOrder, c.work_order_id)
        if wo is None:
            raise CustomException(status_code=404, message="WorkOrder not found")
        assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
        if wo.first_time_to_react is None:
            wo.first_time_to_react = utcnow()


def _before_patch_comment(c: Comment, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if c.user_id != current_user.id and not is_super_admin(current_user, db):
        raise CustomException(status_code=403, message="Access is denied")
    if "text" in payload and "content" not in payload:
        c.content = str(payload["text"] or "")


def _before_delete_comment(c: Comment, current_user: User, db: Session) -> None:
    if c.user_id != current_user.id and not is_super_admin(current_user, db):
        raise CustomException(status_code=403, message="Access is denied")


def _after_save_comment(c: Comment, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            comment_files,
            "comment_id",
            c.id,
            "files_id",
            FileEntity,
            payload.get("files"),
        )


comments_router = build_crud_router(
    "/comments",
    Comment,
    custom_serializer=_serialize_comment,
    before_create=_before_create_comment,
    after_create=_after_save_comment,
    before_patch=_before_patch_comment,
    after_patch=_after_save_comment,
    before_delete=_before_delete_comment,
)


@comments_router.post("/search/{wo_id:int}")
def search_comments_by_wo(
    wo_id: int,
    criteria: SearchCriteria = Body(default_factory=SearchCriteria),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Comment).where(
            Comment.work_order_id == wo_id,
            Comment.company_id == wo.company_id,
        )
    ).all()
    items: list[dict[str, Any]] = [_serialize_comment(r, db) for r in rows]
    histories = db.scalars(
        select(WorkOrderHistory).where(WorkOrderHistory.work_order_id == wo_id)
    ).all()
    for h in histories:
        hu = db.get(User, h.user_id) if h.user_id else None
        user_dto = _hydrate_user_mini_with_image(hu, db)
        items.append(
            {
                "id": h.id,
                "text": h.name or "",
                "content": h.name or "",
                "user": user_dto,
                "createdBy": user_dto,
                "createdAt": to_iso_utc(h.created_at),
                "updatedAt": to_iso_utc(h.updated_at),
                "files": [],
                "system": True,
            }
        )
    items.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return items


@comments_router.get("/count/{wo_id:int}")
def count_comments_by_wo(
    wo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    wo = db.get(WorkOrder, wo_id)
    if not wo:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Comment).where(
            Comment.work_order_id == wo_id,
            Comment.company_id == wo.company_id,
        )
    ).all()
    comment_ids = [r.id for r in rows if r.id is not None]
    with_files_ids = (
        set(
            db.scalars(
                select(comment_files.c.comment_id).where(
                    comment_files.c.comment_id.in_(comment_ids)
                )
            ).all()
        )
        if comment_ids
        else set()
    )
    return {"count": len(rows), "withFilesCount": len(with_files_ids)}


router.include_router(comments_router)

# Labors
def _assert_wo_edit_for_labor(labor: Labor, current_user: User, db: Session) -> WorkOrder | None:
    if labor.work_order_id is None:
        return None
    wo = db.get(WorkOrder, labor.work_order_id)
    if wo is None:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
    return wo


def _before_create_labor(
    labor: Labor, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    wo = _assert_wo_edit_for_labor(labor, current_user, db)
    if wo is not None and wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
    if labor.assigned_to_id is None:
        labor.assigned_to_id = current_user.id
    if labor.hourly_rate is None:
        assigned = db.get(User, labor.assigned_to_id) if labor.assigned_to_id else current_user
        labor.hourly_rate = int((assigned.rate if assigned else current_user.rate) or 0)
    if labor.status is None:
        labor.status = 0  # TimeStatus.STOPPED == 0
    if labor.logged is None:
        labor.logged = False


def _before_patch_labor(
    labor: Labor, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _assert_wo_edit_for_labor(labor, current_user, db)


def _before_delete_labor(labor: Labor, current_user: User, db: Session) -> None:
    _assert_wo_edit_for_labor(labor, current_user, db)


labors_router = build_crud_router(
    "/labors",
    Labor,
    before_create=_before_create_labor,
    before_patch=_before_patch_labor,
    before_delete=_before_delete_labor,
)


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
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")

    if start is not None:
        labor = _toggle_labor_timer(wo, bool(start), current_user, db)
        return model_to_dict(labor, db=db)

    body = payload if isinstance(payload, dict) else {}
    labor = Labor()
    apply_patch(labor, body)
    labor.work_order_id = wo_id
    labor.company_id = wo.company_id
    labor.created_by = current_user.id
    if labor.assigned_to_id is None:
        labor.assigned_to_id = current_user.id
    validate_foreign_key_ownership(labor, current_user, db)
    if labor.hourly_rate is None:
        assigned = db.get(User, labor.assigned_to_id) if labor.assigned_to_id else current_user
        labor.hourly_rate = int((assigned.rate if assigned else current_user.rate) or 0)
    if "status" not in body or labor.status is None:
        labor.status = 0  # TimeStatus.STOPPED == 0
    if "logged" not in body or labor.logged is None:
        labor.logged = False
    if wo.first_time_to_react is None:
        wo.first_time_to_react = utcnow()
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
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")
    should_start = bool(start) if start is not None else (action.strip().upper() != "STOP")
    labor = _toggle_labor_timer(wo, should_start, current_user, db)
    return model_to_dict(labor, db=db)


router.include_router(labors_router)

# Relations
def _before_create_relation(
    rel: Relation, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if rel.parent_id is None or rel.child_id is None:
        raise CustomException(status_code=400, message="Both parent and child work orders are required")
    if rel.parent_id == rel.child_id:
        raise CustomException(
            status_code=406, message="Parent and child work orders cannot be the same"
        )
    parent_wo = db.get(WorkOrder, rel.parent_id)
    child_wo = db.get(WorkOrder, rel.child_id)
    if parent_wo is None or child_wo is None:
        raise CustomException(status_code=404, message="WorkOrder not found")
    assert_company_access(current_user, parent_wo, is_super_admin=is_super_admin(current_user, db))
    assert_company_access(current_user, child_wo, is_super_admin=is_super_admin(current_user, db))
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, parent_wo, db):
        raise CustomException(status_code=403, message="Access is denied")

    # Normalize inverse relation types (matching Java RelationService.createPost):
    # 5 (BLOCKED_BY) -> 6 (BLOCKS), 1 (DUPLICATED_BY) -> 0 (DUPLICATE_OF), 3 (SPLIT_TO) -> 4 (SPLIT_FROM)
    if rel.relation_type == 5:
        rel.parent_id, rel.child_id = rel.child_id, rel.parent_id
        rel.relation_type = 6
    elif rel.relation_type == 1:
        rel.parent_id, rel.child_id = rel.child_id, rel.parent_id
        rel.relation_type = 0
    elif rel.relation_type == 3:
        rel.parent_id, rel.child_id = rel.child_id, rel.parent_id
        rel.relation_type = 4

    existing = db.scalar(
        select(Relation.id).where(
            ((Relation.parent_id == rel.parent_id) & (Relation.child_id == rel.child_id))
            | ((Relation.parent_id == rel.child_id) & (Relation.child_id == rel.parent_id))
        )
    )
    if existing is not None:
        raise CustomException(
            status_code=406,
            message="A relation between these two work orders already exists",
        )


relations_router = build_crud_router(
    "/relations",
    Relation,
    before_create=_before_create_relation,
)


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


def _serialize_womt(t: WorkOrderMeterTrigger, db: Session) -> dict[str, Any]:
    res = model_to_dict(t, db=db)
    assigned_ids = db.scalars(
        select(work_order_meter_trigger_assigned_to.c.assigned_to_id).where(
            work_order_meter_trigger_assigned_to.c.work_order_meter_trigger_id == t.id
        )
    ).all()
    users = db.scalars(select(User).where(User.id.in_(assigned_ids))).all() if assigned_ids else []
    res["assignedTo"] = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]
    customer_ids = db.scalars(
        select(work_order_meter_trigger_customers.c.customers_id).where(
            work_order_meter_trigger_customers.c.work_order_meter_trigger_id == t.id
        )
    ).all()
    customers = (
        db.scalars(select(Customer).where(Customer.id.in_(customer_ids))).all()
        if customer_ids
        else []
    )
    res["customers"] = [{"id": c.id, "name": c.name} for c in customers]
    file_ids = db.scalars(
        select(work_order_meter_trigger_files.c.files_id).where(
            work_order_meter_trigger_files.c.work_order_meter_trigger_id == t.id
        )
    ).all()
    files = (
        db.scalars(select(FileEntity).where(FileEntity.id.in_(file_ids))).all()
        if file_ids
        else []
    )
    res["files"] = [model_to_dict(f, db=db) for f in files]
    return res


def _sync_womt_relations(
    t: WorkOrderMeterTrigger, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if "assignedTo" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            work_order_meter_trigger_assigned_to,
            "work_order_meter_trigger_id",
            t.id,
            "assigned_to_id",
            User,
            payload.get("assignedTo"),
        )
    if "customers" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            work_order_meter_trigger_customers,
            "work_order_meter_trigger_id",
            t.id,
            "customers_id",
            Customer,
            payload.get("customers"),
        )
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            work_order_meter_trigger_files,
            "work_order_meter_trigger_id",
            t.id,
            "files_id",
            FileEntity,
            payload.get("files"),
        )


womt_router = build_crud_router(
    "/work-order-meter-triggers",
    WorkOrderMeterTrigger,
    custom_serializer=_serialize_womt,
    after_create=_sync_womt_relations,
    after_patch=_sync_womt_relations,
)


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
    return [_serialize_womt(r, db) for r in rows]


router.include_router(womt_router)


# 6.12 PreventiveMaintenances & Schedules
def _serialize_schedule(sched: Schedule, db: Session) -> dict[str, Any]:
    sched_dict = model_to_dict(sched, db=db)
    sched_dict["nextDueDate"] = sched_dict.get("startsOn")
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


def _extract_pm_schedule_data(payload: dict[str, Any]) -> dict[str, Any]:
    sched_data: dict[str, Any] = {}
    nested = payload.get("schedule")
    if isinstance(nested, dict):
        sched_data.update(nested)
    for k in (
        "startsOn",
        "endsOn",
        "frequency",
        "dueDateDelay",
        "recurrenceType",
        "recurrenceBasedOn",
        "daysOfWeek",
        "disabled",
    ):
        if k in payload and payload[k] is not None and k not in sched_data:
            sched_data[k] = payload[k]
    return sched_data


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
    sched_data = _extract_pm_schedule_data(payload)
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
    sched_data = _extract_pm_schedule_data(payload)
    if sched_data:
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
    if not can_edit_object(
        current_user, PermissionEntity.PREVENTIVE_MAINTENANCES, pm, db
    ) or not can_create(current_user, PermissionEntity.WORK_ORDERS, db):
        raise CustomException(status_code=403, message="Access is denied")
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
    if not can_edit_object(current_user, PermissionEntity.WORK_ORDERS, wo, db):
        raise CustomException(status_code=403, message="Access is denied")

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

    validate_foreign_key_ownership(wo, current_user, db)
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

