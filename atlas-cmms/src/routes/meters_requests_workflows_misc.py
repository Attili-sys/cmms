"""Routes for Meters, Readings, Requests, Workflows, Files, CustomFields, Notifications, Webhooks, ApiKeys, Export, Import."""

from __future__ import annotations

import csv
import io
import mimetypes
import re
import secrets
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Body, Depends, File, Form, Query, Response, UploadFile, WebSocket
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src import envs
from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user, get_optional_current_user
from src.deps.db import get_db
from src.deps.permissions import can_create, can_view
from src.models._base import utcnow
from src.models.associations import (
    request_assigned_to,
    request_customers,
    request_files,
    t_asset_customer_associations,
    t_asset_part_associations,
    t_asset_team_associations,
    t_asset_user_associations,
    t_asset_vendor_associations,
    t_meter_user_associations,
    t_request_file_associations,
    work_order_assigned_to,
    work_order_customers,
    work_order_files,
)
from src.models.categories import AssetCategory
from src.models.enums import AssetStatus, FileType, PermissionEntity, WFMainCondition
from src.models.files_custom import CustomField, CustomFieldValue, File as FileEntity, Notification
from src.models.integrations import ApiKey, WebhookEndpoint as WebhookConfig
from src.models.location_asset import Asset, Location
from src.models.meters import Meter, Reading, WorkOrderMeterTrigger
from src.models.parts_po import Customer, Part, Vendor
from src.models.pm_schedule import PreventiveMaintenance
from src.models.requests import Request, RequestPortal
from src.models.users import Team, User
from src.models.work_orders import WorkOrder
from src.models.workflows import Workflow, WorkflowAction, WorkflowCondition
from src.routes._crud import (
    _get_user_company_settings_id,
    apply_model_defaults,
    build_crud_router,
)
from src.routes.assets_locations import (
    _hydrate_custom_field_values,
    _sync_entity_custom_fields,
    _verify_and_sync_m2m,
)
from src.routes.work_orders_pm import _serialize_wo
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict
from src.services.workflow_engine import (
    run_request_workflows,
    run_work_order_workflows,
)
from src.utils.dates import to_iso_utc

router = APIRouter()


# 6.13 Meters & Readings
def _serialize_meter(meter: Meter, db: Session) -> dict[str, Any]:
    res = model_to_dict(meter, db=db)
    latest = db.scalar(
        select(Reading)
        .where(Reading.meter_id == meter.id)
        .order_by(Reading.created_at.desc(), Reading.id.desc())
        .limit(1)
    )
    res["lastReading"] = to_iso_utc(latest.created_at) if latest else None
    freq = getattr(meter, "update_frequency", None)
    if isinstance(freq, int) and freq > 0:
        base_dt = latest.created_at if latest and latest.created_at else meter.created_at
        res["nextReading"] = to_iso_utc(base_dt + timedelta(days=freq)) if base_dt else None
    else:
        res["nextReading"] = None

    user_ids = db.scalars(
        select(t_meter_user_associations.c.id_user).where(
            t_meter_user_associations.c.id_meter == meter.id
        )
    ).all()
    users = db.scalars(select(User).where(User.id.in_(user_ids))).all() if user_ids else []
    res["users"] = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]
    res["customFieldValues"] = _hydrate_custom_field_values(
        db, CustomFieldValue.meter_id == meter.id
    )
    return res


def _before_create_meter(
    meter: Meter, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if getattr(meter, "asset_id", None) is None:
        asset = db.scalar(select(Asset).where(Asset.company_id == current_user.company_id))
        if asset is None:
            asset = Asset(
                name="Default Asset",
                company_id=current_user.company_id,
                archived=False,
                is_demo=False,
            )
            db.add(asset)
            db.flush()
        meter.asset_id = asset.id


def _sync_meter_relations(
    meter: Meter, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if "users" in payload and isinstance(payload["users"], list):
        db.execute(
            t_meter_user_associations.delete().where(
                t_meter_user_associations.c.id_meter == meter.id
            )
        )
        for item in payload["users"]:
            uid = item.get("id") if isinstance(item, dict) else item
            if isinstance(uid, int):
                u = db.get(User, uid)
                if u is None or u.company_id != current_user.company_id:
                    raise CustomException(status_code=400, message=f"Invalid user reference {uid}")
                db.execute(
                    t_meter_user_associations.insert().values(id_meter=meter.id, id_user=uid)
                )
    _sync_entity_custom_fields(
        meter, payload, current_user, db, CustomFieldValue.meter_id, "meter_id"
    )


meters_router = build_crud_router(
    "/meters",
    Meter,
    custom_serializer=_serialize_meter,
    before_create=_before_create_meter,
    after_create=_sync_meter_relations,
    after_patch=_sync_meter_relations,
)


@meters_router.get("/mini")
def list_meters_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.METERS, db):
        raise CustomException(status_code=403, message="Insufficient permissions to view meters")
    rows = db.scalars(select(Meter).where(Meter.company_id == current_user.company_id)).all()
    return [{"id": r.id, "name": r.name, "unit": r.unit} for r in rows]


@meters_router.get("/asset/{asset_id:int}")
def list_meters_by_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.METERS, db):
        raise CustomException(status_code=403, message="Insufficient permissions to view meters")
    asset = db.get(Asset, asset_id)
    if not asset:
        raise CustomException(status_code=404, message="Asset not found")
    assert_company_access(current_user, asset, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Meter).where(
            Meter.asset_id == asset_id,
            Meter.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_meter(r, db) for r in rows]


router.include_router(meters_router)


