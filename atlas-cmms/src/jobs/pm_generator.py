"""Preventive maintenance work-order generation job."""

from __future__ import annotations

import calendar
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import PreventiveMaintenance, Schedule, Task, WorkOrder
from src.models.associations import (
    preventive_maintenance_assigned_to,
    preventive_maintenance_customers,
    preventive_maintenance_files,
    schedule_days_of_week,
    work_order_assigned_to,
    work_order_customers,
    work_order_files,
)
from src.models.enums import WFMainCondition
from src.models.files_custom import CustomField, CustomFieldValue
from src.models.tasks import TaskBase, TaskOption
from src.services.workflow_engine import run_work_order_workflows
from src.utils.dates import ensure_utc

logger = logging.getLogger(__name__)

_DAY_NAME_TO_INT: dict[str, int] = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def normalize_day_of_week(val: Any) -> int | None:
    if isinstance(val, int):
        if 0 <= val <= 6:
            return val
        if 1 <= val <= 7:
            return val - 1
    if isinstance(val, str):
        s = val.strip().upper()
        if s in _DAY_NAME_TO_INT:
            return _DAY_NAME_TO_INT[s]
        if s.isdigit():
            return normalize_day_of_week(int(s))
    return None


def get_schedule_days_of_week(schedule_id: int, db: Session) -> list[int]:
    rows = db.scalars(
        select(schedule_days_of_week.c.days_of_week).where(
            schedule_days_of_week.c.schedule_id == schedule_id
        )
    ).all()
    normalized = sorted({d for r in rows if (d := normalize_day_of_week(r)) is not None})
    return normalized


def advance_schedule_next_due_date(
    schedule: Schedule, base_dt: datetime, db: Session | None = None
) -> datetime:
    """Compute the next due date from base_dt according to recurrence_type and frequency."""
    freq = max(1, int(schedule.frequency or 1))
    rec_type = (schedule.recurrence_type or "DAILY").strip().upper()

    if rec_type == "DAILY":
        return base_dt + timedelta(days=freq)

    if rec_type == "WEEKLY":
        days: list[int] = []
        if db is not None and schedule.id is not None:
            days = get_schedule_days_of_week(schedule.id, db)
        if days:
            cur_wd = base_dt.weekday()
            later_in_week = [d for d in days if d > cur_wd]
            if later_in_week:
                return base_dt + timedelta(days=later_in_week[0] - cur_wd)
            first_day = days[0]
            days_until_next = (7 * freq) - cur_wd + first_day
            return base_dt + timedelta(days=days_until_next)
        return base_dt + timedelta(weeks=freq)

    if rec_type == "MONTHLY":
        total_months = (base_dt.year * 12 + (base_dt.month - 1)) + freq
        new_year = total_months // 12
        new_month = (total_months % 12) + 1
        max_day = calendar.monthrange(new_year, new_month)[1]
        new_day = min(base_dt.day, max_day)
        return base_dt.replace(year=new_year, month=new_month, day=new_day)

    if rec_type == "YEARLY":
        new_year = base_dt.year + freq
        max_day = calendar.monthrange(new_year, base_dt.month)[1]
        new_day = min(base_dt.day, max_day)
        return base_dt.replace(year=new_year, day=new_day)

    return base_dt + timedelta(days=freq)


