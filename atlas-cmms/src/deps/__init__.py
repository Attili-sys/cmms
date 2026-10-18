"""FastAPI dependencies package for db, current_user, company isolation, and permissions."""

from src.deps.company import assert_same_company, is_super_admin, scoped_select
from src.deps.current_user import get_current_user
from src.deps.db import SessionLocal, get_db
from src.deps.permissions import (
    can_create,
    can_delete,
    can_edit,
    can_view,
    require_permission,
    require_role,
)

__all__ = [
    "SessionLocal",
    "assert_same_company",
    "can_create",
    "can_delete",
    "can_edit",
    "can_view",
    "get_current_user",
    "get_db",
    "is_super_admin",
    "require_permission",
    "require_role",
    "scoped_select",
]