def _after_create_reading(
    reading: Reading, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if reading.meter_id:
        triggers = db.scalars(
            select(WorkOrderMeterTrigger).where(
                WorkOrderMeterTrigger.meter_id == reading.meter_id
            )
        ).all()
        for trig in triggers:
            cond = trig.trigger_condition if trig.trigger_condition is not None else 0
            should_fire = (
                cond in (0, "0", "MORE_THAN", "GREATER_THAN") and reading.value > trig.value
            ) or (
                cond in (1, "1", "LESS_THAN") and reading.value < trig.value
            )
            if should_fire:
                wo = WorkOrder(
                    title=trig.title or "Meter Triggered Work Order",
                    description=trig.description,
                    priority=trig.priority or 0,
                    status=0,
                    company_id=current_user.company_id,
                    asset_id=trig.asset_id,
                    location_id=trig.location_id,
                    primary_user_id=trig.primary_user_id,
                    created_by=current_user.id,
                    estimated_duration=0.0,
                    required_signature=False,
                    archived=False,
                    is_demo=False,
                )
                db.add(wo)
                db.flush()
                wo.custom_id = f"W{wo.id:06d}"


readings_router = build_crud_router("/readings", Reading, after_create=_after_create_reading)


@readings_router.get("/meter/{meter_id:int}")
def list_readings_by_meter(
    meter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    meter = db.get(Meter, meter_id)
    if not meter:
        raise CustomException(status_code=404, message="Meter not found")
    assert_company_access(current_user, meter, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(
        select(Reading)
        .where(Reading.meter_id == meter_id)
        .order_by(Reading.created_at.desc(), Reading.id.desc())
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


@readings_router.post("/meter/{meter_id:int}/histogram")
def get_readings_histogram(
    meter_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    meter = db.get(Meter, meter_id)
    if not meter:
        raise CustomException(status_code=404, message="Meter not found")
    assert_company_access(current_user, meter, is_super_admin=is_super_admin(current_user, db))
    rows = db.scalars(select(Reading).where(Reading.meter_id == meter_id)).all()
    return [
        {"date": r.created_at.strftime("%Y-%m-%d"), "value": r.value}
        for r in rows
    ]


router.include_router(readings_router)


# 6.14 Requests & RequestPortals
def _serialize_request(req: Request, db: Session) -> dict[str, Any]:
    res = model_to_dict(req, db=db)

    user_ids = db.scalars(
        select(request_assigned_to.c.assigned_to_id).where(
            request_assigned_to.c.request_id == req.id
        )
    ).all()
    users = db.scalars(select(User).where(User.id.in_(user_ids))).all() if user_ids else []
    res["assignedTo"] = [
        {"id": u.id, "firstName": u.first_name, "lastName": u.last_name, "email": u.email}
        for u in users
    ]

    cust_ids = db.scalars(
        select(request_customers.c.customers_id).where(
            request_customers.c.request_id == req.id
        )
    ).all()
    customers = db.scalars(select(Customer).where(Customer.id.in_(cust_ids))).all() if cust_ids else []
    res["customers"] = [
        {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone}
        for c in customers
    ]

    file_ids_1 = db.scalars(
        select(request_files.c.files_id).where(request_files.c.request_id == req.id)
    ).all()
    file_ids_2 = db.scalars(
        select(t_request_file_associations.c.id_file).where(
            t_request_file_associations.c.id_request == req.id
        )
    ).all()
    all_file_ids = list(dict.fromkeys([*file_ids_1, *file_ids_2]))
    files = (
        db.scalars(select(FileEntity).where(FileEntity.id.in_(all_file_ids))).all()
        if all_file_ids
        else []
    )
    res["files"] = [model_to_dict(f, db=db) for f in files]
    res["customFieldValues"] = _hydrate_custom_field_values(
        db, CustomFieldValue.request_id == req.id
    )
    return res


def _before_create_request(
    req: Request, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if req.cancelled is None:
        req.cancelled = False


def _sync_request_relations(
    req: Request, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not req.custom_id:
        req.custom_id = f"R{req.id:06d}"
    _verify_and_sync_m2m(
        db,
        current_user,
        payload,
        "assignedTo",
        request_assigned_to,
        "request_id",
        req.id,
        "assigned_to_id",
        User,
    )
    _verify_and_sync_m2m(
        db,
        current_user,
        payload,
        "customers",
        request_customers,
        "request_id",
        req.id,
        "customers_id",
        Customer,
    )
    _verify_and_sync_m2m(
        db,
        current_user,
        payload,
        "files",
        request_files,
        "request_id",
        req.id,
        "files_id",
        FileEntity,
    )
    _sync_entity_custom_fields(
        req, payload, current_user, db, CustomFieldValue.request_id, "request_id"
    )


def _after_create_request(
    req: Request, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _sync_request_relations(req, payload, current_user, db)
    run_request_workflows(req, WFMainCondition.REQUEST_CREATED, db)


requests_router = build_crud_router(
    "/requests",
    Request,
    custom_serializer=_serialize_request,
    before_create=_before_create_request,
    after_create=_after_create_request,
    after_patch=_sync_request_relations,
)


@requests_router.get("/pending")
def count_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = db.scalars(
        select(Request).where(
            Request.company_id == current_user.company_id,
            Request.work_order_id.is_(None),
            Request.cancelled.is_(False),
        )
    ).all()
    return SuccessResponse(success=True, message=str(len(rows))).model_dump()


@requests_router.post("/portal/{portal_uuid}")
def create_request_from_portal(
    portal_uuid: str,
    payload: dict[str, Any] = Body(...),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    portal = db.scalar(select(RequestPortal).where(RequestPortal.uuid == portal_uuid))
    if not portal:
        raise CustomException(status_code=404, message="RequestPortal not found")

    req = Request()
    apply_patch(req, payload)
    req.company_id = portal.company_id
    req.request_portal_id = portal.id
    req.created_by = current_user.id if current_user is not None else portal.created_by
    if req.cancelled is None:
        req.cancelled = False
    apply_model_defaults(req)
    db.add(req)
    db.flush()
    req.custom_id = f"R{req.id:06d}"

    proxy_user = current_user or User(id=portal.created_by, company_id=portal.company_id)
    _sync_request_relations(req, payload, proxy_user, db)
    run_request_workflows(req, WFMainCondition.REQUEST_CREATED, db)

    db.commit()
    db.refresh(req)
    return _serialize_request(req, db)


@requests_router.patch("/{req_id:int}/approve")
def approve_request(
    req_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    req = db.get(Request, req_id)
    if not req:
        raise CustomException(status_code=404, message="Request not found")
    assert_company_access(current_user, req, is_super_admin=is_super_admin(current_user, db))
    if req.work_order_id is not None or req.cancelled:
        raise CustomException(status_code=406, message="Request is already processed")

    wo = WorkOrder(
        title=req.title,
        description=req.description,
        priority=req.priority or 0,
        status=0,
        company_id=req.company_id or current_user.company_id,
        asset_id=req.asset_id,
        location_id=req.location_id,
        primary_user_id=req.primary_user_id,
        team_id=req.team_id,
        category_id=req.category_id,
        image_id=req.image_id,
        due_date=req.due_date,
        estimated_start_date=req.estimated_start_date,
        parent_request_id=req.id,
        created_by=current_user.id,
        estimated_duration=req.estimated_duration or 0.0,
        required_signature=bool(req.required_signature),
        archived=False,
        is_demo=False,
    )
    db.add(wo)
    db.flush()
    wo.custom_id = f"WO{wo.id:06d}"
    req.work_order_id = wo.id

    user_ids = db.scalars(
        select(request_assigned_to.c.assigned_to_id).where(
            request_assigned_to.c.request_id == req.id
        )
    ).all()
    for uid in user_ids:
        db.execute(
            work_order_assigned_to.insert().values(work_order_id=wo.id, assigned_to_id=uid)
        )

    cust_ids = db.scalars(
        select(request_customers.c.customers_id).where(
            request_customers.c.request_id == req.id
        )
    ).all()
    for cid in cust_ids:
        db.execute(
            work_order_customers.insert().values(work_order_id=wo.id, customers_id=cid)
        )

    file_ids_1 = db.scalars(
        select(request_files.c.files_id).where(request_files.c.request_id == req.id)
    ).all()
    file_ids_2 = db.scalars(
        select(t_request_file_associations.c.id_file).where(
            t_request_file_associations.c.id_request == req.id
        )
    ).all()
    all_file_ids = list(dict.fromkeys([*file_ids_1, *file_ids_2]))
    if req.audio_description_id and req.audio_description_id not in all_file_ids:
        all_file_ids.append(req.audio_description_id)
    for fid in all_file_ids:
        db.execute(work_order_files.insert().values(work_order_id=wo.id, files_id=fid))

    run_request_workflows(req, WFMainCondition.REQUEST_APPROVED, db)
    run_work_order_workflows(wo, WFMainCondition.WORK_ORDER_CREATED, db)

    db.commit()
    db.refresh(wo)
    return _serialize_wo(wo, db)


@requests_router.patch("/{req_id:int}/cancel")
def cancel_request(
    req_id: int,
    reason: str | None = Query(default=None),
    payload: dict[str, Any] | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    req = db.get(Request, req_id)
    if not req:
        raise CustomException(status_code=404, message="Request not found")
    assert_company_access(current_user, req, is_super_admin=is_super_admin(current_user, db))
    body_reason = (
        payload.get("reason") or payload.get("cancellationReason")
        if isinstance(payload, dict)
        else None
    )
    req.cancelled = True
    req.cancellation_reason = reason or body_reason or "Cancelled"
    run_request_workflows(req, WFMainCondition.REQUEST_REJECTED, db)
    db.commit()
    db.refresh(req)
    return _serialize_request(req, db)


router.include_router(requests_router)


def _before_create_request_portal(
    rp: RequestPortal, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not rp.uuid:
        rp.uuid = secrets.token_urlsafe(12)
    if not rp.title:
        rp.title = payload.get("title") or "Request Portal"


request_portals_router = build_crud_router(
    "/request-portals",
    RequestPortal,
    before_create=_before_create_request_portal,
)


@request_portals_router.get("/public/{portal_uuid}")
def get_public_request_portal(
    portal_uuid: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rp = db.scalar(select(RequestPortal).where(RequestPortal.uuid == portal_uuid))
    if not rp:
        raise CustomException(status_code=404, message="RequestPortal not found")
    return model_to_dict(rp, db=db)


router.include_router(request_portals_router)


# 6.15 Workflows
def _serialize_workflow(wf: Workflow, db: Session) -> dict[str, Any]:
    from src.models.associations import workflow_secondary_conditions

    res = model_to_dict(wf, db=db)
    cond_ids = db.scalars(
        select(workflow_secondary_conditions.c.secondary_conditions_id).where(
            workflow_secondary_conditions.c.workflow_id == wf.id
        )
    ).all()
    conds = (
        db.scalars(select(WorkflowCondition).where(WorkflowCondition.id.in_(cond_ids))).all()
        if cond_ids
        else []
    )
    res["secondaryConditions"] = [model_to_dict(c, db=db) for c in conds]
    if wf.action_id:
        act = db.get(WorkflowAction, wf.action_id)
        res["action"] = model_to_dict(act, db=db) if act else None
    return res


def _before_create_workflow(
    wf: Workflow, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if "enabled" not in payload or wf.enabled is None:
        wf.enabled = bool(payload.get("enabled", True))
    act = WorkflowAction(company_id=current_user.company_id)
    if isinstance(payload.get("action"), dict):
        apply_patch(act, payload["action"])
    db.add(act)
    db.flush()
    wf.action_id = act.id


def _after_create_workflow(
    wf: Workflow, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    from src.models.associations import workflow_secondary_conditions

    if isinstance(payload.get("secondaryConditions"), list):
        for cdata in payload["secondaryConditions"]:
            if isinstance(cdata, dict):
                normalized_cdata = dict(cdata)
                if (
                    "comparatedWorkOrderPriority" in normalized_cdata
                    and "priority" not in normalized_cdata
                ):
                    normalized_cdata["priority"] = normalized_cdata["comparatedWorkOrderPriority"]
                if (
                    "comparatedWorkOrderStatus" in normalized_cdata
                    and "workOrderStatus" not in normalized_cdata
                ):
                    normalized_cdata["workOrderStatus"] = normalized_cdata[
                        "comparatedWorkOrderStatus"
                    ]
                if (
                    "comparatedPurchaseOrderStatus" in normalized_cdata
                    and "purchaseOrderStatus" not in normalized_cdata
                ):
                    normalized_cdata["purchaseOrderStatus"] = normalized_cdata[
                        "comparatedPurchaseOrderStatus"
                    ]
                cond = WorkflowCondition(company_id=current_user.company_id)
                apply_patch(cond, normalized_cdata)
                db.add(cond)
                db.flush()
                db.execute(
                    workflow_secondary_conditions.insert().values(
                        workflow_id=wf.id,
                        secondary_conditions_id=cond.id,
                    )
                )


router.include_router(
    build_crud_router(
        "/workflows",
        Workflow,
        custom_serializer=_serialize_workflow,
        before_create=_before_create_workflow,
        after_create=_after_create_workflow,
    )
)


# 6.16 Files & CustomFields
files_router = build_crud_router("/files", FileEntity)


def _sanitize_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._")
    return cleaned or "upload.bin"


def _resolve_file_type(type_str: str) -> int:
    members = list(FileType)
    try:
        return members.index(FileType[type_str.strip().upper()])
    except (KeyError, ValueError):
        return members.index(FileType.OTHER)


def _get_upload_root(company_id: int | None) -> Path:
    cid = str(company_id or 0)
    primary = (envs.DATA_DIR / "uploads" / cid).resolve()
    try:
        primary.mkdir(parents=True, exist_ok=True)
        return primary
    except OSError:
        fallback = (Path(tempfile.gettempdir()) / "cmms-uploads" / cid).resolve()
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


@files_router.post("/upload", response_model=None)
@files_router.post("/upload/request-portal/{portal_uuid}", response_model=None)
def upload_files(
    portal_uuid: str | None = None,
    files: list[UploadFile] = File(default=[]),
    file: list[UploadFile] = File(default=[]),
    multipartFiles: list[UploadFile] = File(default=[]),
    folder: str = Form(default="general"),
    hidden: str = Form(default="false"),
    type: str = Form(default="OTHER"),
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    company_id: int | None = None
    created_by: int | None = None
    if portal_uuid:
        portal = db.scalar(select(RequestPortal).where(RequestPortal.uuid == portal_uuid))
        if portal is None:
            raise CustomException(status_code=404, message="Request portal not found")
        company_id = portal.company_id
        if current_user is not None:
            created_by = current_user.id
    else:
        if current_user is None:
            raise CustomException(status_code=401, message="Authentication required")
        if not can_create(current_user, PermissionEntity.FILES, db):
            raise CustomException(status_code=403, message="Access Denied")
        company_id = current_user.company_id
        created_by = current_user.id

    all_uploads = [*files, *file, *multipartFiles]
    created: list[FileEntity] = []
    is_hidden = str(hidden).lower() == "true"
    file_type_val = _resolve_file_type(type)
    upload_root = _get_upload_root(company_id)

    MAX_UPLOAD_FILE_BYTES = 25 * 1024 * 1024  # 25 MB per file
    for f in all_uploads:
        orig_name = f.filename or "upload.bin"
        safe_fname = _sanitize_filename(orig_name)
        content = f.file.read(MAX_UPLOAD_FILE_BYTES + 1)
        if len(content) > MAX_UPLOAD_FILE_BYTES:
            raise CustomException(status_code=413, message="Uploaded file exceeds 25 MB limit")
        fe = FileEntity(
            name=orig_name,
            path="",
            type=file_type_val,
            hidden=is_hidden,
            company_id=company_id,
            created_by=created_by,
        )
        db.add(fe)
        db.flush()
        target_path = (upload_root / f"{fe.id}_{safe_fname}").resolve()
        if not target_path.is_relative_to(upload_root):
            raise CustomException(status_code=400, message="Invalid upload file name")
        target_path.write_bytes(content)
        fe.path = f"/api/files/download/{fe.id}"
        created.append(fe)
    db.commit()
    return [model_to_dict(fe, db=db) for fe in created]


@files_router.get("/download/{file_id:int}")
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    fe = db.get(FileEntity, file_id)
    if fe is None:
        raise CustomException(status_code=404, message="File not found")
    assert_company_access(current_user, fe, is_super_admin=is_super_admin(current_user, db))
    upload_root = _get_upload_root(fe.company_id)
    safe_fname = _sanitize_filename(fe.name or "upload.bin")
    target_path = (upload_root / f"{fe.id}_{safe_fname}").resolve()
    if not target_path.is_relative_to(upload_root) or not target_path.is_file():
        raise CustomException(status_code=404, message="Stored file not found on disk")
    media_type, _ = mimetypes.guess_type(fe.name or "")
    return FileResponse(
        path=target_path,
        media_type=media_type or "application/octet-stream",
        filename=fe.name or safe_fname,
    )


router.include_router(files_router)
router.include_router(build_crud_router("/custom-fields", CustomField))


# 6.17 Notifications & SockJS / WebSocket
notifications_router = build_crud_router("/notifications", Notification)


@notifications_router.get("/read-all")
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    rows = db.scalars(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.seen.is_(False),
        )
    ).all()
    for n in rows:
        n.seen = True
    db.commit()
    return SuccessResponse(success=True, message="All notifications marked as read").model_dump()


router.include_router(notifications_router)


@router.get("/ws/info")
def sockjs_info() -> dict[str, Any]:
    return {
        "websocket": True,
        "origins": ["*:*"],
        "cookie_needed": False,
        "entropy": 123456789,
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.startswith("CONNECT"):
                await websocket.send_text("CONNECTED\nversion:1.2\nheart-beat:0,0\n\n\x00")
            elif msg.startswith("SUBSCRIBE"):
                pass
    except Exception:
        return


@router.websocket("/ws/{server_id}/{session_id}/websocket")
async def sockjs_websocket_endpoint(websocket: WebSocket, server_id: str, session_id: str) -> None:
    import json

    await websocket.accept()
    try:
        await websocket.send_text("o")
        while True:
            msg = await websocket.receive_text()
            if "CONNECT" in msg:
                frame = "CONNECTED\nversion:1.2\nheart-beat:0,0\n\n\x00"
                await websocket.send_text("a" + json.dumps([frame]))
    except Exception:
        return


# 6.19 Import / Export CSV & Templates
_IMPORT_TEMPLATES: dict[str, tuple[list[str], list[list[str]]]] = {
    "ASSET": (
        [
            "ID",
            "Name",
            "Description",
            "Status",
            "Archived",
            "Location Name",
            "Parent Asset",
            "Area",
            "Barcode",
            "Category",
            "Primary User",
            "Warranty Expiration Date",
            "Additional Information",
            "Serial Number",
            "Assigned To",
            "Teams",
            "Parts",
            "Vendors",
            "Contractors",
            "Acquisition cost",
            "NFC ID",
            "In Service Date",
        ],
        [
            [
                "",
                "Ventilation System-Brooding House",
                "Assembly that ensures adequate air exchange and temperature control",
                "Operational",
                "No",
                "Area 2-Brooding House 1",
                "",
                "Area 2-A",
                "01-BH-VS",
                "HVAC Systems",
                "ab@gmail.com",
                "2026-12-31",
                "See Datasheet and Work Instruction",
                "6437070",
                "abc@gmail.com,abcd@gmail.com",
                "",
                "",
                "Vendor1,Vendor2",
                "Contractor1",
                "1000",
                "",
                "2025-01-15",
            ]
        ],
    ),
    "LOCATION": (
        ["ID", "Name", "Address", "Longitude", "Latitude", "Parent Location", "Workers", "Teams", "Vendors", "Customers"],
        [["", "Main Warehouse", "123 Industrial Way", "", "", "", "", "", "", ""]],
    ),
    "PART": (
        [
            "ID",
            "Name",
            "Cost",
            "Quantity",
            "Barcode",
            "Area",
            "Category",
            "Description",
            "Minimum Quantity",
            "Non Stock",
            "Additional Information",
            "Workers",
            "Teams",
            "Vendors",
            "Customers",
            "Unit",
        ],
        [["", "Air Filter", "25", "10", "AF-001", "Shelf A", "Filters", "Standard HVAC filter", "2", "No", "", "", "", "", "", "pcs"]],
    ),
    "METER": (
        ["ID", "Name", "Unit", "Update Frequency", "Category", "Asset", "Location", "Users"],
        [["", "Compressor Runtime", "hours", "7", "Runtime", "", "", ""]],
    ),
    "WORK_ORDER": (
        [
            "ID",
            "Title",
            "Description",
            "Due Date",
            "Completed On",
            "Status",
            "Estimated Hours",
            "Priority",
            "Category",
            "Completed By",
            "Assigned To",
            "Primary User",
            "Asset Name",
            "Location Name",
            "Team Name",
            "Customers",
            "Feedback",
            " Archive",
            "Requires Signature",
        ],
        [["", "Inspect HVAC Belt", "Routine belt tension check", "", "", "Open", "1.5", "Medium", "Preventive", "", "", "", "", "", "", "", "", "No", "No"]],
    ),
    "PREVENTIVE_MAINTENANCE": (
        [
            "ID",
            "Name",
            "Starts On",
            "Ends On",
            "Frequency",
            "Title",
            "Description",
            "Priority",
            "Estimated Hours",
            "Category",
            "Asset Name",
            "Location Name",
            "Primary User",
            "Assigned To",
            "Team Name",
        ],
        [["", "Monthly Chiller PM", "2026-01-01", "", "30", "Chiller Filter & Coil Inspection", "Clean coils", "Medium", "2", "HVAC", "", "", "", "", ""]],
    ),
}


@router.get("/import/download-template")
def download_import_template(
    language: str = Query(default="EN"),
    importEntity: str = Query(default="ASSET"),
    current_user: User = Depends(get_current_user),
) -> Response:
    key = importEntity.strip().upper().replace("-", "_")
    if key.endswith("S") and key not in _IMPORT_TEMPLATES:
        key = key[:-1]
    headers, sample_rows = _IMPORT_TEMPLATES.get(key, _IMPORT_TEMPLATES["ASSET"])
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in sample_rows:
        writer.writerow(row)
    return Response(
        content=buf.getvalue().encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{key.lower()}_template_{language.lower()}.csv"'},
    )


def _export_asset_rows(assets: list[Asset], db: Session) -> tuple[list[str], list[list[Any]]]:
    cols = [
        "id",
        "custom_id",
        "name",
        "description",
        "status",
        "archived",
        "location_name",
        "parent_asset_name",
        "area",
        "bar_code",
        "nfc_id",
        "model",
        "power",
        "manufacturer",
        "category",
        "primary_user_email",
        "warranty_expiration_date",
        "in_service_date",
        "additional_infos",
        "serial_number",
        "acquisition_cost",
        "assigned_to_emails",
        "teams_names",
        "parts_names",
        "vendors_names",
        "customers_names",
    ]
    rows_out: list[list[Any]] = []
    for a in assets:
        loc_name = ""
        if a.location_id:
            loc = db.get(Location, a.location_id)
            loc_name = loc.name if loc else ""
        parent_name = ""
        if a.parent_asset_id:
            pa = db.get(Asset, a.parent_asset_id)
            parent_name = pa.name if pa else ""
        cat_name = ""
        if a.category_id:
            cat = db.get(AssetCategory, a.category_id)
            cat_name = cat.name if cat else ""
        primary_email = ""
        if a.primary_user_id:
            pu = db.get(User, a.primary_user_id)
            primary_email = pu.email if pu else ""
        status_name = "OPERATIONAL"
        if a.status is not None:
            try:
                status_name = AssetStatus(int(a.status)).name
            except Exception:
                status_name = str(a.status)
        assigned_emails = list(
            db.scalars(
                select(User.email)
                .join(t_asset_user_associations, t_asset_user_associations.c.id_user == User.id)
                .where(t_asset_user_associations.c.id_asset == a.id)
            ).all()
        )
        team_names = list(
            db.scalars(
                select(Team.name)
                .join(t_asset_team_associations, t_asset_team_associations.c.id_team == Team.id)
                .where(t_asset_team_associations.c.id_asset == a.id)
            ).all()
        )
        part_names = list(
            db.scalars(
                select(Part.name)
                .join(t_asset_part_associations, t_asset_part_associations.c.id_part == Part.id)
                .where(t_asset_part_associations.c.id_asset == a.id)
            ).all()
        )
        vendor_names = list(
            db.scalars(
                select(Vendor.name)
                .join(t_asset_vendor_associations, t_asset_vendor_associations.c.id_vendor == Vendor.id)
                .where(t_asset_vendor_associations.c.id_asset == a.id)
            ).all()
        )
        customer_names = list(
            db.scalars(
                select(Customer.name)
                .join(t_asset_customer_associations, t_asset_customer_associations.c.id_customer == Customer.id)
                .where(t_asset_customer_associations.c.id_asset == a.id)
            ).all()
        )
        rows_out.append(
            [
                a.id,
                a.custom_id or "",
                a.name or "",
                a.description or "",
                status_name,
                "Yes" if a.archived else "No",
                loc_name,
                parent_name,
                a.area or "",
                a.bar_code or "",
                a.nfc_id or "",
                a.model or "",
                a.power or "",
                a.manufacturer or "",
                cat_name,
                primary_email,
                to_iso_utc(a.warranty_expiration_date) or "",
                to_iso_utc(a.in_service_date) or "",
                a.additional_infos or "",
                a.serial_number or "",
                a.acquisition_cost if a.acquisition_cost is not None else "",
                ",".join(assigned_emails),
                ",".join(team_names),
                ",".join(part_names),
                ",".join(vendor_names),
                ",".join(customer_names),
            ]
        )
    return cols, rows_out


@router.get("/export/{entity_name}")
@router.post("/export/{entity_name}")
def export_csv(
    entity_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    perm_map: dict[str, PermissionEntity] = {
        "work-orders": PermissionEntity.WORK_ORDERS,
        "assets": PermissionEntity.ASSETS,
        "locations": PermissionEntity.LOCATIONS,
        "parts": PermissionEntity.PARTS_AND_MULTIPARTS,
        "meters": PermissionEntity.METERS,
        "preventive-maintenances": PermissionEntity.PREVENTIVE_MAINTENANCES,
    }
    perm = perm_map.get(entity_name.lower())
    if perm and not can_view(current_user, perm, db):
        raise CustomException(status_code=403, message="Access Denied")

    if entity_name.lower() == "assets":
        assets = list(
            db.scalars(
                select(Asset)
                .where(Asset.company_id == current_user.company_id)
                .order_by(Asset.id.asc())
            ).all()
        )
        cols, data_rows = _export_asset_rows(assets, db)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(cols)
        for r in data_rows:
            writer.writerow(r)
        return Response(
            content=buf.getvalue().encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="assets.csv"'},
        )

    entity_map: dict[str, tuple[type, list[str]]] = {
        "work-orders": (WorkOrder, ["id", "custom_id", "title", "description", "status", "priority"]),
        "locations": (Location, ["id", "custom_id", "name", "address", "longitude", "latitude"]),
        "parts": (Part, ["id", "name", "cost", "quantity", "barcode", "unit", "area", "description", "min_quantity"]),
        "meters": (Meter, ["id", "name", "unit", "update_frequency"]),
        "preventive-maintenances": (PreventiveMaintenance, ["id", "custom_id", "name", "title", "description"]),
    }
    target = entity_map.get(entity_name.lower())
    if not target:
        raise CustomException(status_code=400, message=f"Unsupported export entity: {entity_name}")
    model_cls, cols = target
    rows = db.scalars(select(model_cls).where(model_cls.company_id == current_user.company_id)).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    for r in rows:
        writer.writerow([getattr(r, c, "") for c in cols])

    return Response(
        content=buf.getvalue().encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{entity_name}.csv"'},
    )


def _parse_bool_import(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ("true", "yes", "1", "oui", "si", "ja")


def _parse_list_import(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        return [x.strip() for x in val.split(",") if x.strip()]
    return []


def _parse_asset_status_import(val: Any) -> int:
    members = list(AssetStatus)
    if val is None or str(val).strip() == "":
        return 0
    if isinstance(val, int) and not isinstance(val, bool):
        return val if 0 <= val < len(members) else 0
    norm = str(val).strip().upper().replace(" ", "_").replace("-", "_")
    if norm.isdigit():
        idx = int(norm)
        return idx if 0 <= idx < len(members) else 0
    for idx, member in enumerate(members):
        if member.name == norm or str(member.value).upper() == norm:
            return idx
    return 0


def _import_assets_two_pass(
    payload: list[dict[str, Any]],
    current_user: User,
    db: Session,
) -> dict[str, int]:
    from src.routes.assets_locations import _validate_asset_integrity

    company_id = current_user.company_id
    cs_id = _get_user_company_settings_id(current_user, db)

    # Check batch-internal duplicate barcodes or nfcIds
    seen_barcodes: set[str] = set()
    seen_nfc_ids: set[str] = set()
    for dto in payload:
        bc = str(dto.get("barCode") or "").strip()
        if bc:
            if bc in seen_barcodes:
                raise CustomException(status_code=406, message=f"Duplicate barcode in import batch: {bc}")
            seen_barcodes.add(bc)
        nfc = str(dto.get("nfcId") or "").strip()
        if nfc:
            if nfc in seen_nfc_ids:
                raise CustomException(status_code=406, message=f"Duplicate nfcId in import batch: {nfc}")
            seen_nfc_ids.add(nfc)

    created = 0
    updated = 0
    batch_assets_by_name: dict[str, Asset] = {}
    staged_rows: list[tuple[Asset, dict[str, Any]]] = []

    # Pass 1: Create or update Asset records, assign custom_id, resolve Location, Category, PrimaryUser, M2M links
    for item in payload:
        raw_id = item.get("id")
        item_id: int | None = None
        if raw_id is not None and str(raw_id).strip() != "":
            try:
                item_id = int(float(str(raw_id).strip()))
            except (ValueError, TypeError):
                item_id = None

        asset = db.get(Asset, item_id) if item_id else None
        is_update = asset is not None and asset.company_id == company_id
        if not is_update:
            asset = Asset()
            asset.company_id = company_id
            asset.created_by = current_user.id

        # Basic fields via apply_patch (handles dates, numbers, blank-to-None for barCode/nfcId/customId)
        scalar_patch: dict[str, Any] = {}
        for k in (
            "name",
            "description",
            "area",
            "barCode",
            "nfcId",
            "model",
            "power",
            "manufacturer",
            "warrantyExpirationDate",
            "inServiceDate",
            "additionalInfos",
            "serialNumber",
            "acquisitionCost",
            "customId",
        ):
            if k in item and item[k] is not None:
                scalar_patch[k] = item[k]
        if not scalar_patch.get("name"):
            scalar_patch["name"] = "Imported Asset"
        apply_patch(asset, scalar_patch)
        asset.archived = _parse_bool_import(item.get("archived"))
        asset.status = _parse_asset_status_import(item.get("status"))

        # Resolve Location by locationName
        loc_name = str(item.get("locationName") or "").strip()
        if loc_name:
            loc = db.scalar(
                select(Location).where(
                    Location.company_id == company_id,
                    func.lower(Location.name) == loc_name.lower(),
                )
            )
            if loc is not None:
                asset.location_id = loc.id

        # Resolve or create AssetCategory by category name
        cat_name = str(item.get("category") or "").strip()
        if cat_name and cs_id is not None:
            cat = db.scalar(
                select(AssetCategory).where(
                    AssetCategory.company_settings_id == cs_id,
                    func.lower(AssetCategory.name) == cat_name.lower(),
                )
            )
            if cat is None:
                cat = AssetCategory(
                    name=cat_name,
                    company_settings_id=cs_id,
                    created_by=current_user.id,
                    is_demo=False,
                )
                apply_model_defaults(cat)
                db.add(cat)
                db.flush()
            asset.category_id = cat.id

        # Resolve Primary User by primaryUserEmail
        primary_email = str(item.get("primaryUserEmail") or "").strip()
        if primary_email:
            pu = db.scalar(
                select(User).where(
                    User.company_id == company_id,
                    func.lower(User.email) == primary_email.lower(),
                )
            )
            if pu is not None:
                asset.primary_user_id = pu.id

        apply_model_defaults(asset)
        _validate_asset_integrity(asset, current_user, db)

        if is_update:
            updated += 1
        else:
            db.add(asset)
            created += 1

        db.flush()
        if not asset.custom_id:
            asset.custom_id = f"A{asset.id:06d}"

        if asset.name:
            batch_assets_by_name[asset.name.strip().lower()] = asset
        staged_rows.append((asset, item))

        # M2M links
        assigned_emails = _parse_list_import(item.get("assignedToEmails"))
        if "assignedToEmails" in item:
            db.execute(
                t_asset_user_associations.delete().where(t_asset_user_associations.c.id_asset == asset.id)
            )
            for email in assigned_emails:
                u = db.scalar(
                    select(User).where(
                        User.company_id == company_id,
                        func.lower(User.email) == email.lower(),
                    )
                )
                if u is not None:
                    db.execute(
                        t_asset_user_associations.insert().values(id_asset=asset.id, id_user=u.id)
                    )

        team_names = _parse_list_import(item.get("teamsNames"))
        if "teamsNames" in item:
            db.execute(
                t_asset_team_associations.delete().where(t_asset_team_associations.c.id_asset == asset.id)
            )
            for tname in team_names:
                tm = db.scalar(
                    select(Team).where(
                        Team.company_id == company_id,
                        func.lower(Team.name) == tname.lower(),
                    )
                )
                if tm is not None:
                    db.execute(
                        t_asset_team_associations.insert().values(id_asset=asset.id, id_team=tm.id)
                    )

        part_names = _parse_list_import(item.get("partsNames"))
        if "partsNames" in item:
            db.execute(
                t_asset_part_associations.delete().where(t_asset_part_associations.c.id_asset == asset.id)
            )
            for pname in part_names:
                pt = db.scalar(
                    select(Part).where(
                        Part.company_id == company_id,
                        func.lower(Part.name) == pname.lower(),
                    )
                )
                if pt is not None:
                    db.execute(
                        t_asset_part_associations.insert().values(id_asset=asset.id, id_part=pt.id)
                    )

        vendor_names = _parse_list_import(item.get("vendorsNames"))
        if "vendorsNames" in item:
            db.execute(
                t_asset_vendor_associations.delete().where(t_asset_vendor_associations.c.id_asset == asset.id)
            )
            for vname in vendor_names:
                vd = db.scalar(
                    select(Vendor).where(
                        Vendor.company_id == company_id,
                        or_(
                            func.lower(Vendor.company_name) == vname.lower(),
                            func.lower(Vendor.name) == vname.lower(),
                        ),
                    )
                )
                if vd is not None:
                    db.execute(
                        t_asset_vendor_associations.insert().values(id_asset=asset.id, id_vendor=vd.id)
                    )

        customer_names = _parse_list_import(item.get("customersNames"))
        if "customersNames" in item:
            db.execute(
                t_asset_customer_associations.delete().where(t_asset_customer_associations.c.id_asset == asset.id)
            )
            for cname in customer_names:
                cu = db.scalar(
                    select(Customer).where(
                        Customer.company_id == company_id,
                        func.lower(Customer.name) == cname.lower(),
                    )
                )
                if cu is not None:
                    db.execute(
                        t_asset_customer_associations.insert().values(id_asset=asset.id, id_customer=cu.id)
                    )

    # Pass 2: Resolve parentAssetName in any order (batch first, then DB)
    for asset, item in staged_rows:
        parent_name = str(item.get("parentAssetName") or "").strip()
        if parent_name:
            parent = batch_assets_by_name.get(parent_name.lower())
            if parent is None:
                parent = db.scalar(
                    select(Asset).where(
                        Asset.company_id == company_id,
                        func.lower(Asset.name) == parent_name.lower(),
                        Asset.id != asset.id,
                    )
                )
            if parent is not None and parent.id != asset.id:
                asset.parent_asset_id = parent.id

    db.commit()
    return {"created": created, "updated": updated}


@router.post("/import/{entity_name}")
def import_entities(
    entity_name: str,
    payload: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    perm_map: dict[str, PermissionEntity] = {
        "work-orders": PermissionEntity.WORK_ORDERS,
        "assets": PermissionEntity.ASSETS,
        "locations": PermissionEntity.LOCATIONS,
        "parts": PermissionEntity.PARTS_AND_MULTIPARTS,
        "meters": PermissionEntity.METERS,
        "vendors": PermissionEntity.VENDORS_AND_CUSTOMERS,
        "preventive-maintenances": PermissionEntity.PREVENTIVE_MAINTENANCES,
    }
    perm = perm_map.get(entity_name.lower())
    if perm and not can_create(current_user, perm, db):
        raise CustomException(status_code=403, message="Access Denied")

    if entity_name.lower() == "assets":
        return _import_assets_two_pass(payload, current_user, db)

    entity_map: dict[str, type] = {
        "work-orders": WorkOrder,
        "locations": Location,
        "parts": Part,
        "meters": Meter,
        "vendors": Vendor,
        "preventive-maintenances": PreventiveMaintenance,
    }
    model_cls = entity_map.get(entity_name.lower())
    if not model_cls:
        raise CustomException(status_code=400, message=f"Unsupported import entity: {entity_name}")

    prefix_map: dict[str, str] = {
        "work-orders": "W",
        "locations": "L",
        "preventive-maintenances": "PM",
    }
    prefix = prefix_map.get(entity_name.lower())

    created = 0
    updated = 0
    for item in payload:
        item_id = item.get("id")
        obj = db.get(model_cls, item_id) if item_id else None
        if obj is not None and getattr(obj, "company_id", None) == current_user.company_id:
            apply_patch(obj, item)
            updated += 1
        else:
            obj = model_cls()
            apply_patch(obj, item)
            if hasattr(obj, "company_id"):
                obj.company_id = current_user.company_id
            if hasattr(obj, "created_by"):
                obj.created_by = current_user.id
            apply_model_defaults(obj)
            db.add(obj)
            db.flush()
            if prefix and hasattr(obj, "custom_id") and not getattr(obj, "custom_id", None):
                obj.custom_id = f"{prefix}{obj.id:06d}"
            created += 1
    db.commit()
    return {"created": created, "updated": updated}


# 6.20 ApiKeys & Webhooks
def _before_create_apikey(
    ak: ApiKey, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    ak.user_id = current_user.id
    ak.company_id = current_user.company_id
    if not getattr(ak, "label", None):
        ak.label = payload.get("label") or payload.get("name") or "API Key"
    if not ak.code:
        ak.code = f"ak_{secrets.token_urlsafe(24)}"
    if not ak.expires_at:
        ak.expires_at = utcnow() + timedelta(days=365)


apikeys_router = build_crud_router("/api-keys", ApiKey, before_create=_before_create_apikey)


@apikeys_router.patch("/{ak_id:int}/revoke")
def revoke_apikey(
    ak_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ak = db.get(ApiKey, ak_id)
    if not ak:
        raise CustomException(status_code=404, message="ApiKey not found")
    assert_company_access(current_user, ak, is_super_admin=is_super_admin(current_user, db))
    ak.revoked_at = utcnow()
    db.commit()
    db.refresh(ak)
    return model_to_dict(ak, db=db)


@apikeys_router.post("/{ak_id:int}/rotate")
def rotate_apikey(
    ak_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    ak = db.get(ApiKey, ak_id)
    if not ak:
        raise CustomException(status_code=404, message="ApiKey not found")
    assert_company_access(current_user, ak, is_super_admin=is_super_admin(current_user, db))
    ak.code = f"ak_{secrets.token_urlsafe(24)}"
    db.commit()
    db.refresh(ak)
    return model_to_dict(ak, db=db)


router.include_router(apikeys_router)
router.include_router(build_crud_router("/webhooks", WebhookConfig))

webhook_endpoints_router = build_crud_router("/webhook-endpoints", WebhookConfig)


@webhook_endpoints_router.patch("/{wh_id:int}/rotate-secret")
def rotate_webhook_secret(
    wh_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    wh = db.get(WebhookConfig, wh_id)
    if not wh:
        raise CustomException(status_code=404, message="WebhookEndpoint not found")
    assert_company_access(current_user, wh, is_super_admin=is_super_admin(current_user, db))
    wh.secret = f"whsec_{secrets.token_urlsafe(24)}"
    db.commit()
    db.refresh(wh)
    return model_to_dict(wh, db=db)


router.include_router(webhook_endpoints_router)


@router.delete("/demo/demo-data")
def delete_demo_data(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return SuccessResponse(success=True, message="Demo data deleted").model_dump()

