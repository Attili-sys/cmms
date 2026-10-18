"""Multi-tenant company isolation and scoping dependencies."""

from typing import Any
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from src.models.enums import RoleType
from src.models.users import SuperAccountRelation, User
from src.schemas.errors import CustomException


def is_super_admin(user: User, db: Session | None = None) -> bool:
    """Check if user has super admin privileges."""
    if getattr(user, "owns_company", False) and getattr(user, "company_id", None) is None:
        return True
    role = getattr(user, "role", None)
    if role is not None:
        role_type = getattr(role, "role_type", None)
        if role_type in (0, RoleType.ROLE_SUPER_ADMIN, "ROLE_SUPER_ADMIN"):
            return True
        if getattr(role, "name", "") in ("ROLE_SUPER_ADMIN", "SUPER_ADMIN"):
            return True
    elif getattr(user, "role_id", None) is not None and db is not None:
        from src.models.users import Role

        r = db.get(Role, user.role_id)
        if r is not None and (
            r.role_type in (0, RoleType.ROLE_SUPER_ADMIN, "ROLE_SUPER_ADMIN")
            or r.name in ("ROLE_SUPER_ADMIN", "SUPER_ADMIN")
        ):
            return True
    return False


def get_accessible_company_ids(current_user: User, db: Session | None = None) -> list[int]:
    """Return all company IDs accessible to current_user including child companies from SuperAccountRelation."""
    company_ids: list[int] = []
    if current_user.company_id is not None:
        company_ids.append(current_user.company_id)

    if db is not None and current_user.id is not None:
        relations = db.scalars(
            select(SuperAccountRelation).where(SuperAccountRelation.super_user_id == current_user.id)
        ).all()
        for rel in relations:
            child = db.get(User, rel.child_user_id)
            if child and child.company_id and child.company_id not in company_ids:
                company_ids.append(child.company_id)

    return company_ids


def assert_same_company(
    entity_or_company_id: Any,
    current_user: User,
    db: Session | None = None,
) -> None:
    """Enforce entity.company_id == current_user.company_id unless bypassed by super admin or SuperAccountRelation.

    Raises CustomException(403, "Access is denied") on mismatch.
    """
    if is_super_admin(current_user, db):
        return

    target_company_id: int | None = None
    if isinstance(entity_or_company_id, int):
        target_company_id = entity_or_company_id
    elif hasattr(entity_or_company_id, "company_id"):
        target_company_id = entity_or_company_id.company_id
    elif hasattr(entity_or_company_id, "company") and getattr(entity_or_company_id.company, "id", None):
        target_company_id = entity_or_company_id.company.id

    if target_company_id is None:
        return

    accessible_ids = get_accessible_company_ids(current_user, db)
    if target_company_id in accessible_ids:
        return

    raise CustomException(status_code=403, message="Access is denied")


def scoped_select(
    model: type[Any],
    current_user: User,
    db: Session | None = None,
) -> Select:
    """Return a SQLAlchemy select(model) scoped to the companies accessible to current_user."""
    stmt = select(model)
    if is_super_admin(current_user, db):
        return stmt

    if hasattr(model, "company_id"):
        accessible_ids = get_accessible_company_ids(current_user, db)
        if len(accessible_ids) == 1:
            stmt = stmt.where(model.company_id == accessible_ids[0])
        elif len(accessible_ids) > 1:
            stmt = stmt.where(model.company_id.in_(accessible_ids))
    return stmt


def assert_company_access(
    current_user: User,
    entity: Any,
    is_super_admin: bool = False,
    db: Session | None = None,
) -> None:
    """Compatibility wrapper for assert_same_company."""
    if is_super_admin:
        return
    assert_same_company(entity, current_user, db=db)
