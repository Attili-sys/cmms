"""Turn a stored invitation into an enabled account and send its welcome email."""

from __future__ import annotations

import logging

from ajnkit.logger import log
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.company import Company
from src.models.users import Role, User, UserInvitation, UserSettings
from src.services.welcome_email import send_welcome

logger = logging.getLogger(__name__)
REQUESTED_ADMIN_EMAIL = "elradie@aljazeera.net"


def _display_name(email: str) -> str:
    local = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return local.title() if local else "New"


def fulfill_invitations(db: Session, company_id: int | None = None) -> list[str]:
    """Create any invited people who do not yet have an account, then welcome them.

    An invitation stays in place when Canvas refuses the message, so the next
    application start can try again. A refusal that says the message may already
    have been sent closes the invitation instead.
    """
    invitations = db.scalars(select(UserInvitation).order_by(UserInvitation.id)).all()
    welcomed: list[str] = []
    for invitation in invitations:
        email = (invitation.email or "").strip().lower()
        role = db.get(Role, invitation.role_id)
        company = (
            db.get(Company, company_id)
            if company_id is not None
            else db.scalar(select(Company).order_by(Company.id))
        )
        if not email or role is None or company is None:
            logger.warning("invitation %s cannot be fulfilled yet", invitation.id)
            continue

        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            settings = UserSettings(
                email_notified=True,
                email_updates_for_work_orders=True,
                email_updates_for_requests=True,
                email_updates_for_purchase_orders=True,
                stats_for_assigned_work_orders=False,
            )
            db.add(settings)
            db.flush()
            first_name = _display_name(email)
            user = User(
                first_name=first_name,
                last_name="",
                email=email,
                phone="",
                username=email,
                password="sso-managed-account",  # noqa: S106
                rate=0,
                enabled=True,
                owns_company=False,
                enabled_in_subscription=True,
                created_via_sso=True,
                role_id=role.id,
                company_id=company.id,
                user_settings_id=settings.id,
            )
            db.add(user)
            db.flush()
        elif user.role_id != role.id:
            user.role_id = role.id

        delivered = send_welcome(
            email,
            first_name=user.first_name,
            role_name=role.name,
            company_name=company.name,
        )
        if delivered:
            db.delete(invitation)
            welcomed.append(email)
        db.commit()
    log.info(
        "account invitations fulfilled",
        extra={"checked": len(invitations), "welcomed": welcomed},
    )
    return welcomed


def ensure_requested_administrator(db: Session) -> None:
    """Make the requested Canvas administrator exist, then welcome them once."""
    email = REQUESTED_ADMIN_EMAIL
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    pending = db.scalar(
        select(UserInvitation).where(func.lower(UserInvitation.email) == email)
    )
    if user is not None and pending is None:
        role = db.get(Role, user.role_id)
        log.info(
            "requested administrator present",
            extra={"email": email, "role": role.name if role is not None else None},
        )
        return
    if pending is None:
        role = db.scalar(
            select(Role).where(func.lower(Role.name) == "administrator").order_by(Role.id)
        )
        if role is None:
            log.warning("administrator role missing", extra={"email": email})
            return
        db.add(UserInvitation(email=email, role_id=role.id))
        db.commit()
    fulfill_invitations(db)
