"""Current user authentication and auto-provisioning dependency."""

import logging
from fastapi import Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ajnkit.identity import Caller, caller
from src import envs
from src.deps.db import get_db
from src.models._base import utcnow
from src.models.associations import (
    role_create_permissions,
    role_delete_other_permissions,
    role_edit_other_permissions,
    role_view_other_permissions,
    role_view_permissions,
)
from src.models.company import Company, Currency
from src.models.enums import PermissionEntity
from src.models.integrations import ApiKey
from src.models.settings import (
    CompanySettings,
    FieldConfiguration,
    GeneralPreferences,
    UiConfiguration,
    WorkOrderConfiguration,
    WorkOrderRequestConfiguration,
)
from src.models.users import Role, User, UserSettings
from src.schemas.errors import CustomException

logger = logging.getLogger("app.auth")

DEFAULT_WO_FIELDS = (
    "description",
    "asset",
    "priority",
    "images",
    "primaryUser",
    "assignedTo",
    "team",
    "location",
    "dueDate",
    "category",
    "purchaseOrder",
    "files",
    "signature",
    "completeFiles",
    "completeTasks",
    "completeTime",
    "completeParts",
    "completeCost",
)

DEFAULT_WOR_FIELDS = (
    "asset",
    "location",
    "primaryUser",
    "dueDate",
    "category",
    "team",
)


def _ensure_company_settings(db: Session, company: Company) -> CompanySettings:
    """Ensure CompanySettings and its child configurations exist for the given Company."""
    cs = db.get(CompanySettings, company.company_settings_id) if company.company_settings_id else None
    if not cs:
        cs = db.scalar(select(CompanySettings).where(CompanySettings.company_id == company.id))
    if not cs:
        cs = CompanySettings(company_id=company.id)
        db.add(cs)
        db.flush()

    currency = db.scalar(select(Currency).limit(1))
    if not currency:
        currency = Currency(code="$", name="USD")
        db.add(currency)
        db.flush()

    gp = db.get(GeneralPreferences, cs.general_preferences_id) if cs.general_preferences_id else None
    if not gp:
        gp = db.scalar(select(GeneralPreferences).where(GeneralPreferences.company_settings_id == cs.id))
    if not gp:
        gp = GeneralPreferences(
            ask_feed_back_onwoclosed=False,
            auto_assign_requests=False,
            auto_assign_work_orders=False,
            business_type=0,
            date_format=0,
            disable_closed_work_orders_notif=False,
            labor_cost_in_total_cost=True,
            language=0,
            time_zone="UTC",
            wo_update_for_requesters=True,
            company_settings_id=cs.id,
            currency_id=currency.id,
            simplified_work_order=False,
            days_before_prev_maint_notification=1,
            csv_separator=",",
            auto_generate_asset_barcode=False,
            color=None,
        )
        db.add(gp)
        db.flush()
    cs.general_preferences_id = gp.id

    wo_cfg = db.get(WorkOrderConfiguration, cs.work_order_configuration_id) if cs.work_order_configuration_id else None
    if not wo_cfg:
        wo_cfg = WorkOrderConfiguration(company_settings_id=cs.id)
        db.add(wo_cfg)
        db.flush()
    cs.work_order_configuration_id = wo_cfg.id

    existing_wo_fields = {
        fc.field_name
        for fc in db.scalars(
            select(FieldConfiguration).where(FieldConfiguration.work_order_configuration_id == wo_cfg.id)
        ).all()
    }
    for fname in DEFAULT_WO_FIELDS:
        if fname not in existing_wo_fields:
            db.add(
                FieldConfiguration(
                    field_name=fname,
                    field_type=0,
                    work_order_configuration_id=wo_cfg.id,
                )
            )
    db.flush()

    wor_cfg = db.get(WorkOrderRequestConfiguration, cs.work_order_request_configuration_id) if cs.work_order_request_configuration_id else None
    if not wor_cfg:
        wor_cfg = WorkOrderRequestConfiguration(company_settings_id=cs.id)
        db.add(wor_cfg)
        db.flush()
    cs.work_order_request_configuration_id = wor_cfg.id

    existing_wor_fields = {
        fc.field_name
        for fc in db.scalars(
            select(FieldConfiguration).where(
                FieldConfiguration.work_order_request_configuration_id == wor_cfg.id
            )
        ).all()
    }
    for fname in DEFAULT_WOR_FIELDS:
        if fname not in existing_wor_fields:
            db.add(
                FieldConfiguration(
                    field_name=fname,
                    field_type=0,
                    work_order_request_configuration_id=wor_cfg.id,
                )
            )
    db.flush()

    ui_cfg = db.get(UiConfiguration, cs.ui_configuration_id) if cs.ui_configuration_id else None
    if not ui_cfg:
        ui_cfg = db.scalar(select(UiConfiguration).where(UiConfiguration.company_settings_id == cs.id))
    if not ui_cfg:
        ui_cfg = UiConfiguration(
            requests=True,
            locations=True,
            meters=True,
            vendors_and_customers=True,
            company_settings_id=cs.id,
        )
        db.add(ui_cfg)
        db.flush()
    cs.ui_configuration_id = ui_cfg.id

    company.company_settings_id = cs.id
    db.flush()
    return cs


