"""Asset downtime monitoring and alert job."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import AssetDowntime

logger = logging.getLogger(__name__)


def notify_ongoing_downtimes(
    db: Session,
    now: datetime | None = None,
    threshold_minutes: int = 0,
) -> list[dict]:
    """Find active ongoing asset downtime records (duration == 0) and generate alerts."""
    if now is None:
        now = datetime.now(timezone.utc)

    stmt = select(AssetDowntime).where(AssetDowntime.duration == 0)
    active_downtimes = list(db.scalars(stmt).all())
    alerts: list[dict] = []

    for dt in active_downtimes:
        elapsed_minutes = 0.0
        if dt.starts_on:
            starts = dt.starts_on
            if starts.tzinfo is None and now.tzinfo is not None:
                starts = starts.replace(tzinfo=timezone.utc)
            elif starts.tzinfo is not None and now.tzinfo is None:
                starts = starts.replace(tzinfo=None)
            diff = (now - starts).total_seconds()
            elapsed_minutes = max(0.0, diff / 60.0)

        if elapsed_minutes >= threshold_minutes:
            alert = {
                "downtime_id": dt.id,
                "asset_id": dt.asset_id,
                "company_id": dt.company_id,
                "starts_on": dt.starts_on.isoformat() if dt.starts_on else None,
                "elapsed_minutes": round(elapsed_minutes, 1),
            }
            alerts.append(alert)
            logger.warning(
                "Ongoing downtime on asset %s (downtime_id=%s) has lasted %.1f minutes",
                dt.asset_id,
                dt.id,
                elapsed_minutes,
            )

    return alerts
