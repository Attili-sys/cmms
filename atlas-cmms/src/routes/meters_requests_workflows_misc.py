"""Routes for Meters, Readings, Requests, Workflows, Files, CustomFields, Notifications, Webhooks, ApiKeys, Export, Import."""

from __future__ import annotations

import csv
import io
import secrets
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, File, Form, Response, UploadFile, WebSocket
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models._base import utcnow
from src.models.files_custom import CustomField, File as FileEntity, Notification
from src.models.integrations import ApiKey, WebhookEndpoint as WebhookConfig
from src.models.location_asset import Asset, Location
from src.models.meters import Meter, Reading, WorkOrderMeterTrigger
from src.models.parts_po import Part, Vendor
from src.models.requests import Request
from src.models.users import User
from src.models.work_orders import WorkOrder
from src.models.workflows import Workflow, WorkflowAction, WorkflowCondition
from src.routes._crud import build_crud_router
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict

router = APIRouter()


# 6.13 Meters & Readings
def _before_create_meter(
    meter: Meter, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if getattr(meter, "asset_id", None) is None:
        asset = db.scalar(select(Asset).where(Asset.company_id == current_user.company_id))
        if asset is None:
            asset = Asset(name="Default Asset", company_id=current_user.company_id)
            db.add(asset)
            db.flush()
        meter.asset_id = asset.id


meters_router = build_crud_router("/meters", Meter, before_create=_before_create_meter)


@meters_router.get("/mini")
def list_meters_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Meter).where(Meter.company_id == current_user.company_id)).all()
    return [{"id": r.id, "name": r.name, "unit": r.unit} for r in rows]


@meters_router.get("/asset/{asset_id:int}")
def list_meters_by_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Meter).where(
            Meter.asset_id == asset_id,
            Meter.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


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
            cond = trig.trigger_condition or 0  # 0=GREATER_THAN, 1=LESS_THAN
            should_fire = (cond == 0 and reading.value > trig.value) or (
                cond == 1 and reading.value < trig.value
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
                )
                db.add(wo)


readings_router = build_crud_router("/readings", Reading, after_create=_after_create_reading)


@readings_router.get("/meter/{meter_id:int}")
def list_readings_by_meter(
    meter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Reading).where(
            Reading.meter_id == meter_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(readings_router)


# 6.14 Requests
def _before_create_request(
    req: Request, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if req.cancelled is None:
        req.cancelled = False


def _after_create_request(
    req: Request, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not req.custom_id:
        req.custom_id = f"R{req.id:06d}"


requests_router = build_crud_router(
    "/requests",
    Request,
    before_create=_before_create_request,
    after_create=_after_create_request,
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
    wo = WorkOrder(
        title=req.title,
        description=req.description,
        priority=req.priority or 0,
        status=0,
        company_id=current_user.company_id,
        asset_id=req.asset_id,
        location_id=req.location_id,
        primary_user_id=req.primary_user_id,
        team_id=req.team_id,
        category_id=req.category_id,
        due_date=req.due_date,
        parent_request_id=req.id,
        created_by=current_user.id,
    )
    db.add(wo)
    db.flush()
    wo.custom_id = f"WO{wo.id:06d}"
    req.work_order_id = wo.id
    db.commit()
    db.refresh(wo)
    return model_to_dict(wo, db=db)


@requests_router.patch("/{req_id:int}/cancel")
def cancel_request(
    req_id: int,
    payload: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    req = db.get(Request, req_id)
    if not req:
        raise CustomException(status_code=404, message="Request not found")
    assert_company_access(current_user, req, is_super_admin=is_super_admin(current_user, db))
    req.cancelled = True
    req.cancellation_reason = payload.get("reason") or payload.get("cancellationReason")
    db.commit()
    db.refresh(req)
    return model_to_dict(req, db=db)


router.include_router(requests_router)


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
                cond = WorkflowCondition(company_id=current_user.company_id)
                apply_patch(cond, cdata)
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


@files_router.post("/upload", response_model=None)
async def upload_files(
    files: list[UploadFile] = File(default=[]),
    folder: str = Form(default="general"),
    hidden: str = Form(default="false"),
    type: str = Form(default="OTHER"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    created: list[FileEntity] = []
    is_hidden = hidden.lower() == "true"
    for f in files:
        fname = f.filename or "upload.bin"
        fe = FileEntity(
            name=fname,
            url=f"/media/{folder}/{fname}",
            file_type=0,
            hidden=is_hidden,
            company_id=current_user.company_id,
            created_by=current_user.id,
        )
        db.add(fe)
        db.flush()
        created.append(fe)
    db.commit()
    return [model_to_dict(fe, db=db) for fe in created]


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


# 6.19 Import / Export CSV
@router.get("/export/{entity_name}")
def export_csv(
    entity_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    entity_map: dict[str, tuple[type, list[str]]] = {
        "work-orders": (WorkOrder, ["id", "custom_id", "title", "description", "status", "priority"]),
        "assets": (Asset, ["id", "custom_id", "name", "description", "bar_code", "status"]),
        "locations": (Location, ["id", "custom_id", "name", "address"]),
        "parts": (Part, ["id", "name", "cost", "quantity", "barcode", "unit"]),
        "meters": (Meter, ["id", "name", "unit", "update_frequency"]),
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


@router.post("/import/{entity_name}")
def import_entities(
    entity_name: str,
    payload: list[dict[str, Any]] = Body(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    entity_map: dict[str, type] = {
        "work-orders": WorkOrder,
        "assets": Asset,
        "locations": Location,
        "parts": Part,
        "meters": Meter,
        "vendors": Vendor,
    }
    model_cls = entity_map.get(entity_name.lower())
    if not model_cls:
        raise CustomException(status_code=400, message=f"Unsupported import entity: {entity_name}")

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
            db.add(obj)
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


router.include_router(apikeys_router)
router.include_router(build_crud_router("/webhooks", WebhookConfig))