def _grant_all_permissions(db: Session, role_id: int) -> None:
    existing = db.scalars(
        select(role_view_permissions.c.view_permissions).where(
            role_view_permissions.c.role_id == role_id
        )
    ).all()
    if existing:
        return
    for entity_ord in range(len(PermissionEntity)):
        db.execute(role_create_permissions.insert().values(role_id=role_id, create_permissions=entity_ord))
        db.execute(role_view_permissions.insert().values(role_id=role_id, view_permissions=entity_ord))
        db.execute(role_view_other_permissions.insert().values(role_id=role_id, view_other_permissions=entity_ord))
        db.execute(role_edit_other_permissions.insert().values(role_id=role_id, edit_other_permissions=entity_ord))
        db.execute(role_delete_other_permissions.insert().values(role_id=role_id, delete_other_permissions=entity_ord))


def _bootstrap_first_company_and_admin(db: Session, who: Caller) -> User:
    """Bootstrap single Company and default roles on empty database, returning super admin User."""
    logger.warning("Empty database: auto-provisioning first Company and ROLE_SUPER_ADMIN user for %s", who.email)

    company = db.scalar(select(Company).limit(1))
    if not company:
        company = Company(
            name=getattr(envs, "COMPANY_NAME", "AJ CAFM"),
            employees_count=1,
            first_work_order_created=False,
            invited_users=False,
            imported_assets=False,
        )
        db.add(company)
        db.flush()

    _ensure_company_settings(db, company)

    super_role = db.scalar(select(Role).where(Role.name == "ROLE_SUPER_ADMIN"))
    if not super_role:
        super_role = Role(
            name="ROLE_SUPER_ADMIN",
            role_type=0,
            paid=True,
            code=0,
            description="Super Administrator",
        )
        db.add(super_role)
        db.flush()
    _grant_all_permissions(db, super_role.id)

    admin_role = db.scalar(select(Role).where(Role.name == "Administrator"))
    if not admin_role:
        admin_role = Role(
            name="Administrator",
            role_type=1,
            paid=True,
            code=0,
            description="Administrator",
        )
        db.add(admin_role)
        db.flush()
    _grant_all_permissions(db, admin_role.id)

    client_role = db.scalar(select(Role).where(Role.name == "Requester"))
    if not client_role:
        client_role = Role(
            name="Requester",
            role_type=1,
            paid=False,
            code=5,
            description="Requester",
        )
        db.add(client_role)
        db.flush()

    us = UserSettings(
        email_notified=True,
        email_updates_for_work_orders=True,
        email_updates_for_requests=True,
        email_updates_for_purchase_orders=True,
        stats_for_assigned_work_orders=False,
    )
    db.add(us)
    db.flush()

    name_str = (who.name or "Super Admin").strip()
    parts = name_str.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    email = who.email or "admin@canvas.local"
    user = User(
        email=email,
        username=email,
        first_name=first_name,
        last_name=last_name,
        company_id=company.id,
        role_id=super_role.id,
        user_settings_id=us.id,
        owns_company=True,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _provision_sso_user(db: Session, who: Caller) -> User:
    """Auto-join new SSO identity to the primary Company."""
    company = db.scalar(select(Company).limit(1))
    if not company:
        company = Company(
            name=getattr(envs, "COMPANY_NAME", "Atlas CMMS"),
            employees_count=1,
            first_work_order_created=False,
            invited_users=False,
            imported_assets=False,
        )
        db.add(company)
        db.flush()

    _ensure_company_settings(db, company)

    role = db.scalar(select(Role).where(Role.role_type == 1).order_by(Role.id))
    if not role:
        role = db.scalar(select(Role).order_by(Role.id))
    if not role:
        role = Role(
            name="Requester",
            role_type=1,
            paid=False,
            code=5,
            description="Default SSO Role",
        )
        db.add(role)
        db.flush()

    us = UserSettings(
        email_notified=True,
        email_updates_for_work_orders=True,
        email_updates_for_requests=True,
        email_updates_for_purchase_orders=True,
        stats_for_assigned_work_orders=False,
    )
    db.add(us)
    db.flush()

    name_str = (who.name or "User").strip()
    parts = name_str.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    email = who.email or "user@canvas.local"
    user = User(
        email=email,
        username=email,
        first_name=first_name,
        last_name=last_name,
        company_id=company.id,
        role_id=role.id,
        user_settings_id=us.id,
        owns_company=False,
        enabled=True,
        enabled_in_subscription=True,
        created_via_sso=True,
        password="",
        rate=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency resolving current authenticated User via SSO headers or Bearer API token."""
    cached = getattr(request.state, "current_user", None)
    if cached is not None:
        return cached

    who = caller(request.headers)
    if not who.email:
        fwd_email = request.headers.get("X-Forwarded-Email")
        if fwd_email:
            who = Caller(
                email=fwd_email,
                name=request.headers.get("X-Forwarded-User") or fwd_email.split("@")[0],
                groups=who.groups,
            )
    if who.email:
        user = db.scalar(select(User).where(func.lower(User.email) == who.email.lower()))
        if user is not None:
            if not user.enabled:
                raise CustomException(status_code=403, message="Account is disabled")
            request.state.current_user = user
            return user

        user_count = db.scalar(select(func.count(User.id))) or 0
        if user_count == 0:
            user = _bootstrap_first_company_and_admin(db, who)
        else:
            user = _provision_sso_user(db, who)

        request.state.current_user = user
        return user

    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        if token:
            now = utcnow()
            api_key = db.scalar(
                select(ApiKey).where(
                    ApiKey.code == token,
                    ApiKey.revoked_at.is_(None),
                )
            )
            if api_key is not None and (
                api_key.expires_at is None
                or api_key.expires_at.replace(tzinfo=now.tzinfo) > now
            ):
                user = db.get(User, api_key.user_id)
                if user is not None and user.enabled:
                    api_key.last_used = now
                    db.commit()
                    request.state.current_user = user
                    return user

    raise CustomException(status_code=401, message="Unauthorized")
