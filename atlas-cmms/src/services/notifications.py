"""In-app bell notification helper matching Java NotificationService lifecycle triggers."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.associations import t_team_user_associations
from src.models.enums import NotificationType
from src.models.files_custom import Notification

_NOTIFICATION_TYPE_ORDINALS: dict[str, int] = {
    member.value: idx for idx, member in enumerate(NotificationType)
}


def resolve_notification_type_ordinal(ntype: NotificationType | str | int) -> int:
    """Resolve NotificationType enum/string/int to its SmallInteger ordinal."""
    if isinstance(ntype, int):
        return ntype
    key = ntype.value if isinstance(ntype, NotificationType) else str(ntype).strip().upper()
    return _NOTIFICATION_TYPE_ORDINALS.get(key, 0)


def create_in_app_notifications(
    db: Session,
    *,
    user_ids: Iterable[int | None] = (),
    team_ids: Iterable[int | None] = (),
    message: str,
    notification_type: NotificationType | str | int,
    resource_id: int | None,
    exclude_user_id: int | None = None,
    created_by: int | None = None,
) -> list[Notification]:
    """Create in-app bell Notification rows for target users and team members."""
    target_users: set[int] = {int(uid) for uid in user_ids if uid is not None}
    clean_teams = [int(tid) for tid in team_ids if tid is not None]
    if clean_teams:
        team_member_ids = db.scalars(
            select(t_team_user_associations.c.id_user).where(
                t_team_user_associations.c.id_team.in_(clean_teams)
            )
        ).all()
        target_users.update(int(uid) for uid in team_member_ids if uid is not None)

    if exclude_user_id is not None:
        target_users.discard(int(exclude_user_id))

    ntype_ordinal = resolve_notification_type_ordinal(notification_type)
    created: list[Notification] = []
    for uid in sorted(target_users):
        notif = Notification(
            user_id=uid,
            message=message[:255],
            notification_type=ntype_ordinal,
            resource_id=resource_id,
            seen=False,
            created_by=created_by,
        )
        db.add(notif)
        created.append(notif)
    if created:
        db.flush()
    return created
