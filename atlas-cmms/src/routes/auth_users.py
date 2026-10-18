"""Routes for Auth, License, Subscription, SubscriptionPlan, Companies, Users, Roles, Teams."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import (
    DEFAULT_WO_FIELDS,
    DEFAULT_WOR_FIELDS,
    _ensure_company_settings,
    get_current_user,
)
from src.deps.db import get_db
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
from src.routes._crud import build_crud_router
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
    default_currency = {"id": 1, "code": "$", "name": "USD"}
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
def update_password(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return {"success": True, "message": "Password managed by Canvas SSO"}


@router.get("/license/validity")
def get_license_validity() -> dict[str, Any]:
    return {"valid": LicenseService.is_license_valid(), "unrestricted": LicenseService.is_unrestricted_self_hosted()}


@router.get("/subscription-plans")
def list_subscription_plans(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    plans = db.scalars(select(SubscriptionPlan)).all()
    if not plans:
        return [serialize_subscription_plan(None)]
    return [serialize_subscription_plan(p) for p in plans]


@router.get("/subscriptions/{sub_id:int}")
def get_subscription(sub_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    sub = db.get(Subscription, sub_id)
    return serialize_subscription(sub, db)


@router.patch("/subscriptions/{sub_id:int}")
def patch_subscription(
    sub_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    sub = db.get(Subscription, sub_id)
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
    cs = db.get(CompanySettings, cs_id)
    if not cs:
        cs = CompanySettings(id=cs_id, company_id=current_user.company_id)
        db.add(cs)
        db.commit()
        db.refresh(cs)
    return serialize_company_settings(cs, db)


@router.patch("/general-preferences/{gp_id:int}")
def patch_general_preferences(
    gp_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    gp = db.get(GeneralPreferences, gp_id)
    if not gp:
        gp = GeneralPreferences(id=gp_id)
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
    fc = db.get(FieldConfiguration, fc_id)
    if not fc:
        raise CustomException(status_code=404, message="FieldConfiguration not found")
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
    ui = db.scalar(select(UiConfiguration).limit(1))
    if not ui:
        ui = UiConfiguration()
        db.add(ui)
    apply_patch(ui, payload)
    db.commit()
    db.refresh(ui)
    return model_to_dict(ui, db=db)


# 6.3 Users, Roles, Teams, UserSettings
@router.get("/user-settings/{us_id:int}")
def get_user_settings(
    us_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
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


@router.get("/users/mini")
def list_users_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(User).where(User.company_id == current_user.company_id)).all()
    return [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in rows
    ]


@router.post("/users/invite")
def invite_user(
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    email = (payload.get("email") or "").strip().lower()
    role_id = payload.get("role", {}).get("id") if isinstance(payload.get("role"), dict) else payload.get("roleId")
    if not role_id:
        role = db.scalar(select(Role).order_by(Role.id))
        role_id = role.id if role else 1
    inv = UserInvitation(email=email, role_id=role_id)
    db.add(inv)
    db.commit()
    return {"success": True, "message": "Invitation recorded"}


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
    apply_patch(u, payload, exclude={"password"})
    db.commit()
    db.refresh(u)
    return serialize_user(u, db)


# Roles
@router.get("/roles")
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Role)).all()
    return [serialize_role(r, db) for r in rows]


@router.post("/roles")
def create_role(
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    role = Role(
        name=payload.get("name", "Custom Role"),
        description=payload.get("description"),
        paid=bool(payload.get("paid", True)),
        role_type=1,
        code=4,
        company_settings_id=payload.get("companySettingsId"),
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
    return serialize_role(role, db)


@router.patch("/roles/{role_id:int}")
def patch_role(
    role_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    role = db.get(Role, role_id)
    if not role:
        raise CustomException(status_code=404, message="Role not found")
    apply_patch(role, payload)
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
    role = db.get(Role, role_id)
    if not role:
        raise CustomException(status_code=404, message="Role not found")
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
    users = db.scalars(select(User).where(User.id.in_(user_ids))).all() if user_ids else []
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
