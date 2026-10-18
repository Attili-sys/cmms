"""Preventive maintenance upcoming notification job."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import PreventiveMaintenance, Schedule, User

logger = logging.getLogger(__name__)


def notify_upcoming_preventive_maintenance(
    db: Session,
    now: datetime | None = None,
    horizon_days: int = 1,
) -> list[dict]:
    """Find active PM schedules due within horizon_days and notify company users."""
    if now is None:
        now = datetime.now(timezone.utc)

    until = now + timedelta(days=horizon_days)

    stmt = select(Schedule).where(
        Schedule.disabled == False,  # noqa: E712
        Schedule.next_due_date > now,
        Schedule.next_due_date <= until,
    )
    upcoming_schedules = list(db.scalars(stmt).all())
    notifications: list[dict] = []

    for schedule in upcoming_schedules:
        pm: PreventiveMaintenance | None = None
        if schedule.preventive_maintenance_id:
            pm = db.get(PreventiveMaintenance, schedule.preventive_maintenance_id)
        if pm is None:
            pm = db.scalars(
                select(PreventiveMaintenance).where(PreventiveMaintenance.schedule_id == schedule.id)
            ).first()

        if pm is None:
            continue

        users = list(
            db.scalars(
                select(User).where(
                    User.company_id == pm.company_id,
                    User.enabled == True,  # noqa: E712
                )
            ).all()
        )

        for u in users:
            notif = {
                "user_id": u.id,
                "email": u.email,
                "pm_id": pm.id,
                "pm_title": pm.title,
                "due_date": schedule.next_due_date.isoformat() if schedule.next_due_date else None,
            }
            notifications.append(notif)
            logger.info("Notifying user %s about upcoming PM %s", u.email, pm.title)

    return notifications
