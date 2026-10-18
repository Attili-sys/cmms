"""Database cleanup jobs (expired tokens, etc.)."""

import logging
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.models import RefreshToken, VerificationToken

logger = logging.getLogger(__name__)


def cleanup_expired_tokens(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Delete expired RefreshToken and VerificationToken rows from the database."""
    if now is None:
        now = datetime.now(timezone.utc)

    rt_stmt = delete(RefreshToken).where(
        (RefreshToken.expires_at <= now) | (RefreshToken.revoked == True)  # noqa: E712
    )
    rt_result = db.execute(rt_stmt)
    rt_count = rt_result.rowcount if rt_result.rowcount is not None else 0

    vt_stmt = delete(VerificationToken).where(
        VerificationToken.expiry_date <= now
    )
    vt_result = db.execute(vt_stmt)
    vt_count = vt_result.rowcount if vt_result.rowcount is not None else 0

    db.commit()
    logger.info(
        "Cleaned up expired tokens: %d refresh tokens, %d verification tokens",
        rt_count,
        vt_count,
    )
    return {"refresh_tokens": rt_count, "verification_tokens": vt_count}
