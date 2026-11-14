"""Routes for Auth, License, Subscription, SubscriptionPlan, Companies, Users, Roles, Teams."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import (
    DEFAULT_WO_FIELDS,
    DEFAULT_WOR_FIELDS,
    _ensure_company_settings,
    get_current_user,
)
from src.deps.db import get_db
from src.deps.permissions import can_create, can_delete, can_edit, can_view
from src.models.associations import (
    role_create_permissions,
    role_delete_other_permissions,
    role_edit_other_permissions,
    role_view_other_permissions,
    role_view_permissions,
    t_team_user_associations,
)
from src.models.company import Company, Currency, Subscription, SubscriptionPlan
from src.models.enums import PermissionEntity
from src.models.settings import (
    CompanySettings,
    FieldConfiguration,
    GeneralPreferences,
    UiConfiguration,
    WorkOrderConfiguration,
    WorkOrderRequestConfiguration,
)
from src.models.users import Role, Team, User, UserInvitation, UserSettings
from src.services.account_invitations import fulfill_invitations
from src.services.welcome_email import send_welcome
from src.routes._crud import (
    _ensure_company_settings_id,
    build_crud_router,
    validate_foreign_key_ownership,
)
from src.schemas.errors import CustomException, SuccessResponse
from src.services.license_service import (
    LicenseService,
    serialize_subscription,
    serialize_subscription_plan,
)
from src.services.serializer import apply_patch, model_to_dict
from src.utils.search import SearchCriteria, execute_search

router = APIRouter()
_ENTITY_BY_ORD = {idx: member.value for idx, member in enumerate(PermissionEntity)}
_ORD_BY_ENTITY = {member.value: idx for idx, member in enumerate(PermissionEntity)}
_ALL_ENTITIES = [member.value for member in PermissionEntity]
_DEFAULT_JWT = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJjYW52YXMtc3NvIiwiZXhwIjo0MTAyNDQ0ODAwfQ."


def serialize_role(role: Role | None, db: Session) -> dict[str, Any]:
    if role is None:
        return {}
    base = model_to_dict(role, db=db)
    create_ords = db.scalars(
        select(role_create_permissions.c.create_permissions).where(
            role_create_permissions.c.role_id == role.id
        )
    ).all()
    view_ords = db.scalars(
        select(role_view_permissions.c.view_permissions).where(
            role_view_permissions.c.role_id == role.id
        )
    ).all()
    view_other_ords = db.scalars(
        select(role_view_other_permissions.c.view_other_permissions).where(
            role_view_other_permissions.c.role_id == role.id
        )
    ).all()
    edit_other_ords = db.scalars(
        select(role_edit_other_permissions.c.edit_other_permissions).where(
            role_edit_other_permissions.c.role_id == role.id
        )
    ).all()
    delete_other_ords = db.scalars(
        select(role_delete_other_permissions.c.delete_other_permissions).where(
            role_delete_other_permissions.c.role_id == role.id
        )
    ).all()

    is_admin = role.role_type == 0 or role.name in ("ROLE_SUPER_ADMIN", "Administrator")
    base["createPermissions"] = [_ENTITY_BY_ORD.get(o, o) for o in create_ords] or (_ALL_ENTITIES if is_admin else [])
    base["viewPermissions"] = [_ENTITY_BY_ORD.get(o, o) for o in view_ords] or (_ALL_ENTITIES if is_admin else [])
    base["viewOtherPermissions"] = [_ENTITY_BY_ORD.get(o, o) for o in view_other_ords] or (_ALL_ENTITIES if is_admin else [])
    base["editOtherPermissions"] = [_ENTITY_BY_ORD.get(o, o) for o in edit_other_ords] or (_ALL_ENTITIES if is_admin else [])
    base["deleteOtherPermissions"] = [_ENTITY_BY_ORD.get(o, o) for o in delete_other_ords] or (_ALL_ENTITIES if is_admin else [])
    return base


def _sync_role_permissions(role_id: int, payload: dict[str, Any], db: Session) -> None:
    perm_tables = [
        ("createPermissions", role_create_permissions, "create_permissions"),
        ("viewPermissions", role_view_permissions, "view_permissions"),
        ("viewOtherPermissions", role_view_other_permissions, "view_other_permissions"),
        ("editOtherPermissions", role_edit_other_permissions, "edit_other_permissions"),
        ("deleteOtherPermissions", role_delete_other_permissions, "delete_other_permissions"),
    ]
    for key, tbl, col_name in perm_tables:
        if key in payload and isinstance(payload[key], list):
            db.execute(tbl.delete().where(tbl.c.role_id == role_id))
            for item in payload[key]:
                ord_val = _ORD_BY_ENTITY.get(str(item), item if isinstance(item, int) else None)
                if ord_val is not None:
                    db.execute(tbl.insert().values({"role_id": role_id, col_name: ord_val}))


def serialize_general_preferences(gp: GeneralPreferences | None, db: Session) -> dict[str, Any]:
    default_currency = {"id": 1, "code": "QR", "name": "Qatari Riyal"}
    if gp is None:
        return {
            "id": 1,
            "language": "EN",
            "dateFormat": "DDMMYY",
            "currency": default_currency,
            "businessType": "GENERAL_ASSET_MANAGEMENT",
            "timeZone": "UTC",
            "daysBeforePrevMaintNotification": 1,
            "csvSeparator": ",",
            "autoAssignWorkOrders": False,
            "autoAssignRequests": False,
            "disableClosedWorkOrdersNotif": False,
            "askFeedBackOnWOClosed": False,
            "laborCostInTotalCost": True,
            "woUpdateForRequesters": True,
            "simplifiedWorkOrder": False,
            "autoGenerateAssetBarcode": False,
            "color": None,
        }
    res = model_to_dict(gp, db=db)
    cur = db.get(Currency, gp.currency_id) if gp.currency_id else db.scalar(select(Currency).limit(1))
    res["currency"] = model_to_dict(cur, db=db) if cur else default_currency
    res["language"] = res.get("language") or "EN"
    res["dateFormat"] = res.get("dateFormat") or "DDMMYY"
    res["businessType"] = res.get("businessType") or "GENERAL_ASSET_MANAGEMENT"
    res["timeZone"] = res.get("timeZone") or "UTC"
    res["askFeedBackOnWOClosed"] = bool(gp.ask_feed_back_onwoclosed)
    return res


def serialize_company_settings(cs: CompanySettings | None, db: Session) -> dict[str, Any]:
    default_wo_fcs = [
        {"id": idx + 1, "fieldName": fname, "fieldType": "OPTIONAL"}
        for idx, fname in enumerate(DEFAULT_WO_FIELDS)
    ]
    default_wor_fcs = [
        {"id": 100 + idx + 1, "fieldName": fname, "fieldType": "OPTIONAL"}
        for idx, fname in enumerate(DEFAULT_WOR_FIELDS)
    ]
    if cs is None:
        return {
            "id": 1,
            "generalPreferences": serialize_general_preferences(None, db),
            "workOrderConfiguration": {"id": 1, "workOrderFieldConfigurations": default_wo_fcs},
            "workOrderRequestConfiguration": {"id": 1, "fieldConfigurations": default_wor_fcs},
            "fieldConfigurations": default_wo_fcs + default_wor_fcs,
        }
    res = model_to_dict(cs, db=db)
    gp = db.get(GeneralPreferences, cs.general_preferences_id) if cs.general_preferences_id else None
    if not gp:
        gp = db.scalar(select(GeneralPreferences).where(GeneralPreferences.company_settings_id == cs.id))
    res["generalPreferences"] = serialize_general_preferences(gp, db)

    wo_cfg = db.get(WorkOrderConfiguration, cs.work_order_configuration_id) if cs.work_order_configuration_id else None
    if not wo_cfg:
        wo_cfg = db.scalar(
            select(WorkOrderConfiguration).where(WorkOrderConfiguration.company_settings_id == cs.id)
        )
    wo_rows = (
        list(
            db.scalars(
                select(FieldConfiguration).where(
                    FieldConfiguration.work_order_configuration_id == wo_cfg.id
                )
            ).all()
        )
        if wo_cfg
        else []
    )
    if wo_cfg and len(wo_rows) < len(DEFAULT_WO_FIELDS):
        existing_names = {fc.field_name for fc in wo_rows}
        for fname in DEFAULT_WO_FIELDS:
            if fname not in existing_names:
                new_fc = FieldConfiguration(
                    field_name=fname,
                    field_type=0,
                    work_order_configuration_id=wo_cfg.id,
                )
                db.add(new_fc)
                wo_rows.append(new_fc)
        db.commit()
    wo_fields = [model_to_dict(fc, db=db) for fc in wo_rows] if wo_rows else default_wo_fcs
    res["workOrderConfiguration"] = {
        "id": wo_cfg.id if wo_cfg else 1,
        "workOrderFieldConfigurations": wo_fields,
    }

    wor_cfg = db.get(WorkOrderRequestConfiguration, cs.work_order_request_configuration_id) if cs.work_order_request_configuration_id else None
    if not wor_cfg:
        wor_cfg = db.scalar(
            select(WorkOrderRequestConfiguration).where(
                WorkOrderRequestConfiguration.company_settings_id == cs.id
            )
        )
    wor_rows = (
        list(
            db.scalars(
                select(FieldConfiguration).where(
                    FieldConfiguration.work_order_request_configuration_id == wor_cfg.id
                )
            ).all()
        )
        if wor_cfg
        else []
    )
    if wor_cfg and len(wor_rows) < len(DEFAULT_WOR_FIELDS):
        existing_wor_names = {fc.field_name for fc in wor_rows}
        for fname in DEFAULT_WOR_FIELDS:
            if fname not in existing_wor_names:
                new_fc = FieldConfiguration(
                    field_name=fname,
                    field_type=0,
                    work_order_request_configuration_id=wor_cfg.id,
                )
                db.add(new_fc)
                wor_rows.append(new_fc)
        db.commit()
    wor_fields = [model_to_dict(fc, db=db) for fc in wor_rows] if wor_rows else default_wor_fcs
    res["workOrderRequestConfiguration"] = {
        "id": wor_cfg.id if wor_cfg else 1,
        "fieldConfigurations": wor_fields,
    }
    res["fieldConfigurations"] = wo_fields + wor_fields
    return res


def serialize_company(company: Company | None, db: Session) -> dict[str, Any]:
    if company is None:
        return {}
    cs = _ensure_company_settings(db, company)
    db.commit()
    base = model_to_dict(company, db=db)
    sub = db.get(Subscription, company.subscription_id) if company.subscription_id else None
    base["subscription"] = serialize_subscription(sub, db)
    base["companySettings"] = serialize_company_settings(cs, db)
    return base


def serialize_user(user: User | None, db: Session) -> dict[str, Any]:
    if user is None:
        return {}
    base = model_to_dict(user, db=db, exclude={"password"})
    role = db.get(Role, user.role_id) if user.role_id else None
    company = db.get(Company, user.company_id) if user.company_id else None
    base["role"] = serialize_role(role, db) if role else None
    base["companyId"] = user.company_id
    base["companySettingsId"] = (company.company_settings_id if company and company.company_settings_id else 1)
    base["userSettingsId"] = user.user_settings_id or 1
    base["superAccountRelations"] = []
    default_ui = {
        "id": 1,
        "requests": True,
        "locations": True,
        "meters": True,
        "vendorsAndCustomers": True,
    }
    base["uiConfiguration"] = default_ui
    if company and company.company_settings_id:
        ui_cfg = db.scalar(
            select(UiConfiguration).where(
                UiConfiguration.company_settings_id == company.company_settings_id
            )
        )
        if ui_cfg:
            base["uiConfiguration"] = model_to_dict(ui_cfg, db=db)
    return base


# 6.1 Auth & License
@router.get("/auth/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return serialize_user(current_user, db)


@router.post("/auth/signin")
def signin(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {
        "accessToken": _DEFAULT_JWT,
        "refreshToken": "canvas-sso-refresh",
        "tokenType": "Bearer",
        "expiresAt": "2099-12-31T23:59:59.000Z",
    }


@router.post("/auth/signup")
def signup(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {"success": True, "message": "Account provisioned via SSO"}


@router.post("/auth/refresh")
def refresh_token(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {
        "accessToken": _DEFAULT_JWT,
        "refreshToken": "canvas-sso-refresh",
        "tokenType": "Bearer",
        "expiresAt": "2099-12-31T23:59:59.000Z",
    }


@router.get("/auth/resetpwd")
def reset_password(email: str = Query(default="")) -> dict[str, Any]:
    return {"success": True, "message": "Password managed by Canvas SSO"}


@router.post("/auth/resetpwd")
def confirm_reset_password(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {"success": True, "message": "Password managed by Canvas SSO"}


@router.patch("/auth/updatePassword")
@router.post("/auth/updatepwd")
def update_password(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {"success": True, "message": "Password managed by Canvas SSO"}


@router.post("/auth/logout")
def logout() -> dict[str, Any]:
    return {"success": True, "message": "Logged out"}


@router.post("/auth/delete-account-request")
def delete_account_request(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {"success": True, "message": "Request submitted"}


@router.get("/auth/switch-account")
def switch_account(id: int = Query(default=1)) -> dict[str, Any]:
    return {
        "accessToken": _DEFAULT_JWT,
        "refreshToken": "canvas-sso-refresh",
        "tokenType": "Bearer",
        "expiresAt": "2099-12-31T23:59:59.000Z",
    }


@router.get("/license/validity")
def get_license_validity() -> dict[str, Any]:
    return {"valid": LicenseService.is_license_valid(), "unrestricted": LicenseService.is_unrestricted_self_hosted()}


_ALL_LICENSE_ENTITLEMENTS: list[str] = [
    "SSO",
    "WORK_ORDER_HISTORY",
    "WORKFLOW",
    "MULTI_INSTANCE",
    "WEBHOOK",
    "BRANDING",
    "NFC_BARCODE",
    "CUSTOM_ROLES",
    "FILE_ATTACHMENTS",
    "TIME_TRACKING",
    "COST_TRACKING",
    "WORK_ORDER_LINKING",
    "SIGNATURE_CAPTURE",
    "PM_CALENDAR",
    "CONDITION_BASED_PM",
    "ASSET_HIERARCHY",
    "ASSET_DOWNTIME",
    "LOW_STOCK_ALERTS",
    "PARTS_COST_TRACKING",
    "CUSTOMER_VENDOR",
    "FIELD_CONFIGURATION",
    "VOICE_NOTES",
    "ADVANCED_ANALYTICS",
    "API_ACCESS",
    "UNLIMITED_ASSETS",
    "UNLIMITED_LOCATIONS",
    "UNLIMITED_PARTS",
    "UNLIMITED_PM_SCHEDULES",
    "UNLIMITED_ACTIVE_WORK_ORDERS",
    "UNLIMITED_CHECKLISTS",
    "UNLIMITED_METERS",
    "UNLIMITED_USERS",
    "REQUEST_PORTAL",
    "RESOURCE_PLANNING",
]


@router.get("/license/state")
def get_license_state() -> dict[str, Any]:
    return {
        "valid": LicenseService.is_license_valid(),
        "unrestricted": LicenseService.is_unrestricted_self_hosted(),
        "state": "VALID",
        "entitlements": _ALL_LICENSE_ENTITLEMENTS,
        "expirationDate": "2099-12-31T23:59:59.000Z",
        "planName": "ENTERPRISE",
    }


@router.get("/subscription-plans")
def list_subscription_plans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    plans = db.scalars(select(SubscriptionPlan)).all()
    if not plans:
        return [serialize_subscription_plan(None)]
    return [serialize_subscription_plan(p) for p in plans]


@router.post("/subscriptions/upgrade")
def upgrade_subscription(
    payload: Any = Body(default=None),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "success": True,
        "url": "",
        "message": "Unrestricted self-hosted edition requires no subscription upgrade",
    }


@router.get("/subscriptions/downgrade")
def downgrade_subscription(
    usersIds: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return SuccessResponse(
        success=True,
        message="Unrestricted self-hosted edition",
    ).model_dump()


@router.get("/subscriptions/{sub_id:int}")
def get_subscription(
    sub_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    sub = db.get(Subscription, sub_id)
    owner_co = db.scalar(select(Company).where(Company.subscription_id == sub_id))
    if owner_co is not None:
        assert_company_access(
            current_user, owner_co.id, is_super_admin=is_super_admin(current_user, db)
        )
    return serialize_subscription(sub, db)


@router.patch("/subscriptions/{sub_id:int}")
def patch_subscription(
    sub_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    sub = db.get(Subscription, sub_id)
    owner_co = db.scalar(select(Company).where(Company.subscription_id == sub_id))
    if owner_co is not None:
        assert_company_access(
            current_user, owner_co.id, is_super_admin=is_super_admin(current_user, db)
        )
    if sub:
        apply_patch(sub, payload)
        db.commit()
        db.refresh(sub)
    return serialize_subscription(sub, db)


# 6.2 Companies & CompanySettings
@router.get("/companies/{company_id:int}")
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if not company:
        raise CustomException(status_code=404, message="Company not found")
    assert_company_access(current_user, company_id, is_super_admin=is_super_admin(current_user, db))
    return serialize_company(company, db)


@router.patch("/companies/{company_id:int}")
def patch_company(
    company_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    company = db.get(Company, company_id)
    if not company:
        raise CustomException(status_code=404, message="Company not found")
    assert_company_access(current_user, company_id, is_super_admin=is_super_admin(current_user, db))
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    apply_patch(company, payload)
    db.commit()
    db.refresh(company)
    return serialize_company(company, db)


@router.get("/company-settings/{cs_id:int}")
def get_company_settings(
    cs_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    own_cs_id = _ensure_company_settings_id(current_user, db)
    cs = db.get(CompanySettings, cs_id)
    if not cs:
        cs = db.get(CompanySettings, own_cs_id)
        db.commit()
    elif cs.id != own_cs_id:
        owner_company_id = cs.company_id or db.scalar(
            select(Company.id).where(Company.company_settings_id == cs.id)
        )
        assert_company_access(
            current_user,
            owner_company_id,
            is_super_admin=is_super_admin(current_user, db),
            db=db,
        )
    return serialize_company_settings(cs, db)


@router.get("/general-preferences/{gp_id:int}")
def get_general_preferences(
    gp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    cs_id = _ensure_company_settings_id(current_user, db)
    gp = db.get(GeneralPreferences, gp_id)
    if not gp:
        gp = db.scalar(select(GeneralPreferences).where(GeneralPreferences.company_settings_id == cs_id))
    elif gp.company_settings_id is not None and gp.company_settings_id != cs_id:
        raise CustomException(status_code=403, message="Access is denied")
    if not gp:
        raise CustomException(status_code=404, message="GeneralPreferences not found")
    return serialize_general_preferences(gp, db)


@router.patch("/general-preferences/{gp_id:int}")
def patch_general_preferences(
    gp_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    cs_id = _ensure_company_settings_id(current_user, db)
    gp = db.get(GeneralPreferences, gp_id)
    if not gp:
        gp = db.scalar(select(GeneralPreferences).where(GeneralPreferences.company_settings_id == cs_id))
    elif gp.company_settings_id is not None and gp.company_settings_id != cs_id:
        raise CustomException(status_code=403, message="Access is denied")
    if not gp:
        gp = GeneralPreferences(
            id=gp_id,
            company_settings_id=cs_id,
            ask_feed_back_onwoclosed=False,
            auto_assign_requests=False,
            auto_assign_work_orders=False,
            disable_closed_work_orders_notif=False,
            labor_cost_in_total_cost=True,
            time_zone="UTC",
            wo_update_for_requesters=True,
            simplified_work_order=False,
            days_before_prev_maint_notification=1,
        )
        db.add(gp)
    apply_patch(gp, payload)
    db.commit()
    db.refresh(gp)
    return serialize_general_preferences(gp, db)


@router.patch("/field-configurations/{fc_id:int}")
def patch_field_configuration(
    fc_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    fc = db.get(FieldConfiguration, fc_id)
    if not fc:
        raise CustomException(status_code=404, message="FieldConfiguration not found")
    cs_id = _ensure_company_settings_id(current_user, db)
    if fc.work_order_configuration_id is not None:
        woc = db.get(WorkOrderConfiguration, fc.work_order_configuration_id)
        if woc and woc.company_settings_id is not None and woc.company_settings_id != cs_id:
            raise CustomException(status_code=403, message="Access is denied")
    if fc.work_order_request_configuration_id is not None:
        worc = db.get(WorkOrderRequestConfiguration, fc.work_order_request_configuration_id)
        if worc and worc.company_settings_id is not None and worc.company_settings_id != cs_id:
            raise CustomException(status_code=403, message="Access is denied")
    apply_patch(fc, payload)
    db.commit()
    db.refresh(fc)
    return model_to_dict(fc, db=db)


@router.patch("/ui-configurations")
def patch_ui_configuration(
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    cs_id = _ensure_company_settings_id(current_user, db)
    ui = db.scalar(select(UiConfiguration).where(UiConfiguration.company_settings_id == cs_id))
    if not ui:
        ui = UiConfiguration(
            company_settings_id=cs_id,
            requests=True,
            locations=True,
            meters=True,
            vendors_and_customers=True,
        )
        db.add(ui)
    apply_patch(ui, payload)
    db.commit()
    db.refresh(ui)
    return model_to_dict(ui, db=db)


# 6.3 Users, Roles, Teams, UserSettings
def _assert_user_settings_access(us_id: int, current_user: User, db: Session) -> None:
    if us_id == current_user.user_settings_id:
        return
    owner = db.scalar(select(User).where(User.user_settings_id == us_id))
    if owner is not None and owner.company_id != current_user.company_id:
        assert_company_access(current_user, owner, is_super_admin=is_super_admin(current_user, db), db=db)


@router.get("/user-settings/{us_id:int}")
def get_user_settings(
    us_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _assert_user_settings_access(us_id, current_user, db)
    us = db.get(UserSettings, us_id)
    if not us:
        us = UserSettings(
            id=us_id,
            email_notified=True,
            email_updates_for_work_orders=True,
            email_updates_for_requests=True,
            email_updates_for_purchase_orders=True,
            stats_for_assigned_work_orders=False,
        )
        db.add(us)
        db.commit()
        db.refresh(us)
    return model_to_dict(us, db=db)


@router.patch("/user-settings/{us_id:int}")
def patch_user_settings(
    us_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _assert_user_settings_access(us_id, current_user, db)
    us = db.get(UserSettings, us_id)
    if not us:
        us = UserSettings(
            id=us_id,
            email_notified=True,
            email_updates_for_work_orders=True,
            email_updates_for_requests=True,
            email_updates_for_purchase_orders=True,
            stats_for_assigned_work_orders=False,
        )
        db.add(us)
    apply_patch(us, payload)
    db.commit()
    db.refresh(us)
    return model_to_dict(us, db=db)


@router.post("/users/search")
def search_users(
    criteria: SearchCriteria = Body(default_factory=SearchCriteria),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return execute_search(
        db=db,
        model_cls=User,
        criteria=criteria,
        company_id=current_user.company_id,
        serializer=lambda u: serialize_user(u, db),
    )


@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(User).where(User.company_id == current_user.company_id)).all()
    return [serialize_user(u, db) for u in rows]


@router.post("/users")
def create_user(
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_create(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    cs_id = _ensure_company_settings_id(current_user, db)
    role_id = payload.get("role", {}).get("id") if isinstance(payload.get("role"), dict) else payload.get("roleId")
    if role_id:
        target_role = db.get(Role, int(role_id))
        if not target_role or (target_role.company_settings_id is not None and target_role.company_settings_id != cs_id):
            raise CustomException(status_code=403, message="Role does not belong to this company")
        if target_role.role_type == 0 and not is_super_admin(current_user, db):
            raise CustomException(status_code=403, message="Cannot assign super admin role")
    else:
        role = db.scalar(
            select(Role).where(
                (Role.company_settings_id == cs_id) | (Role.company_settings_id.is_(None))
            ).order_by(Role.id)
        )
        role_id = role.id if role else current_user.role_id

    us = UserSettings(
        email_notified=True,
        email_updates_for_work_orders=True,
        email_updates_for_requests=True,
        email_updates_for_purchase_orders=True,
        stats_for_assigned_work_orders=False,
    )
    db.add(us)
    db.flush()

    u = User(
        first_name=payload.get("firstName", "New"),
        last_name=payload.get("lastName", "User"),
        email=(payload.get("email") or "user@canvas.local").strip().lower(),
        phone=payload.get("phone") or "",
        job_title=payload.get("jobTitle"),
        username=(payload.get("email") or "user@canvas.local").strip().lower(),
        password="sso-managed-account",  # noqa: S106
        rate=int(float(payload.get("rate") or 0)),
        enabled=True,
        owns_company=False,
        enabled_in_subscription=True,
        created_via_sso=False,
        role_id=role_id,
        company_id=current_user.company_id,
        user_settings_id=us.id,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    role = db.get(Role, u.role_id)
    company = db.get(Company, u.company_id)
    send_welcome(
        u.email,
        first_name=u.first_name,
        role_name=role.name if role is not None else None,
        company_name=company.name if company is not None else None,
    )
    return serialize_user(u, db)


@router.get("/users/mini")
def list_users_mini(
    with_requesters: bool = Query(default=False, alias="withRequesters"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(User)
        .outerjoin(Role, User.role_id == Role.id)
        .where(
            User.company_id == current_user.company_id,
            User.enabled.is_(True),
        )
    )
    if not with_requesters:
        # Java's findWorkersByCompany excludes VIEW_ONLY (ordinal 4) and REQUESTER (ordinal 5).
        stmt = stmt.where(or_(Role.code.is_(None), Role.code.notin_([4, 5])))
    rows = db.scalars(stmt).all()
    return [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in rows
    ]


@router.get("/users/mini/disabled")
def list_disabled_users_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(User).where(
            User.company_id == current_user.company_id,
            User.enabled.is_(False),
        )
    ).all()
    return [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in rows
    ]


@router.get("/users/invitations/last-week")
def get_last_week_invitations(
    current_user: User = Depends(get_current_user),
) -> int:
    return 0


@router.post("/users/invite")
def invite_user(
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_create(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    cs_id = _ensure_company_settings_id(current_user, db)
    role_id = payload.get("role", {}).get("id") if isinstance(payload.get("role"), dict) else payload.get("roleId")
    if role_id:
        target_role = db.get(Role, int(role_id))
        if not target_role or (target_role.company_settings_id is not None and target_role.company_settings_id != cs_id):
            raise CustomException(status_code=403, message="Role does not belong to this company")
        if target_role.role_type == 0 and not is_super_admin(current_user, db):
            raise CustomException(status_code=403, message="Cannot assign super admin role")
    else:
        role = db.scalar(
            select(Role).where(
                (Role.company_settings_id == cs_id) | (Role.company_settings_id.is_(None))
            ).order_by(Role.id)
        )
        role_id = role.id if role else current_user.role_id

    raw_emails = payload.get("emails")
    if isinstance(raw_emails, list):
        emails = [str(e).strip().lower() for e in raw_emails if str(e).strip()]
    else:
        single = (payload.get("email") or "").strip().lower()
        emails = [single] if single else []
    if not emails:
        raise CustomException(status_code=400, message="At least one email is required")
    if len(emails) > 20:
        raise CustomException(status_code=400, message="Invite at most 20 people at a time")

    for email in emails:
        already = db.scalar(select(User).where(User.email == email))
        pending = db.scalar(
            select(UserInvitation).where(UserInvitation.email == email)
        )
        if already is None and pending is None:
            db.add(UserInvitation(email=email, role_id=role_id))
    db.commit()
    welcomed = fulfill_invitations(db, current_user.company_id)
    return {"success": True, "message": "Invitation sent", "welcomed": welcomed}


@router.get("/users/{user_id:int}")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    return serialize_user(u, db)


@router.patch("/users/{user_id:int}")
def patch_user(
    user_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    if current_user.id != user_id and not can_edit(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    apply_patch(
        u,
        payload,
        exclude={
            "password",
            "role_id",
            "owns_company",
            "company_id",
            "super_account_id",
            "enabled_in_subscription",
        },
    )
    validate_foreign_key_ownership(u, current_user, db)
    db.commit()
    db.refresh(u)
    return serialize_user(u, db)


@router.patch("/users/{user_id:int}/disable")
def disable_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_edit(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    if user_id == current_user.id or u.owns_company:
        raise CustomException(status_code=406, message="Cannot disable this user")
    u.enabled = False
    db.commit()
    db.refresh(u)
    return serialize_user(u, db)


@router.patch("/users/{user_id:int}/enable")
def enable_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_edit(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    u.enabled = True
    db.commit()
    db.refresh(u)
    return serialize_user(u, db)


@router.patch("/users/{user_id:int}/role")
def update_user_role(
    user_id: int,
    role: int = Query(default=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_edit(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    if user_id == current_user.id or u.owns_company:
        raise CustomException(status_code=406, message="Cannot change role of this user")
    cs_id = _ensure_company_settings_id(current_user, db)
    target_role = db.get(Role, role)
    if not target_role or (target_role.company_settings_id is not None and target_role.company_settings_id != cs_id):
        raise CustomException(status_code=403, message="Role does not belong to this company")
    if target_role.role_type == 0 and not is_super_admin(current_user, db):
        raise CustomException(status_code=403, message="Cannot assign super admin role")
    u.role_id = role
    db.commit()
    db.refresh(u)
    return serialize_user(u, db)


@router.delete("/users/{user_id:int}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_delete(current_user, PermissionEntity.PEOPLE_AND_TEAMS, db):
        raise CustomException(status_code=403, message="Access is denied")
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    if user_id == current_user.id or u.owns_company:
        raise CustomException(status_code=406, message="Cannot delete this user")
    db.delete(u)
    db.commit()
    return SuccessResponse(success=True, message="User deleted").model_dump()


@router.patch("/shift-configurations/user/{user_id:int}")
def patch_shift_configuration(
    user_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    u = db.get(User, user_id)
    if not u:
        raise CustomException(status_code=404, message="User not found")
    assert_company_access(current_user, u, is_super_admin=is_super_admin(current_user, db))
    return serialize_user(u, db)


# Roles
def _assert_role_access(role: Role, current_user: User, db: Session, *, allow_system: bool = True) -> None:
    cs_id = _ensure_company_settings_id(current_user, db)
    if (
        role.company_settings_id is not None
        and role.company_settings_id != cs_id
        and not (current_user.company_id is None and is_super_admin(current_user, db))
    ):
        raise CustomException(status_code=403, message="Access is denied")
    if not allow_system:
        is_system = role.role_type == 0 or (
            role.code is not None and role.code not in (4, 6, "USER_CREATED")
        )
        if is_system:
            raise CustomException(status_code=403, message="Default roles cannot be modified or deleted")


def _assert_can_grant_permissions(current_user: User, payload: dict[str, Any], db: Session) -> None:
    if is_super_admin(current_user, db) or current_user.owns_company:
        return
    caller_role_obj = db.get(Role, current_user.role_id) if current_user.role_id else None
    caller_role = serialize_role(caller_role_obj, db)
    for key in (
        "createPermissions",
        "viewPermissions",
        "viewOtherPermissions",
        "editOtherPermissions",
        "deleteOtherPermissions",
    ):
        req_perms = payload.get(key)
        if isinstance(req_perms, list):
            allowed = {str(p) for p in caller_role.get(key, [])}
            for item in req_perms:
                name = _ENTITY_BY_ORD.get(item, str(item)) if isinstance(item, int) else str(item)
                if name not in allowed:
                    raise CustomException(
                        status_code=403,
                        message="You don't have permission to grant these permissions",
                    )


@router.get("/roles")
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    cs_id = _ensure_company_settings_id(current_user, db)
    rows = db.scalars(
        select(Role).where(
            (Role.company_settings_id == cs_id) | (Role.company_settings_id.is_(None))
        )
    ).all()
    return [serialize_role(r, db) for r in rows]


@router.post("/roles")
def create_role(
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    _assert_can_grant_permissions(current_user, payload, db)
    cs_id = _ensure_company_settings_id(current_user, db)
    role = Role(
        name=payload.get("name", "Custom Role"),
        description=payload.get("description"),
        paid=bool(payload.get("paid", True)),
        role_type=1,
        code=6,
        company_settings_id=cs_id,
    )
    db.add(role)
    db.flush()
    _sync_role_permissions(role.id, payload, db)
    db.commit()
    db.refresh(role)
    return serialize_role(role, db)


@router.get("/roles/{role_id:int}")
def get_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    role = db.get(Role, role_id)
    if not role:
        raise CustomException(status_code=404, message="Role not found")
    _assert_role_access(role, current_user, db, allow_system=True)
    return serialize_role(role, db)


@router.patch("/roles/{role_id:int}")
def patch_role(
    role_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    role = db.get(Role, role_id)
    if not role:
        raise CustomException(status_code=404, message="Role not found")
    _assert_role_access(role, current_user, db, allow_system=False)
    _assert_can_grant_permissions(current_user, payload, db)
    apply_patch(role, payload, exclude={"role_type", "code", "company_settings_id"})
    _sync_role_permissions(role.id, payload, db)
    db.commit()
    db.refresh(role)
    return serialize_role(role, db)


@router.delete("/roles/{role_id:int}")
def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.SETTINGS, db):
        raise CustomException(status_code=403, message="Access is denied")
    role = db.get(Role, role_id)
    if not role:
        raise CustomException(status_code=404, message="Role not found")
    _assert_role_access(role, current_user, db, allow_system=False)
    db.delete(role)
    db.commit()
    return SuccessResponse(success=True, message="Role deleted").model_dump()


# Teams
def _serialize_team(team: Team, db: Session) -> dict[str, Any]:
    base = model_to_dict(team, db=db)
    user_ids = db.scalars(
        select(t_team_user_associations.c.id_user).where(
            t_team_user_associations.c.id_team == team.id
        )
    ).all()
    users = (
        db.scalars(
            select(User).where(User.id.in_(user_ids), User.company_id == team.company_id)
        ).all()
        if user_ids
        else []
    )
    base["users"] = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]
    return base


def _sync_team_users(team: Team, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if "users" in payload and isinstance(payload["users"], list):
        db.execute(
            t_team_user_associations.delete().where(t_team_user_associations.c.id_team == team.id)
        )
        for item in payload["users"]:
            uid = item.get("id") if isinstance(item, dict) else item
            if isinstance(uid, int):
                target_u = db.get(User, uid)
                if not target_u or target_u.company_id != team.company_id:
                    raise CustomException(
                        status_code=400,
                        message="Foreign key user does not belong to your company",
                    )
                db.execute(
                    t_team_user_associations.insert().values(id_team=team.id, id_user=uid)
                )



teams_router = build_crud_router(
    "/teams",
    Team,
    custom_serializer=_serialize_team,
    after_create=_sync_team_users,
    after_patch=_sync_team_users,
)


@teams_router.get("/mini")
def list_teams_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Team).where(Team.company_id == current_user.company_id)).all()
    return [{"id": t.id, "name": t.name} for t in rows]


router.include_router(teams_router)
router.include_router(build_crud_router("/currencies", Currency))

