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
    preventive_maintenance_assigned_to,
    request_assigned_to,
    role_create_permissions,
    role_delete_other_permissions,
    role_edit_other_permissions,
    role_view_other_permissions,
    role_view_permissions,
    t_asset_user_associations,
    t_location_user_associations,
    t_meter_user_associations,
    t_part_user_associations,
    work_order_assigned_to,
)
from src.models.enums import PermissionEntity, RoleType
from src.models.users import Role, User
from src.schemas.errors import CustomException

_ENTITY_ORDINALS = {member.value: idx for idx, member in enumerate(PermissionEntity)}

_ASSIGNED_USER_TABLES: dict[str, tuple[Any, str, str]] = {
    "Asset": (t_asset_user_associations, "id_asset", "id_user"),
    "Location": (t_location_user_associations, "id_location", "id_user"),
    "Meter": (t_meter_user_associations, "id_meter", "id_user"),
    "Part": (t_part_user_associations, "id_part", "id_user"),
    "WorkOrder": (work_order_assigned_to, "work_order_id", "assigned_to_id"),
    "PreventiveMaintenance": (
        preventive_maintenance_assigned_to,
        "preventive_maintenance_id",
        "assigned_to_id",
    ),
    "Request": (request_assigned_to, "request_id", "assigned_to_id"),
}


def _resolve_ordinal(entity: PermissionEntity | str) -> int:
    name = entity.value if isinstance(entity, PermissionEntity) else str(entity)
    if name not in _ENTITY_ORDINALS:
        raise ValueError(f"Unknown PermissionEntity: {entity}")
    return _ENTITY_ORDINALS[name]


def _is_admin_role(user: User, db: Session) -> bool:
    if is_super_admin(user, db):
        return True
    if getattr(user, "owns_company", False):
        return True
    if not user.role_id:
        return False
    role = getattr(user, "role", None) or db.get(Role, user.role_id)
    if role is not None and (
        role.name in ("ROLE_SUPER_ADMIN", "Administrator")
        or getattr(role, "code", None) in (0, "ADMIN")
    ):
        return True
    return False


def can_view(user: User, entity: PermissionEntity | str, db: Session, own: bool = True) -> bool:
    """Check whether user can view instances of an entity."""
    if _is_admin_role(user, db):
        return True
    if not user.role_id:
        return False

    ordinal = _resolve_ordinal(entity)
    if not own:
        count_other = db.scalar(
            select(func.count())
            .select_from(role_view_other_permissions)
            .where(
                role_view_other_permissions.c.role_id == user.role_id,
                role_view_other_permissions.c.view_other_permissions == ordinal,
            )
        )
        return bool(count_other and count_other > 0)

    count_own = db.scalar(
        select(func.count())
        .select_from(role_view_permissions)
        .where(
            role_view_permissions.c.role_id == user.role_id,
            role_view_permissions.c.view_permissions == ordinal,
        )
    )
    if count_own and count_own > 0:
        return True
    count_other = db.scalar(
        select(func.count())
        .select_from(role_view_other_permissions)
        .where(
            role_view_other_permissions.c.role_id == user.role_id,
            role_view_other_permissions.c.view_other_permissions == ordinal,
        )
    )
    return bool(count_other and count_other > 0)


def can_edit(user: User, entity: PermissionEntity | str, db: Session, own: bool = True) -> bool:
    """Check whether user has edit_other permission on an entity."""
    if _is_admin_role(user, db):
        return True
    if not user.role_id:
        return False
    if entity in (PermissionEntity.SETTINGS, "SETTINGS"):
        return can_view(user, PermissionEntity.SETTINGS, db)

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
    """Check whether user has delete_other permission on an entity."""
    if _is_admin_role(user, db):
        return True
    if not user.role_id:
        return False
    if entity in (PermissionEntity.SETTINGS, "SETTINGS"):
        return can_view(user, PermissionEntity.SETTINGS, db)

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
    if _is_admin_role(user, db):
        return True
    if not user.role_id:
        return False
    if entity in (PermissionEntity.SETTINGS, "SETTINGS"):
        return can_view(user, PermissionEntity.SETTINGS, db)

    ordinal = _resolve_ordinal(entity)
    table = role_create_permissions
    col = table.c.create_permissions

    count = db.scalar(
        select(func.count())
        .select_from(table)
        .where(table.c.role_id == user.role_id, col == ordinal)
    )
    return bool(count and count > 0)


def is_assigned_to_object(user: User, obj: Any, db: Session) -> bool:
    """Check whether user.id is in the object's assigned users association table (matching Java)."""
    if user.id is None or getattr(obj, "id", None) is None:
        return False
    cls_name = obj.__class__.__name__
    assoc = _ASSIGNED_USER_TABLES.get(cls_name)
    if assoc is None:
        return False
    tbl, entity_col, user_col = assoc
    cnt = db.scalar(
        select(func.count())
        .select_from(tbl)
        .where(
            getattr(tbl.c, entity_col) == obj.id,
            getattr(tbl.c, user_col) == user.id,
        )
    )
    return bool(cnt and cnt > 0)


def can_edit_object(user: User, entity: PermissionEntity | str, obj: Any, db: Session) -> bool:
    """Java-parity canBeEditedBy(User) check (Asset.java:244-250, CategoryAbstract.java:80-83).

    - Allowed if role has edit_other permission on entity.
    - Or if obj.created_by == user.id.
    - Or (for non-Category entities) if user is in obj's assigned users association table.
      Note: primary_user_id on Asset does NOT grant edit permission in Java.
    """
    if can_edit(user, entity, db):
        return True
    if getattr(obj, "created_by", None) is not None and obj.created_by == user.id:
        return True
    entity_name = entity.value if isinstance(entity, PermissionEntity) else str(entity)
    if entity_name in ("CATEGORIES", "CATEGORIES_WEB") or obj.__class__.__name__.endswith("Category"):
        return False
    return is_assigned_to_object(user, obj, db)


def can_delete_object(user: User, entity: PermissionEntity | str, obj: Any, db: Session) -> bool:
    """Java-parity canBeDeletedBy(User) check (Asset.java:252-256, CategoryAbstract.java:85-88).

    - Allowed ONLY if role has delete_other permission on entity, OR obj.created_by == user.id.
    - Being in assignedTo or primaryUser does NOT grant delete permission.
    """
    if can_delete(user, entity, db):
        return True
    if getattr(obj, "created_by", None) is not None and obj.created_by == user.id:
        return True
    return False


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
    own: bool = True,
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

