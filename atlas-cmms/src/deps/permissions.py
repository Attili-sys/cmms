"""Role and permission evaluation dependencies."""

from collections.abc import Callable
from typing import Any
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.deps.company import is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models.associations import (
    role_create_permissions,
    role_delete_other_permissions,
    role_edit_other_permissions,
    role_view_other_permissions,
    role_view_permissions,
)
from src.models.enums import PermissionEntity, RoleType
from src.models.users import Role, User
from src.schemas.errors import CustomException

_ENTITY_ORDINALS = {member.value: idx for idx, member in enumerate(PermissionEntity)}


def _resolve_ordinal(entity: PermissionEntity | str) -> int:
    name = entity.value if isinstance(entity, PermissionEntity) else str(entity)
    if name not in _ENTITY_ORDINALS:
        raise ValueError(f"Unknown PermissionEntity: {entity}")
    return _ENTITY_ORDINALS[name]


def can_view(user: User, entity: PermissionEntity | str, db: Session, own: bool = True) -> bool:
    """Check whether user can view instances of an entity."""
    if is_super_admin(user, db):
        return True
    if not user.role_id:
        return False

    ordinal = _resolve_ordinal(entity)
    table = role_view_permissions if own else role_view_other_permissions
    col = table.c.view_permissions if own else table.c.view_other_permissions

    count = db.scalar(
        select(func.count())
        .select_from(table)
        .where(table.c.role_id == user.role_id, col == ordinal)
    )
    return bool(count and count > 0)


def can_edit(user: User, entity: PermissionEntity | str, db: Session, own: bool = True) -> bool:
    """Check whether user can edit instances of an entity."""
    if is_super_admin(user, db):
        return True
    if not user.role_id:
        return False

    ordinal = _resolve_ordinal(entity)
    table = role_edit_other_permissions
    col = table.c.edit_other_permissions

    count = db.scalar(
        select(func.count())
        .select_from(table)
        .where(table.c.role_id == user.role_id, col == ordinal)
    )
    return bool(count and count > 0)


def can_delete(user: User, entity: PermissionEntity | str, db: Session, own: bool = True) -> bool:
    """Check whether user can delete instances of an entity."""
    if is_super_admin(user, db):
        return True
    if not user.role_id:
        return False

    ordinal = _resolve_ordinal(entity)
    table = role_delete_other_permissions
    col = table.c.delete_other_permissions

    count = db.scalar(
        select(func.count())
        .select_from(table)
        .where(table.c.role_id == user.role_id, col == ordinal)
    )
    return bool(count and count > 0)


def can_create(user: User, entity: PermissionEntity | str, db: Session) -> bool:
    """Check whether user can create instances of an entity."""
    if is_super_admin(user, db):
        return True
    if not user.role_id:
        return False

    ordinal = _resolve_ordinal(entity)
    table = role_create_permissions
    col = table.c.create_permissions

    count = db.scalar(
        select(func.count())
        .select_from(table)
        .where(table.c.role_id == user.role_id, col == ordinal)
    )
    return bool(count and count > 0)


def require_role(*allowed_roles: Any) -> Callable[..., User]:
    """FastAPI dependency factory enforcing that current_user has one of the allowed roles."""

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if is_super_admin(current_user, db):
            return current_user

        role = db.get(Role, current_user.role_id) if current_user.role_id else None
        if role is not None:
            for allowed in allowed_roles:
                if (
                    role.name == allowed
                    or role.role_type == allowed
                    or (hasattr(role, "code") and role.code == allowed)
                    or (isinstance(allowed, RoleType) and role.name == allowed.value)
                ):
                    return current_user

        raise CustomException(status_code=403, message="Access is denied")

    return dependency


def require_permission(
    entity: PermissionEntity | str,
    action: str = "view",
    own: bool = False,
) -> Callable[..., User]:
    """FastAPI dependency factory enforcing that current_user has permission on entity."""

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        allowed = False
        action_lower = action.lower()
        if action_lower == "view":
            allowed = can_view(current_user, entity, db, own=own)
        elif action_lower in ("edit", "update"):
            allowed = can_edit(current_user, entity, db, own=own)
        elif action_lower in ("delete", "remove"):
            allowed = can_delete(current_user, entity, db, own=own)
        elif action_lower in ("create", "add"):
            allowed = can_create(current_user, entity, db)

        if not allowed:
            raise CustomException(status_code=403, message="Access is denied")
        return current_user

    return dependency
