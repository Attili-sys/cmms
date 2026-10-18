"""Preventive maintenance work-order generation job."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import PreventiveMaintenance, Schedule, Task, WorkOrder

logger = logging.getLogger(__name__)


def generate_due_work_orders(db: Session, now: datetime | None = None) -> list[WorkOrder]:
    """Find active Schedule rows with disabled == False and next_due_date <= now,
    creates WorkOrder from PreventiveMaintenance, clones Checklist/TaskBase tasks,
    and advances next_due_date by frequency days.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    stmt = select(Schedule).where(Schedule.disabled == False, Schedule.next_due_date <= now)  # noqa: E712
    due_schedules = list(db.scalars(stmt).all())
    created_work_orders: list[WorkOrder] = []

    for schedule in due_schedules:
        if schedule.ends_on and now > schedule.ends_on:
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

        # Compute due_date for generated WorkOrder
        due_date = None
        if schedule.due_date_delay:
            due_date = now + timedelta(days=schedule.due_date_delay)
        elif pm.due_date:
            due_date = pm.due_date

        custom_id = f"WO-PM{pm.id}-{int(now.timestamp())}"
        if pm.custom_id:
            custom_id = f"{pm.custom_id}-{int(now.timestamp())}"

        wo = WorkOrder(
            title=pm.title,
            description=pm.description,
            priority=pm.priority,
            estimated_duration=pm.estimated_duration,
            required_signature=pm.required_signature,
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
            is_demo=pm.is_demo,
            due_date=due_date,
            custom_id=custom_id,
        )
        db.add(wo)
        db.flush()  # assign wo.id

        # Clone tasks linked to the PM
        pm_tasks = db.scalars(
            select(Task).where(Task.preventive_maintenance_id == pm.id)
        ).all()
        for t in pm_tasks:
            cloned = Task(
                company_id=pm.company_id,
                task_base_id=t.task_base_id,
                work_order_id=wo.id,
                notes=t.notes,
                value=t.value,
            )
            db.add(cloned)

        # Advance next_due_date by frequency days
        freq_days = schedule.frequency if schedule.frequency > 0 else 1
        schedule.next_due_date = schedule.next_due_date + timedelta(days=freq_days)

        if schedule.ends_on and schedule.next_due_date > schedule.ends_on:
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
