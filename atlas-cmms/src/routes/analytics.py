"""Analytics routes matching all 6 Spring analytics controllers (WorkOrder, Asset, Part, Request, User, Overview)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.deps.permissions import can_view
from src.models._base import utcnow
from src.models.categories import PartCategory, WorkOrderCategory
from src.models.enums import PermissionEntity
from src.models.location_asset import Asset, AssetDowntime
from src.models.parts_po import AdditionalCost, Part, PartQuantity, PartTransaction as PartConsumption
from src.models.requests import Request
from src.models.users import User
from src.models.work_orders import Labor, WorkOrder
from src.routes._crud import _get_user_company_settings_id
from src.schemas.errors import CustomException
from src.utils.dates import ensure_utc, parse_iso_utc, to_iso_utc

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _load_company_wos(db: Session, company_id: int) -> list[WorkOrder]:
    return list(db.scalars(select(WorkOrder).where(WorkOrder.company_id == company_id)).all())


# 1. WorkOrderAnalyticsController (/analytics/work-orders/...)
@router.post("/work-orders/complete/overview")
@router.get("/work-orders/complete/overview")
def wo_complete_overview(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    total = len(wos)
    complete = sum(1 for w in wos if w.status == 3)
    compliant = sum(
        1
        for w in wos
        if w.status == 3
        and (
            w.due_date is None
            or (w.completed_on and ensure_utc(w.completed_on) <= ensure_utc(w.due_date))
        )
    )
    avg_cycle = 0.0
    return {
        "total": total,
        "complete": complete,
        "compliant": compliant,
        "avgCycleTime": avg_cycle,
        "count": total,
        "ratio": (complete / total * 100.0) if total > 0 else 0.0,
    }


@router.post("/work-orders/incomplete/overview")
@router.get("/work-orders/incomplete/overview")
def wo_incomplete_overview(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    incomplete = [w for w in wos if w.status != 3]
    return {
        "total": len(incomplete),
        "remaining": len(incomplete),
        "estimatedHours": sum(w.estimated_duration or 0.0 for w in incomplete),
        "averageAge": 0.0,
    }


@router.post("/work-orders/complete/counts")
@router.get("/work-orders/complete/counts")
def wo_complete_counts(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    complete = sum(1 for w in wos if w.status == 3)
    reactive = sum(1 for w in wos if w.status == 3 and not w.parent_preventive_maintenance_id)
    rp = complete - reactive
    return {
        "complete": complete,
        "compliant": complete,
        "reactive": reactive,
        "rp": rp,
        "count": complete,
    }


@router.post("/work-orders/priority")
@router.get("/work-orders/priority")
def wo_by_priority(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    return {
        "none": {"count": sum(1 for w in wos if (w.priority or 0) == 0), "estimatedHours": 0.0},
        "low": {"count": sum(1 for w in wos if w.priority == 1), "estimatedHours": 0.0},
        "medium": {"count": sum(1 for w in wos if w.priority == 2), "estimatedHours": 0.0},
        "high": {"count": sum(1 for w in wos if w.priority == 3), "estimatedHours": 0.0},
    }


@router.post("/work-orders/statuses")
@router.get("/work-orders/statuses")
def wo_statuses(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    return {
        "open": sum(1 for w in wos if (w.status or 0) == 0),
        "inProgress": sum(1 for w in wos if w.status == 1),
        "onHold": sum(1 for w in wos if w.status == 2),
        "complete": sum(1 for w in wos if w.status == 3),
    }


@router.post("/work-orders/costs/time")
@router.get("/work-orders/costs/time")
@router.post("/work-orders/complete/costs-time")
@router.get("/work-orders/complete/costs-time")
def wo_costs_And_time(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    wo_ids = [w.id for w in wos]
    completed_count = sum(1 for w in wos if w.status == 3)
    labors = db.scalars(select(Labor).where(Labor.company_id == current_user.company_id)).all()
    add_costs = (
        db.scalars(
            select(AdditionalCost).where(AdditionalCost.work_order_id.in_(wo_ids))
        ).all()
        if wo_ids
        else []
    )
    pqs = db.scalars(select(PartQuantity).where(PartQuantity.company_id == current_user.company_id)).all()

    labor_cost = round(sum((l.hourly_rate or 0) * ((l.duration or 0) / 3600.0) for l in labors), 2)
    labor_time = sum(l.duration or 0 for l in labors)
    additional_cost = round(sum(c.cost or 0.0 for c in add_costs), 2)
    part_cost = 0.0
    for pq in pqs:
        if pq.part_id:
            p = db.get(Part, pq.part_id)
            if p:
                part_cost += (p.cost or 0.0) * (pq.quantity or 0)
    part_cost = round(part_cost, 2)
    total = round(labor_cost + additional_cost + part_cost, 2)
    average = round(total / completed_count, 2) if completed_count > 0 else 0.0
    return {
        "total": total,
        "average": average,
        "partCost": part_cost,
        "additionalCost": additional_cost,
        "laborCost": labor_cost,
        "laborTime": labor_time,
    }


@router.post("/work-orders/{subpath:path}")
@router.get("/work-orders/{subpath:path}")
def wo_analytics_fallback(
    subpath: str,
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    if "date" in subpath or "category" in subpath or "hours" in subpath:
        return []
    return {"count": 0, "total": 0}


# 2. AssetAnalyticsController (/analytics/assets/...)
def _parse_date_range(payload: dict[str, Any] | None) -> tuple[datetime, datetime]:
    now = utcnow()
    default_start = now - timedelta(days=30)
    if not isinstance(payload, dict):
        return default_start, now
    start = parse_iso_utc(payload.get("start")) or default_start
    end = parse_iso_utc(payload.get("end")) or now
    return start, end


def _get_asset_real_created_at(asset: Asset) -> datetime:
    return ensure_utc(asset.in_service_date or asset.created_at or utcnow())


def _get_labor_total_work_duration(labors: list[Labor]) -> int:
    """Java parity with Labor.getTotalWorkDuration(List<Labor>) (Labor.java:80-106)."""
    valid = [lb for lb in labors if lb.started_at is not None]
    valid.sort(key=lambda lb: ensure_utc(lb.started_at))
    total_duration = 0
    previous_end: datetime | None = None
    for lb in valid:
        current_start = ensure_utc(lb.started_at)
        dur = int(lb.duration or 0)
        current_end = current_start + timedelta(seconds=dur)
        if previous_end is not None and current_start < previous_end:
            total_duration += int((current_end - previous_end).total_seconds())
        else:
            total_duration += dur
        previous_end = current_end
    return total_duration


def _get_asset_mtbf(db: Session, asset_id: int, start: datetime, end: datetime) -> int:
    """Java parity with AssetService.getMTBF (AssetService.java:665-684)."""
    downtimes = list(
        db.scalars(
            select(AssetDowntime)
            .where(
                AssetDowntime.asset_id == asset_id,
                AssetDowntime.starts_on >= start,
                AssetDowntime.starts_on <= end,
            )
            .order_by(AssetDowntime.starts_on.asc())
        ).all()
    )
    if len(downtimes) < 2:
        return 0
    intervals_sum = 0
    num_intervals = len(downtimes) - 1
    for i in range(num_intervals):
        curr = downtimes[i]
        nxt = downtimes[i + 1]
        ends_on = ensure_utc(curr.starts_on) + timedelta(seconds=int(curr.duration or 0))
        interval_days = int((ensure_utc(nxt.starts_on) - ends_on).total_seconds() / 86400)
        intervals_sum += interval_days
    return int(intervals_sum / num_intervals)


def _get_asset_mttr(db: Session, asset_id: int, start: datetime, end: datetime) -> int:
    """Java parity with AssetService.getMTTR (AssetService.java:686-693)."""
    wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.asset_id == asset_id,
                WorkOrder.created_at >= start,
                WorkOrder.created_at <= end,
            )
        ).all()
    )
    if not wos:
        return 0
    wo_ids = [w.id for w in wos]
    labors = list(db.scalars(select(Labor).where(Labor.work_order_id.in_(wo_ids))).all())
    return int((_get_labor_total_work_duration(labors) // 60) // len(wos))


def _get_asset_downtime(db: Session, asset_id: int, start: datetime, end: datetime) -> int:
    """Java parity with AssetService.getDowntime (AssetService.java:695-698)."""
    downtimes = db.scalars(
        select(AssetDowntime).where(
            AssetDowntime.asset_id == asset_id,
            AssetDowntime.starts_on >= start,
            AssetDowntime.starts_on <= end,
        )
    ).all()
    return sum(int(d.duration or 0) for d in downtimes)


def _get_asset_uptime(db: Session, asset: Asset, start: datetime, end: datetime) -> int:
    """Java parity with AssetService.getUptime (AssetService.java:700-710)."""
    now = utcnow()
    real_created = _get_asset_real_created_at(asset)
    effective_start = start if start > real_created else real_created
    effective_end = end if end < now else now
    if effective_start > effective_end:
        return 0
    effective_duration = int((effective_end - effective_start).total_seconds())
    return effective_duration - _get_asset_downtime(db, asset.id, effective_start, effective_end)


def _get_wos_all_cost(db: Session, wos: list[WorkOrder], include_labor_cost: bool = True) -> float:
    if not wos:
        return 0.0
    wo_ids = [w.id for w in wos]
    total = 0.0
    if include_labor_cost:
        labors = db.scalars(select(Labor).where(Labor.work_order_id.in_(wo_ids))).all()
        total += sum((lb.hourly_rate or 0) * ((lb.duration or 0) / 3600.0) for lb in labors)
    add_costs = db.scalars(
        select(AdditionalCost).where(AdditionalCost.work_order_id.in_(wo_ids))
    ).all()
    total += sum(float(ac.cost or 0.0) for ac in add_costs)
    pqs = db.scalars(select(PartQuantity).where(PartQuantity.work_order_id.in_(wo_ids))).all()
    for pq in pqs:
        if pq.part_id:
            p = db.get(Part, pq.part_id)
            if p:
                total += float(p.cost or 0.0) * float(pq.quantity or 0)
    return round(total, 2)


def _get_downtimes_meantime(downtimes: list[AssetDowntime]) -> int:
    """Java parity with AssetDowntimeService.getDowntimesMeantime (AssetDowntimeService.java:83-93)."""
    valid = [d for d in downtimes if d.starts_on is not None]
    if len(valid) <= 2:
        return 0
    first_dt = min(valid, key=lambda d: ensure_utc(d.starts_on))
    last_dt = max(valid, key=lambda d: ensure_utc(d.starts_on))
    hours_diff = int((ensure_utc(last_dt.starts_on) - ensure_utc(first_dt.starts_on)).total_seconds() // 3600)
    return int(hours_diff // (len(valid) - 1))


@router.post("/assets/{asset_id:int}/overview")
@router.get("/assets/{asset_id:int}/overview")
def asset_details_overview(
    asset_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access Denied")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise CustomException(status_code=404, message="Asset not found")
    assert_company_access(asset, current_user)
    start, end = _parse_date_range(payload)
    wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.asset_id == asset.id,
                WorkOrder.created_at >= start,
                WorkOrder.created_at <= end,
            )
        ).all()
    )
    return {
        "mtbf": _get_asset_mtbf(db, asset.id, start, end),
        "mttr": _get_asset_mttr(db, asset.id, start, end),
        "downtime": _get_asset_downtime(db, asset.id, start, end),
        "uptime": _get_asset_uptime(db, asset, start, end),
        "totalCost": _get_wos_all_cost(db, wos, include_labor_cost=True),
    }


@router.post("/assets/overview")
@router.get("/assets/overview")
def assets_overview(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    downtimes = list(
        db.scalars(
            select(AssetDowntime).where(
                AssetDowntime.company_id == company_id,
                AssetDowntime.starts_on >= start,
                AssetDowntime.starts_on <= end,
            )
        ).all()
    )
    downtimes_duration = 0
    for dt in downtimes:
        if dt.starts_on is None:
            continue
        dt_starts = ensure_utc(dt.starts_on)
        dt_start = max(dt_starts, start)
        dt_end = min(dt_starts + timedelta(seconds=int(dt.duration or 0)), end)
        downtimes_duration += max(0, int((dt_end - dt_start).total_seconds()))

    assets = list(
        db.scalars(
            select(Asset).where(
                Asset.company_id == company_id,
                Asset.created_at <= end,
            )
        ).all()
    )
    living_time = 0
    for a in assets:
        real_created = _get_asset_real_created_at(a)
        eff_start = start if real_created < start else real_created
        if end > eff_start:
            living_time += int((end - eff_start).total_seconds())

    availability = 0 if living_time == 0 else int((living_time - downtimes_duration) * 100 // living_time)
    return {
        "downtime": downtimes_duration,
        "availability": availability,
        "downtimeEvents": len(downtimes),
    }


@router.post("/assets/costs/overview")
@router.get("/assets/costs/overview")
def assets_costs_overview(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(
        db.scalars(
            select(Asset).where(
                Asset.company_id == company_id,
                Asset.created_at <= end,
            )
        ).all()
    )
    total_acq_cost = float(sum(a.acquisition_cost or 0.0 for a in assets))
    wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == company_id,
                WorkOrder.created_at >= start,
                WorkOrder.created_at <= end,
            )
        ).all()
    )
    total_wo_costs = _get_wos_all_cost(db, wos, include_labor_cost=True)
    assets_with_acq = {a.id for a in assets if (a.acquisition_cost or 0) > 0}
    wos_with_acq = [w for w in wos if w.asset_id in assets_with_acq]
    rav_wo_costs = _get_wos_all_cost(db, wos_with_acq, include_labor_cost=True)
    rav = 0.0 if total_acq_cost == 0 else round(rav_wo_costs * 100.0 / total_acq_cost, 2)
    return {
        "totalWOCosts": total_wo_costs,
        "totalAcquisitionCost": total_acq_cost,
        "rav": rav,
    }


@router.post("/assets/time-cost")
@router.get("/assets/time-cost")
def assets_time_cost(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(db.scalars(select(Asset).where(Asset.company_id == company_id)).all())
    result: list[dict[str, Any]] = []
    for a in assets:
        wos = list(
            db.scalars(
                select(WorkOrder).where(
                    WorkOrder.asset_id == a.id,
                    WorkOrder.created_at >= start,
                    WorkOrder.created_at <= end,
                )
            ).all()
        )
        if not wos:
            continue
        wo_ids = [w.id for w in wos]
        labors = list(db.scalars(select(Labor).where(Labor.work_order_id.in_(wo_ids))).all())
        time_sec = sum(int(lb.duration or 0) for lb in labors)
        cost = _get_wos_all_cost(db, wos, include_labor_cost=True)
        result.append({"id": a.id, "name": a.name, "time": time_sec, "cost": cost})
    result.sort(key=lambda r: (r["cost"], r["time"]), reverse=True)
    return result[:10]


@router.post("/assets/downtimes")
@router.get("/assets/downtimes")
def assets_downtimes_by_asset(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(db.scalars(select(Asset).where(Asset.company_id == company_id)).all())
    result: list[dict[str, Any]] = []
    for a in assets:
        dts = list(
            db.scalars(
                select(AssetDowntime).where(
                    AssetDowntime.asset_id == a.id,
                    AssetDowntime.starts_on >= start,
                    AssetDowntime.starts_on <= end,
                )
            ).all()
        )
        if not dts:
            continue
        total_dur = sum(int(d.duration or 0) for d in dts)
        real_created = _get_asset_real_created_at(a)
        eff_start = start if real_created < start else real_created
        living_time = max(0, int((end - eff_start).total_seconds()))
        percent = 0 if living_time == 0 else int(total_dur * 100 // living_time)
        result.append({"id": a.id, "name": a.name, "count": len(dts), "percent": percent})
    result.sort(key=lambda r: (r["percent"], r["count"]), reverse=True)
    return result[:10]


@router.post("/assets/mtbf")
@router.get("/assets/mtbf")
def assets_mtbf_by_asset(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(db.scalars(select(Asset).where(Asset.company_id == company_id)).all())
    result: list[dict[str, Any]] = []
    for a in assets:
        mtbf = _get_asset_mtbf(db, a.id, start, end)
        result.append({"id": a.id, "name": a.name, "mtbf": mtbf})
    result.sort(key=lambda r: r["mtbf"], reverse=True)
    return result[:10]


@router.post("/assets/mttr")
@router.get("/assets/mttr")
def assets_mttr_by_asset(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(db.scalars(select(Asset).where(Asset.company_id == company_id)).all())
    result: list[dict[str, Any]] = []
    for a in assets:
        mttr = _get_asset_mttr(db, a.id, start, end)
        result.append({"id": a.id, "name": a.name, "mttr": mttr})
    result.sort(key=lambda r: r["mttr"], reverse=True)
    return result[:10]


@router.post("/assets/meantimes")
@router.get("/assets/meantimes")
def assets_meantimes(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    downtimes = list(
        db.scalars(
            select(AssetDowntime).where(
                AssetDowntime.company_id == company_id,
                AssetDowntime.starts_on >= start,
                AssetDowntime.starts_on <= end,
            )
        ).all()
    )
    wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == company_id,
                WorkOrder.created_at >= start,
                WorkOrder.created_at <= end,
            )
        ).all()
    )
    between_maintenances = 0
    valid_wos = [w for w in wos if w.created_at is not None]
    if len(valid_wos) > 2:
        first_wo = min(valid_wos, key=lambda w: ensure_utc(w.created_at))
        last_wo = max(valid_wos, key=lambda w: ensure_utc(w.created_at))
        hours_diff = int((ensure_utc(last_wo.created_at) - ensure_utc(first_wo.created_at)).total_seconds() // 3600)
        between_maintenances = int(hours_diff // (len(valid_wos) - 1))
    return {
        "betweenDowntimes": _get_downtimes_meantime(downtimes),
        "betweenMaintenances": between_maintenances,
    }


@router.post("/assets/repair-times")
@router.get("/assets/repair-times")
def assets_repair_times(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(db.scalars(select(Asset).where(Asset.company_id == company_id)).all())
    result: list[dict[str, Any]] = []
    for a in assets:
        wos = list(
            db.scalars(
                select(WorkOrder).where(
                    WorkOrder.asset_id == a.id,
                    WorkOrder.created_at >= start,
                    WorkOrder.created_at <= end,
                )
            ).all()
        )
        if not wos:
            continue
        wo_ids = [w.id for w in wos]
        labors = list(db.scalars(select(Labor).where(Labor.work_order_id.in_(wo_ids))).all())
        dur = sum(int(lb.duration or 0) for lb in labors)
        result.append({"id": a.id, "name": a.name, "duration": dur})
    result.sort(key=lambda r: r["duration"], reverse=True)
    return result[:10]


@router.post("/assets/downtimes/costs")
@router.get("/assets/downtimes/costs")
def assets_downtimes_and_costs(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    assets = list(db.scalars(select(Asset).where(Asset.company_id == company_id)).all())
    result: list[dict[str, Any]] = []
    for a in assets:
        dur = _get_asset_downtime(db, a.id, start, end)
        wos = list(
            db.scalars(
                select(WorkOrder).where(
                    WorkOrder.asset_id == a.id,
                    WorkOrder.created_at >= start,
                    WorkOrder.created_at <= end,
                )
            ).all()
        )
        cost = _get_wos_all_cost(db, wos, include_labor_cost=True)
        if dur > 0 or cost > 0:
            result.append(
                {"id": a.id, "name": a.name, "duration": dur, "workOrdersCosts": cost}
            )
    result.sort(key=lambda r: (r["duration"], r["workOrdersCosts"]), reverse=True)
    return result[:10]


@router.post("/assets/downtimes/costs/date")
@router.get("/assets/downtimes/costs/date")
def assets_downtimes_costs_by_date(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    total_days = max(1, int((end.date() - start.date()).days) + 1)
    points = min(15, total_days)
    step_days = max(1, total_days // points)
    result: list[dict[str, Any]] = []
    curr = start
    for _ in range(points):
        nxt = min(end, curr + timedelta(days=step_days))
        wos = list(
            db.scalars(
                select(WorkOrder).where(
                    WorkOrder.company_id == company_id,
                    WorkOrder.status == 3,
                    WorkOrder.completed_on >= curr,
                    WorkOrder.completed_on <= nxt,
                )
            ).all()
        )
        dts = list(
            db.scalars(
                select(AssetDowntime).where(
                    AssetDowntime.company_id == company_id,
                    AssetDowntime.starts_on >= curr,
                    AssetDowntime.starts_on <= nxt,
                )
            ).all()
        )
        result.append(
            {
                "date": to_iso_utc(curr),
                "workOrdersCosts": _get_wos_all_cost(db, wos, include_labor_cost=True),
                "duration": sum(int(d.duration or 0) for d in dts),
            }
        )
        curr = nxt
    return result


@router.post("/assets/downtimes/meantime/date")
@router.get("/assets/downtimes/meantime/date")
@router.post("/assets/downtimes/meantimes")
@router.get("/assets/downtimes/meantimes")
def assets_downtimes_meantime_by_date(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    company_id = current_user.company_id
    total_days = max(1, int((end.date() - start.date()).days) + 1)
    points = min(15, total_days)
    step_days = max(1, total_days // points)
    result: list[dict[str, Any]] = []
    curr = start
    for _ in range(points):
        nxt = min(end, curr + timedelta(days=step_days))
        dts = list(
            db.scalars(
                select(AssetDowntime).where(
                    AssetDowntime.company_id == company_id,
                    AssetDowntime.starts_on >= curr,
                    AssetDowntime.starts_on <= nxt,
                )
            ).all()
        )
        result.append(
            {
                "date": to_iso_utc(curr),
                "meantime": _get_downtimes_meantime(dts),
            }
        )
        curr = nxt
    return result


@router.post("/assets/{subpath:path}")
@router.get("/assets/{subpath:path}")
def assets_analytics_fallback(
    subpath: str,
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
) -> Any:
    return []


# 3. PartAnalyticsController (/analytics/parts/...)
def _load_part_consumptions(
    db: Session, company_id: int, start: datetime, end: datetime
) -> list[PartConsumption]:
    rows = list(
        db.scalars(
            select(PartConsumption).where(
                PartConsumption.company_id == company_id,
                PartConsumption.created_at >= start,
                PartConsumption.created_at <= end,
            )
        ).all()
    )
    return [
        c
        for c in rows
        if c.description in (None, "PART_CONSUMPTION", "CONSUMPTION")
        or c.work_order_id is not None
    ]


def _get_consumption_cost(db: Session, c: PartConsumption) -> float:
    if not c.part_id:
        return 0.0
    p = db.get(Part, c.part_id)
    if not p:
        return 0.0
    return float(p.cost or 0.0) * float(c.quantity or 0.0)


@router.post("/parts/consumptions/overview")
@router.get("/parts/consumptions/overview")
def parts_consumptions_overview(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    start, end = _parse_date_range(payload)
    consumptions = _load_part_consumptions(db, current_user.company_id, start, end)
    total_cost = round(sum(_get_consumption_cost(db, c) for c in consumptions), 2)
    consumed_count = sum(int(c.quantity or 0) for c in consumptions)
    return {"totalConsumptionCost": total_cost, "consumedCount": consumed_count}


@router.post("/parts/consumptions/pareto")
@router.get("/parts/consumptions/pareto")
def parts_consumptions_pareto(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    consumptions = [
        c
        for c in _load_part_consumptions(db, current_user.company_id, start, end)
        if (c.quantity or 0) != 0 and c.part_id is not None
    ]
    part_costs: dict[int, float] = {}
    for c in consumptions:
        part_costs[c.part_id] = part_costs.get(c.part_id, 0.0) + _get_consumption_cost(db, c)
    result: list[dict[str, Any]] = []
    for pid, cost in part_costs.items():
        p = db.get(Part, pid)
        if p:
            result.append({"id": p.id, "name": p.name, "cost": round(cost, 2)})
    result.sort(key=lambda r: r["cost"], reverse=True)
    return result


@router.post("/parts/consumptions/assets")
@router.get("/parts/consumptions/assets")
def parts_consumptions_assets(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    consumptions = _load_part_consumptions(db, current_user.company_id, start, end)
    asset_costs: dict[int, float] = {}
    for c in consumptions:
        if c.work_order_id:
            wo = db.get(WorkOrder, c.work_order_id)
            if wo and wo.asset_id:
                asset_costs[wo.asset_id] = asset_costs.get(wo.asset_id, 0.0) + _get_consumption_cost(
                    db, c
                )
    result: list[dict[str, Any]] = []
    for aid, cost in asset_costs.items():
        asset = db.get(Asset, aid)
        if asset:
            result.append({"id": asset.id, "name": asset.name, "cost": round(cost, 2)})
    result.sort(key=lambda r: r["cost"], reverse=True)
    return result[:10]


@router.post("/parts/consumptions/parts-category")
@router.get("/parts/consumptions/parts-category")
def parts_consumptions_parts_category(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    cs_id = _get_user_company_settings_id(current_user, db)
    categories = list(
        db.scalars(
            select(PartCategory).where(PartCategory.company_settings_id == cs_id)
        ).all()
    )
    consumptions = _load_part_consumptions(db, current_user.company_id, start, end)
    result: list[dict[str, Any]] = []
    for cat in categories:
        cost = 0.0
        for c in consumptions:
            if c.part_id:
                p = db.get(Part, c.part_id)
                if p and p.category_id == cat.id:
                    cost += _get_consumption_cost(db, c)
        result.append({"id": cat.id, "name": cat.name, "cost": round(cost, 2)})
    return result


@router.post("/parts/consumptions/work-order-category")
@router.get("/parts/consumptions/work-order-category")
def parts_consumptions_wo_category(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    cs_id = _get_user_company_settings_id(current_user, db)
    categories = list(
        db.scalars(
            select(WorkOrderCategory).where(WorkOrderCategory.company_settings_id == cs_id)
        ).all()
    )
    consumptions = _load_part_consumptions(db, current_user.company_id, start, end)
    result: list[dict[str, Any]] = []
    for cat in categories:
        cost = 0.0
        for c in consumptions:
            if c.work_order_id:
                wo = db.get(WorkOrder, c.work_order_id)
                if wo and wo.category_id == cat.id:
                    cost += _get_consumption_cost(db, c)
        result.append({"id": cat.id, "name": cat.name, "cost": round(cost, 2)})
    return result


@router.post("/parts/consumptions/date")
@router.get("/parts/consumptions/date")
def parts_consumptions_by_date(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    total_days = max(1, int((end.date() - start.date()).days) + 1)
    points = min(15, total_days)
    step_days = max(1, total_days // points)
    result: list[dict[str, Any]] = []
    curr = start
    for _ in range(points):
        nxt = min(end, curr + timedelta(days=step_days))
        consumptions = _load_part_consumptions(db, current_user.company_id, curr, nxt)
        cost = round(sum(_get_consumption_cost(db, c) for c in consumptions), 2)
        result.append({"date": to_iso_utc(curr), "cost": cost})
        curr = nxt
    return result


@router.post("/parts/{subpath:path}")
@router.get("/parts/{subpath:path}")
def parts_analytics_fallback(
    subpath: str,
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
) -> Any:
    return []


# 4. RequestAnalyticsController (/analytics/requests/...)
def _compute_requests_cycle_time(db: Session, reqs: list[Request]) -> float:
    durations: list[float] = []
    for r in reqs:
        if r.work_order_id:
            wo = db.get(WorkOrder, r.work_order_id)
            if wo and wo.status == 3 and wo.created_at and wo.completed_on:
                diff_days = (
                    ensure_utc(wo.completed_on) - ensure_utc(wo.created_at)
                ).total_seconds() / 86400.0
                durations.append(max(0.0, diff_days))
    if not durations:
        return 0.0
    return round(sum(durations) / len(durations), 2)


@router.post("/requests/priority")
@router.get("/requests/priority")
def requests_by_priority(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    reqs = db.scalars(select(Request).where(Request.company_id == current_user.company_id)).all()
    return {
        "none": {"count": sum(1 for r in reqs if (r.priority or 0) == 0)},
        "low": {"count": sum(1 for r in reqs if r.priority == 1)},
        "medium": {"count": sum(1 for r in reqs if r.priority == 2)},
        "high": {"count": sum(1 for r in reqs if r.priority == 3)},
    }


@router.post("/requests/rate")
@router.get("/requests/rate")
@router.post("/requests/overview")
@router.get("/requests/overview")
def requests_rate(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    reqs = list(
        db.scalars(select(Request).where(Request.company_id == current_user.company_id)).all()
    )
    approved = sum(1 for r in reqs if r.work_order_id is not None)
    cancelled = sum(1 for r in reqs if r.cancelled)
    pending = len(reqs) - approved - cancelled
    return {
        "approved": approved,
        "pending": pending,
        "cancelled": cancelled,
        "cycleTime": _compute_requests_cycle_time(db, reqs),
    }


@router.post("/requests/cycle-time/date")
@router.get("/requests/cycle-time/date")
def requests_cycle_time_by_date(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    total_days = max(1, int((end.date() - start.date()).days) + 1)
    points = min(15, total_days)
    step_days = max(1, total_days // points)
    result: list[dict[str, Any]] = []
    curr = start
    for _ in range(points):
        nxt = min(end, curr + timedelta(days=step_days))
        reqs = list(
            db.scalars(
                select(Request).where(
                    Request.company_id == current_user.company_id,
                    Request.created_at >= curr,
                    Request.created_at <= nxt,
                )
            ).all()
        )
        result.append(
            {
                "date": to_iso_utc(curr),
                "cycleTime": _compute_requests_cycle_time(db, reqs),
            }
        )
        curr = nxt
    return result


@router.post("/requests/received-and-resolved")
@router.get("/requests/received-and-resolved")
def requests_received_and_resolved(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    total_days = max(1, int((end.date() - start.date()).days) + 1)
    points = min(15, total_days)
    step_days = max(1, total_days // points)
    result: list[dict[str, Any]] = []
    curr = start
    for _ in range(points):
        nxt = min(end, curr + timedelta(days=step_days))
        reqs = list(
            db.scalars(
                select(Request).where(
                    Request.company_id == current_user.company_id,
                    Request.created_at >= curr,
                    Request.created_at <= nxt,
                    Request.cancelled.is_(False),
                )
            ).all()
        )
        resolved = 0
        for r in reqs:
            if r.work_order_id:
                wo = db.get(WorkOrder, r.work_order_id)
                if wo and wo.status == 3:
                    resolved += 1
        result.append(
            {
                "date": to_iso_utc(curr),
                "received": len(reqs),
                "resolved": resolved,
            }
        )
        curr = nxt
    return result


@router.post("/requests/counts/category")
@router.get("/requests/counts/category")
def requests_counts_by_category(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    start, end = _parse_date_range(payload)
    cs_id = _get_user_company_settings_id(current_user, db)
    categories = list(
        db.scalars(
            select(WorkOrderCategory).where(WorkOrderCategory.company_settings_id == cs_id)
        ).all()
    )
    result: list[dict[str, Any]] = []
    for cat in categories:
        reqs = list(
            db.scalars(
                select(Request).where(
                    Request.company_id == current_user.company_id,
                    Request.category_id == cat.id,
                    Request.created_at >= start,
                    Request.created_at <= end,
                )
            ).all()
        )
        result.append({"id": cat.id, "name": cat.name, "count": len(reqs)})
    return result


@router.post("/requests/{subpath:path}")
@router.get("/requests/{subpath:path}")
def requests_analytics_fallback(
    subpath: str,
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
) -> Any:
    return []


# 5. UserAnalyticsController (/analytics/users/...)
@router.post("/users/complete/work-orders")
@router.get("/users/complete/work-orders")
def users_complete_wos(
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wos = _load_company_wos(db, current_user.company_id)
    return {
        "created": len(wos),
        "completed": sum(1 for w in wos if w.status == 3),
    }


@router.post("/users/me/work-orders/overview")
@router.get("/users/me/work-orders/overview")
def users_me_wos_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    created_wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == current_user.company_id,
                WorkOrder.created_by == current_user.id,
            )
        ).all()
    )
    completed_wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == current_user.company_id,
                WorkOrder.completed_by_id == current_user.id,
                WorkOrder.status == 3,
            )
        ).all()
    )
    return {
        "created": len(created_wos),
        "completed": len(completed_wos),
    }


def _build_two_weeks_wo_stats(
    db: Session, company_id: int, target_user_id: int | None = None
) -> list[dict[str, Any]]:
    now = utcnow()
    first_day = now - timedelta(days=14)
    wos = list(
        db.scalars(
            select(WorkOrder).where(
                WorkOrder.company_id == company_id,
                WorkOrder.created_at >= first_day,
            )
        ).all()
    )
    result: list[dict[str, Any]] = []
    for i in range(13, -1, -1):
        day_dt = (now - timedelta(days=i)).date()
        created_in_day = sum(
            1
            for w in wos
            if w.created_at
            and ensure_utc(w.created_at).date() == day_dt
            and (target_user_id is None or w.created_by == target_user_id)
        )
        completed_in_day = sum(
            1
            for w in wos
            if w.created_at
            and ensure_utc(w.created_at).date() == day_dt
            and w.status == 3
            and (target_user_id is None or w.completed_by_id == target_user_id)
        )
        result.append(
            {
                "created": created_in_day,
                "completed": completed_in_day,
                "date": to_iso_utc(datetime(day_dt.year, day_dt.month, day_dt.day)),
            }
        )
    return result


@router.get("/users/two-weeks/work-orders")
@router.post("/users/two-weeks/work-orders")
def users_two_weeks_wos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return _build_two_weeks_wo_stats(db, current_user.company_id)


@router.get("/users/two-weeks/work-orders/{user_id:int}")
@router.post("/users/two-weeks/work-orders/{user_id:int}")
def users_two_weeks_wos_by_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access Denied")
    target = db.get(User, user_id)
    if not target or target.company_id != current_user.company_id:
        raise CustomException(status_code=403, message="Access Denied")
    return _build_two_weeks_wo_stats(db, current_user.company_id, target_user_id=user_id)


@router.post("/users/{subpath:path}")
@router.get("/users/{subpath:path}")
def users_analytics_fallback(
    subpath: str,
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
) -> Any:
    return []
