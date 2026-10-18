"""Tests for permissions evaluation, role requirements, and multi-tenant scoping."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.deps.company import assert_same_company, is_super_admin, scoped_select
from src.deps.permissions import (
    can_create,
    can_delete,
    can_edit,
    can_view,
    require_permission,
    require_role,
)
from src.models._base import Base
from src.models.associations import (
    role_edit_other_permissions,
    role_view_permissions,
)
from src.models.company import Company
from src.models.enums import PermissionEntity
from src.models.users import Role, SuperAccountRelation, User
from src.models.work_orders import WorkOrder
from src.schemas.errors import CustomException


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_super_admin_bypasses_all_permissions(db_session):
    company = Company(id=1, name="Acme", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    role_super = Role(id=1, name="ROLE_SUPER_ADMIN", role_type=0, paid=True)
    super_user = User(
        id=1,
        email="super@acme.com",
        username="super",
        first_name="Super",
        last_name="Admin",
        company_id=1,
        role_id=1,
        owns_company=True,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    db_session.add_all([company, role_super, super_user])
    db_session.commit()

    assert is_super_admin(super_user, db_session) is True
    assert can_view(super_user, PermissionEntity.WORK_ORDERS, db_session) is True
    assert can_edit(super_user, PermissionEntity.ASSETS, db_session) is True
    assert can_delete(super_user, PermissionEntity.PARTS_AND_MULTIPARTS, db_session) is True
    assert can_create(super_user, PermissionEntity.METERS, db_session) is True


def test_client_role_permissions(db_session):
    company = Company(id=1, name="Acme", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    role = Role(id=2, name="Technician", role_type=1, paid=True)
    tech = User(
        id=2,
        email="tech@acme.com",
        username="tech",
        first_name="Tech",
        last_name="User",
        company_id=1,
        role_id=2,
        owns_company=False,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    db_session.add_all([company, role, tech])
    db_session.commit()

    # WO ordinal = 3
    wo_ord = 3
    db_session.execute(role_view_permissions.insert().values(role_id=2, view_permissions=wo_ord))
    db_session.execute(role_edit_other_permissions.insert().values(role_id=2, edit_other_permissions=wo_ord))
    db_session.commit()

    # Can view own WO, but not others
    assert can_view(tech, PermissionEntity.WORK_ORDERS, db_session, own=True) is True
    assert can_view(tech, PermissionEntity.WORK_ORDERS, db_session, own=False) is False

    # Can edit WO
    assert can_edit(tech, "WORK_ORDERS", db_session) is True

    # Cannot delete WO
    assert can_delete(tech, PermissionEntity.WORK_ORDERS, db_session) is False

    # Cannot view Assets (ordinal 5)
    assert can_view(tech, PermissionEntity.ASSETS, db_session) is False


def test_require_role_and_permission_dependencies(db_session):
    company = Company(id=1, name="Acme", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    role = Role(id=2, name="Technician", role_type=1, paid=True)
    user = User(
        id=2,
        email="tech@acme.com",
        username="tech",
        first_name="Tech",
        last_name="User",
        company_id=1,
        role_id=2,
        owns_company=False,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    db_session.add_all([company, role, user])
    db_session.commit()

    # Role check passing
    dep_role_ok = require_role("Technician")
    assert dep_role_ok(current_user=user, db=db_session) == user

    # Role check failing
    dep_role_fail = require_role("Administrator", "ROLE_SUPER_ADMIN")
    with pytest.raises(CustomException) as exc_info:
        dep_role_fail(current_user=user, db=db_session)
    assert exc_info.value.status_code == 403

    # Permission check failing
    dep_perm_fail = require_permission(PermissionEntity.REQUESTS, action="delete")
    with pytest.raises(CustomException) as exc_info:
        dep_perm_fail(current_user=user, db=db_session)
    assert exc_info.value.status_code == 403


def test_assert_same_company_and_super_account_relation(db_session):
    c1 = Company(id=1, name="Acme Corp", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    c2 = Company(id=2, name="Beta Branch", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    c3 = Company(id=3, name="Gamma Branch", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)

    role = Role(id=1, name="Manager", role_type=1, paid=True)

    super_parent = User(
        id=10,
        email="parent@acme.com",
        username="parent",
        first_name="Parent",
        last_name="User",
        company_id=1,
        role_id=1,
        owns_company=False,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    child_user = User(
        id=20,
        email="child@beta.com",
        username="child",
        first_name="Child",
        last_name="User",
        company_id=2,
        role_id=1,
        owns_company=False,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    rel = SuperAccountRelation(id=1, super_user_id=10, child_user_id=20)
    db_session.add_all([c1, c2, c3, role, super_parent, child_user, rel])
    db_session.commit()

    # Same company passes
    assert_same_company(1, super_parent, db_session)

    # Child company via SuperAccountRelation passes
    assert_same_company(2, super_parent, db_session)

    # Unrelated company fails with 403
    with pytest.raises(CustomException) as exc_info:
        assert_same_company(3, super_parent, db_session)
    assert exc_info.value.status_code == 403


def test_scoped_select(db_session):
    c1 = Company(id=1, name="C1", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    c2 = Company(id=2, name="C2", employees_count=1, first_work_order_created=False, invited_users=False, imported_assets=False)
    role = Role(id=1, name="User", role_type=1, paid=True)
    user = User(
        id=1,
        email="u1@c1.com",
        username="u1",
        first_name="U1",
        last_name="Last",
        company_id=1,
        role_id=1,
        owns_company=False,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    db_session.add_all([c1, c2, role, user])
    db_session.commit()

    # scoped_select filters by company_id == 1
    stmt = scoped_select(WorkOrder, user, db_session)
    compiled = str(stmt)
    assert "work_order.company_id" in compiled