def create_work_order_from_pm(
    pm: PreventiveMaintenance,
    schedule: Schedule | None,
    db: Session,
    created_by_id: int | None = None,
    now: datetime | None = None,
) -> WorkOrder:
    """Create a WorkOrder from a PreventiveMaintenance and clone all tasks, M2M relations, and custom fields."""
    if now is None:
        now = datetime.now(timezone.utc)
    now_utc = ensure_utc(now)

    due_date = None
    if schedule is not None and schedule.due_date_delay:
        due_date = now_utc + timedelta(days=int(schedule.due_date_delay))
    elif pm.due_date:
        due_date = pm.due_date

    actor_id = created_by_id if created_by_id is not None else pm.created_by

    wo = WorkOrder(
        title=pm.title or pm.name or "PM Work Order",
        description=pm.description,
        priority=pm.priority if pm.priority is not None else 0,
        estimated_duration=pm.estimated_duration or 0.0,
        estimated_start_date=pm.estimated_start_date,
        required_signature=bool(pm.required_signature),
        company_id=pm.company_id,
        asset_id=pm.asset_id,
        category_id=pm.category_id,
        image_id=pm.image_id,
        location_id=pm.location_id,
        primary_user_id=pm.primary_user_id,
        team_id=pm.team_id,
        parent_preventive_maintenance_id=pm.id,
        status=0,
        archived=False,
        is_demo=bool(pm.is_demo),
        due_date=due_date,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(wo)
    db.flush()
    wo.custom_id = f"WO{wo.id:06d}"

    # Clone assignedTo
    assigned_ids = db.scalars(
        select(preventive_maintenance_assigned_to.c.assigned_to_id).where(
            preventive_maintenance_assigned_to.c.preventive_maintenance_id == pm.id
        )
    ).all()
    for uid in assigned_ids:
        db.execute(
            work_order_assigned_to.insert().values(
                work_order_id=wo.id,
                assigned_to_id=uid,
            )
        )

    # Clone customers
    customer_ids = db.scalars(
        select(preventive_maintenance_customers.c.customers_id).where(
            preventive_maintenance_customers.c.preventive_maintenance_id == pm.id
        )
    ).all()
    for cid in customer_ids:
        db.execute(
            work_order_customers.insert().values(
                work_order_id=wo.id,
                customers_id=cid,
            )
        )

    # Clone files
    file_ids = db.scalars(
        select(preventive_maintenance_files.c.files_id).where(
            preventive_maintenance_files.c.preventive_maintenance_id == pm.id
        )
    ).all()
    for fid in file_ids:
        db.execute(
            work_order_files.insert().values(
                work_order_id=wo.id,
                files_id=fid,
            )
        )

    # Clone CustomFieldValues (only when CustomField.copy_on_repeat is True)
    pm_cfvs = db.scalars(
        select(CustomFieldValue)
        .join(CustomField, CustomField.id == CustomFieldValue.custom_field_id)
        .where(
            CustomFieldValue.preventive_maintenance_id == pm.id,
            CustomField.copy_on_repeat.is_(True),
        )
    ).all()
    for cfv in pm_cfvs:
        db.add(
            CustomFieldValue(
                custom_field_id=cfv.custom_field_id,
                value=cfv.value,
                work_order_id=wo.id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )

    # Clone Tasks (with dedicated TaskBase and TaskOption copies so WO edits don't mutate PM template)
    pm_tasks = db.scalars(
        select(Task).where(Task.preventive_maintenance_id == pm.id)
    ).all()
    for t in pm_tasks:
        orig_tb = db.get(TaskBase, t.task_base_id) if t.task_base_id else None
        if orig_tb is not None:
            cloned_tb = TaskBase(
                label=orig_tb.label,
                task_type=orig_tb.task_type,
                company_id=pm.company_id,
                asset_id=orig_tb.asset_id,
                user_id=orig_tb.user_id,
                meter_id=orig_tb.meter_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
            db.add(cloned_tb)
            db.flush()
            orig_opts = db.scalars(
                select(TaskOption).where(TaskOption.task_base_id == orig_tb.id)
            ).all()
            for opt in orig_opts:
                db.add(
                    TaskOption(
                        label=opt.label,
                        task_base_id=cloned_tb.id,
                        company_id=pm.company_id,
                        created_by=actor_id,
                        updated_by=actor_id,
                    )
                )
            db.flush()
            tb_id = cloned_tb.id
        else:
            tb_id = t.task_base_id

        db.add(
            Task(
                company_id=pm.company_id,
                task_base_id=tb_id,
                work_order_id=wo.id,
                notes=t.notes,
                value=t.value,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )

    db.flush()
    run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_CREATED, db)
    return wo


def generate_due_work_orders(db: Session, now: datetime | None = None) -> list[WorkOrder]:
    """Find active Schedule rows with disabled == False and next_due_date <= now,
    creates WorkOrder from PreventiveMaintenance, clones Checklist/TaskBase tasks,
    and advances next_due_date according to recurrence_type and recurrence_based_on.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    now_utc = ensure_utc(now)

    stmt = select(Schedule).where(Schedule.disabled == False, Schedule.next_due_date <= now_utc)  # noqa: E712
    due_schedules = list(db.scalars(stmt).all())
    created_work_orders: list[WorkOrder] = []

    for schedule in due_schedules:
        if schedule.ends_on and now_utc > ensure_utc(schedule.ends_on):
            schedule.disabled = True
            continue

        # Locate corresponding PreventiveMaintenance
        pm: PreventiveMaintenance | None = None
        if schedule.preventive_maintenance_id:
            pm = db.get(PreventiveMaintenance, schedule.preventive_maintenance_id)
        if pm is None:
            pm = db.scalars(
                select(PreventiveMaintenance).where(PreventiveMaintenance.schedule_id == schedule.id)
            ).first()

        if pm is None:
            logger.warning("Schedule %s has no associated PreventiveMaintenance; skipping", schedule.id)
            continue

        based_on = (schedule.recurrence_based_on or "SCHEDULED_DATE").strip().upper()
        if based_on == "COMPLETED_DATE":
            open_pm_wo = db.scalar(
                select(WorkOrder.id).where(
                    WorkOrder.parent_preventive_maintenance_id == pm.id,
                    WorkOrder.status != 3,
                )
            )
            if open_pm_wo is not None:
                continue

        wo = create_work_order_from_pm(pm, schedule, db, now=now_utc)

        if based_on != "COMPLETED_DATE":
            base_due = ensure_utc(schedule.next_due_date) if schedule.next_due_date else now_utc
            next_due = advance_schedule_next_due_date(schedule, base_due, db)
            while ensure_utc(next_due) <= now_utc:
                next_due = advance_schedule_next_due_date(schedule, next_due, db)
            schedule.next_due_date = next_due

            if schedule.ends_on and ensure_utc(schedule.next_due_date) > ensure_utc(schedule.ends_on):
                schedule.disabled = True

        created_work_orders.append(wo)
        logger.info(
            "Generated WorkOrder %s for PreventiveMaintenance %s (Schedule %s)",
            wo.custom_id,
            pm.id,
            schedule.id,
        )

    db.commit()
    return created_work_orders
