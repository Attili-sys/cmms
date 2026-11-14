"""Routes for Categories, Locations, FloorPlans, Assets, AssetDowntimes, AssetDeprecations, Vendors, Customers."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import delete, func, insert, or_, select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.deps.permissions import PermissionEntity, can_edit_object, can_view
from src.models._base import utcnow
from src.models.associations import (
    t_asset_customer_associations,
    t_asset_file_associations,
    t_asset_part_associations,
    t_asset_team_associations,
    t_asset_user_associations,
    t_asset_vendor_associations,
    t_location_customer_associations,
    t_location_file_associations,
    t_location_team_associations,
    t_location_user_associations,
    t_location_vendor_associations,
)
from src.models.categories import (
    AssetCategory,
    CostCategory,
    MeterCategory,
    PartCategory,
    PurchaseOrderCategory,
    TimeCategory,
    WorkOrderCategory,
)
from src.models.files_custom import CustomField, CustomFieldValue, File
from src.models.location_asset import (
    Asset,
    AssetDowntime,
    Deprecation as AssetDeprecation,
    FloorPlan,
    FloorPlanPin,
    Location,
)
from src.models.enums import FloorPlanKind, Status
from src.models.work_orders import WorkOrder
from src.models.parts_po import Customer, Part, Vendor
from src.models.requests import RequestPortal
from src.models.users import Team, User
from src.routes._crud import _ensure_company_settings_id, build_crud_router
from src.schemas.errors import CustomException
from src.services.serializer import model_to_dict, resolve_enum_value, serialize_value
from src.utils.dates import ensure_utc
from src.utils.pagination import as_spring_page
from src.utils.search import SearchCriteria, apply_spring_sort, execute_search

router = APIRouter()


def _extract_rel_ids(items: Any) -> list[int]:
    """Extract integer IDs from a list of dicts ({'id': 1}) or scalar IDs."""
    if not isinstance(items, list):
        return []
    result: list[int] = []
    seen: set[int] = set()
    for item in items:
        raw_id = item.get("id") if isinstance(item, dict) else item
        if raw_id is None or isinstance(raw_id, bool):
            continue
        try:
            int_id = int(raw_id)
        except (ValueError, TypeError):
            continue
        if int_id not in seen:
            seen.add(int_id)
            result.append(int_id)
    return result


def _verify_and_sync_m2m(
    db: Session,
    current_user: User,
    *args: Any,
) -> None:
    """Validate tenant ownership of target IDs and replace M2M association rows."""
    if len(args) == 7 and isinstance(args[0], dict) and isinstance(args[1], str):
        payload, key_name, assoc_table, owner_col_or_name, owner_id, target_col_or_name, target_cls = args
        if key_name not in payload or not isinstance(payload[key_name], list):
            return
        raw_items = payload[key_name]
        owner_col = (
            getattr(assoc_table.c, owner_col_or_name)
            if isinstance(owner_col_or_name, str)
            else owner_col_or_name
        )
        target_col = (
            getattr(assoc_table.c, target_col_or_name)
            if isinstance(target_col_or_name, str)
            else target_col_or_name
        )
    else:
        assoc_table, owner_col_or_name, owner_id, target_col_or_name, target_cls, raw_items = args
        owner_col = (
            getattr(assoc_table.c, owner_col_or_name)
            if isinstance(owner_col_or_name, str)
            else owner_col_or_name
        )
        target_col = (
            getattr(assoc_table.c, target_col_or_name)
            if isinstance(target_col_or_name, str)
            else target_col_or_name
        )

    target_ids = _extract_rel_ids(raw_items)
    for tid in target_ids:
        target_obj = db.get(target_cls, tid)
        if target_obj is None:
            raise CustomException(
                status_code=400,
                message=f"Referenced {target_cls.__name__} {tid} does not exist",
            )
        if hasattr(target_obj, "company_id") and current_user.company_id is not None:
            try:
                assert_company_access(current_user, getattr(target_obj, "company_id", None))
            except CustomException as exc:
                raise CustomException(
                    status_code=400,
                    message=f"Cross-tenant reference to {target_cls.__name__} is not allowed",
                ) from exc

    db.execute(delete(assoc_table).where(owner_col == owner_id))
    for tid in target_ids:
        db.execute(
            insert(assoc_table).values(
                {owner_col.name: owner_id, target_col.name: tid}
            )
        )


def _sync_entity_custom_fields(
    *args: Any,
) -> None:
    """Synchronize CustomFieldValue rows for an entity."""
    if len(args) == 5 and isinstance(args[0], Session):
        db, current_user, entity_fk_col, entity_id, payload = args
    else:
        entity, payload, current_user, db, _col_obj, entity_fk_col = args
        entity_id = entity.id

    cf_list: list[Any] | None = None
    if isinstance(payload.get("customFields"), list) and len(payload["customFields"]) > 0:
        cf_list = payload["customFields"]
    elif (
        "customFieldValues" in payload
        and not payload.get("customFields")
        and isinstance(payload["customFieldValues"], list)
    ):
        cf_list = payload["customFieldValues"]
    elif (
        "customFields" in payload
        and isinstance(payload["customFields"], list)
        and "customFieldValues" not in payload
    ):
        cf_list = payload["customFields"]

    if cf_list is None:
        return

    cs_id = (
        _ensure_company_settings_id(current_user, db)
        if current_user.company_id is not None
        else None
    )
    fk_attr = getattr(CustomFieldValue, entity_fk_col)
    db.execute(delete(CustomFieldValue).where(fk_attr == entity_id))

    for item in cf_list:
        if not isinstance(item, dict):
            continue
        cf_id_raw = None
        if isinstance(item.get("customField"), dict):
            cf_id_raw = item["customField"].get("id")
        if cf_id_raw is None:
            cf_id_raw = item.get("customFieldId") or item.get("id")
        if cf_id_raw is None:
            continue
        try:
            cf_id = int(cf_id_raw)
        except (ValueError, TypeError):
            continue
        cf = db.get(CustomField, cf_id)
        if cf is None:
            raise CustomException(
                status_code=400,
                message=f"CustomField {cf_id} does not exist",
            )
        if cs_id is not None and cf.company_settings_id != cs_id:
            raise CustomException(
                status_code=400,
                message="Cross-tenant reference to CustomField is not allowed",
            )
        raw_val = item.get("value")
        val_str = "" if raw_val is None else str(raw_val)
        cfv = CustomFieldValue(
            custom_field_id=cf.id,
            value=val_str,
            created_by=current_user.id,
        )
        setattr(cfv, entity_fk_col, entity_id)
        db.add(cfv)
    db.flush()


def _hydrate_custom_field_values(
    db: Session,
    entity_fk_col_or_expr: Any,
    entity_id: int | None = None,
) -> list[dict[str, Any]]:
    if isinstance(entity_fk_col_or_expr, str):
        fk_attr = getattr(CustomFieldValue, entity_fk_col_or_expr)
        where_clause = fk_attr == entity_id
    else:
        where_clause = entity_fk_col_or_expr
    cfvs = db.scalars(select(CustomFieldValue).where(where_clause)).all()
    result: list[dict[str, Any]] = []
    for cfv in cfvs:
        cf = db.get(CustomField, cfv.custom_field_id)
        if cf is None:
            continue
        result.append(
            {
                "id": cfv.id,
                "value": cfv.value,
                "customField": model_to_dict(cf, db=db),
            }
        )
    return result


# 6.4 Category controllers (all 7)
def _add_category_mini_route(cat_router: APIRouter, cls: type) -> None:
    @cat_router.get("/mini")
    def _list_cat_mini(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[dict[str, Any]]:
        if not can_view(current_user, PermissionEntity.CATEGORIES, db):
            raise CustomException(status_code=403, message="Access is denied")
        stmt = select(cls)
        if hasattr(cls, "company_id") and current_user.company_id is not None:
            stmt = stmt.where(cls.company_id == current_user.company_id)
        elif hasattr(cls, "company_settings_id") and current_user.company_id is not None:
            cs_id = _ensure_company_settings_id(current_user, db)
            stmt = stmt.where(cls.company_settings_id == cs_id)
        rows = db.scalars(stmt).all()
        return [{"id": r.id, "name": r.name} for r in rows]


for cat_prefix, cat_cls in [
    ("/asset-categories", AssetCategory),
    ("/work-order-categories", WorkOrderCategory),
    ("/meter-categories", MeterCategory),
    ("/part-categories", PartCategory),
    ("/purchase-order-categories", PurchaseOrderCategory),
    ("/cost-categories", CostCategory),
    ("/time-categories", TimeCategory),
]:
    cat_router = build_crud_router(cat_prefix, cat_cls)
    _add_category_mini_route(cat_router, cat_cls)
    router.include_router(cat_router)


# 6.5 Locations & FloorPlans
def _validate_location_hierarchy(loc: Location, current_user: User, db: Session) -> None:
    if loc.parent_location_id is None:
        return
    if loc.id is not None and loc.parent_location_id == loc.id:
        raise CustomException(
            status_code=400,
            message="A location cannot be its own parent",
        )
    visited: set[int] = {loc.id} if loc.id is not None else set()
    cur_id: int | None = loc.parent_location_id
    cid = loc.company_id or current_user.company_id
    while cur_id is not None:
        if cur_id in visited:
            raise CustomException(
                status_code=400,
                message="Cyclic location hierarchy is not allowed",
            )
        visited.add(cur_id)
        parent = db.get(Location, cur_id)
        if parent is None:
            raise CustomException(status_code=400, message="Parent location not found")
        if cid is not None and parent.company_id != cid:
            raise CustomException(
                status_code=400,
                message="Cross-tenant parent location is not allowed",
            )
        cur_id = parent.parent_location_id


def _sync_location_relations(
    loc: Location,
    payload: dict[str, Any],
    current_user: User,
    db: Session,
) -> None:
    if "workers" in payload or "users" in payload:
        raw_users = payload.get("workers") if "workers" in payload else payload.get("users")
        _verify_and_sync_m2m(
            db,
            current_user,
            t_location_user_associations,
            t_location_user_associations.c.id_location,
            loc.id,
            t_location_user_associations.c.id_user,
            User,
            raw_users,
        )
    if "teams" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_location_team_associations,
            t_location_team_associations.c.id_location,
            loc.id,
            t_location_team_associations.c.id_team,
            Team,
            payload["teams"],
        )
    if "vendors" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_location_vendor_associations,
            t_location_vendor_associations.c.id_location,
            loc.id,
            t_location_vendor_associations.c.id_vendor,
            Vendor,
            payload["vendors"],
        )
    if "customers" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_location_customer_associations,
            t_location_customer_associations.c.id_location,
            loc.id,
            t_location_customer_associations.c.id_customer,
            Customer,
            payload["customers"],
        )
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_location_file_associations,
            t_location_file_associations.c.id_location,
            loc.id,
            t_location_file_associations.c.id_file,
            File,
            payload["files"],
        )
    _sync_entity_custom_fields(db, current_user, "location_id", loc.id, payload)


def _serialize_location(loc: Location, db: Session) -> dict[str, Any]:
    res = model_to_dict(loc, db=db)
    has_child = db.scalar(
        select(Location.id).where(Location.parent_location_id == loc.id).limit(1)
    )
    res["hasChildren"] = has_child is not None
    if loc.parent_location_id:
        parent = db.get(Location, loc.parent_location_id)
        if parent:
            res["parentLocation"] = {"id": parent.id, "name": parent.name}
    else:
        res["parentLocation"] = None

    # Hydrate M2M collections
    user_ids = db.scalars(
        select(t_location_user_associations.c.id_user).where(
            t_location_user_associations.c.id_location == loc.id
        )
    ).all()
    workers = [
        {
            "id": u.id,
            "firstName": u.first_name,
            "lastName": u.last_name,
            "email": u.email,
            "role": {"id": u.role_id} if u.role_id else None,
        }
        for uid in user_ids
        if (u := db.get(User, uid)) is not None
    ]
    res["workers"] = workers
    res["users"] = workers

    team_ids = db.scalars(
        select(t_location_team_associations.c.id_team).where(
            t_location_team_associations.c.id_location == loc.id
        )
    ).all()
    res["teams"] = [
        {"id": t.id, "name": t.name, "description": t.description}
        for tid in team_ids
        if (t := db.get(Team, tid)) is not None
    ]

    vendor_ids = db.scalars(
        select(t_location_vendor_associations.c.id_vendor).where(
            t_location_vendor_associations.c.id_location == loc.id
        )
    ).all()
    res["vendors"] = [
        model_to_dict(v, db=db)
        for vid in vendor_ids
        if (v := db.get(Vendor, vid)) is not None
    ]

    customer_ids = db.scalars(
        select(t_location_customer_associations.c.id_customer).where(
            t_location_customer_associations.c.id_location == loc.id
        )
    ).all()
    res["customers"] = [
        model_to_dict(c, db=db)
        for cid in customer_ids
        if (c := db.get(Customer, cid)) is not None
    ]

    file_ids = db.scalars(
        select(t_location_file_associations.c.id_file).where(
            t_location_file_associations.c.id_location == loc.id
        )
    ).all()
    res["files"] = [
        model_to_dict(f, db=db)
        for fid in file_ids
        if (f := db.get(File, fid)) is not None
    ]

    res["customFieldValues"] = _hydrate_custom_field_values(db, "location_id", loc.id)
    return res


def _before_create_location(
    loc: Location, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _validate_location_hierarchy(loc, current_user, db)


def _after_create_location(
    loc: Location, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not loc.custom_id:
        loc.custom_id = f"L{loc.id:06d}"
    _sync_location_relations(loc, payload, current_user, db)


def _after_patch_location(
    loc: Location, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _validate_location_hierarchy(loc, current_user, db)
    _sync_location_relations(loc, payload, current_user, db)


locations_router = build_crud_router(
    "/locations",
    Location,
    custom_serializer=_serialize_location,
    before_create=_before_create_location,
    after_create=_after_create_location,
    after_patch=_after_patch_location,
)


@locations_router.get("/mini")
def list_locations_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    rows = db.scalars(select(Location).where(Location.company_id == current_user.company_id)).all()
    return [
        {"id": r.id, "name": r.name, "parentId": r.parent_location_id, "customId": r.custom_id}
        for r in rows
    ]


@locations_router.get("/public/mini/{portal_uuid}")
@locations_router.get("/mini/{portal_uuid}")
def list_public_locations_mini(
    portal_uuid: str,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    portal = db.scalar(select(RequestPortal).where(RequestPortal.uuid == portal_uuid))
    if portal is None:
        return []
    rows = db.scalars(
        select(Location).where(Location.company_id == portal.company_id)
    ).all()
    return [
        {"id": r.id, "name": r.name, "parentId": r.parent_location_id, "customId": r.custom_id}
        for r in rows
    ]


@locations_router.get("/children/{parent_id:int}")
def list_location_children(
    parent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    stmt = select(Location).where(Location.company_id == current_user.company_id)
    if parent_id == 0:
        stmt = stmt.where(Location.parent_location_id.is_(None))
    else:
        stmt = stmt.where(Location.parent_location_id == parent_id)
    rows = db.scalars(stmt.order_by(Location.id.desc())).all()
    return [_serialize_location(r, db) for r in rows]


@locations_router.get("/children/{parent_id:int}/paginated")
def list_location_children_paginated(
    parent_id: int,
    page: int | None = Query(default=None),
    size: int | None = Query(default=None),
    page_num: int | None = Query(default=None, alias="pageNum"),
    page_size: int | None = Query(default=None, alias="pageSize"),
    sort: list[str] | None = Query(default=None),
    sort_field: str | None = Query(default=None, alias="sortField"),
    direction: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    eff_page = page if page is not None else (page_num if page_num is not None else 0)
    eff_size = size if size is not None else (page_size if page_size is not None else 40)

    base_stmt = select(Location).where(Location.company_id == current_user.company_id)
    if parent_id == 0:
        base_stmt = base_stmt.where(Location.parent_location_id.is_(None))
    else:
        base_stmt = base_stmt.where(Location.parent_location_id == parent_id)

    total_elements = (
        db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
    )
    sorted_stmt, resolved_field, resolved_dir = apply_spring_sort(
        base_stmt,
        Location,
        sort=sort,
        sort_field=sort_field,
        direction=direction,
    )
    offset = max(0, eff_page) * max(1, eff_size)
    rows = db.scalars(sorted_stmt.offset(offset).limit(max(1, eff_size))).all()
    serialized = [_serialize_location(r, db) for r in rows]
    return as_spring_page(
        items=serialized,
        total_elements=total_elements,
        page_num=eff_page,
        page_size=eff_size,
        sort_field=resolved_field,
        direction=resolved_dir,
    ).model_dump(by_alias=True)


router.include_router(locations_router)

# --- Floor plans (drawings) and asset pins ---------------------------------------------------
_MAX_LOCATION_DEPTH = 50
_WO_COMPLETE = list(Status).index(Status.COMPLETE)


def _location_ancestors(db: Session, location_id: int | None) -> list[int]:
    """The location and its ancestors, nearest first (cycle-safe, bounded)."""
    chain: list[int] = []
    seen: set[int] = set()
    cur = location_id
    while cur is not None and cur not in seen and len(chain) < _MAX_LOCATION_DEPTH:
        seen.add(cur)
        chain.append(cur)
        cur = db.scalar(select(Location.parent_location_id).where(Location.id == cur))
    return chain


def _location_subtree_ids(db: Session, root_id: int) -> list[int]:
    """The location and all its descendants (cycle-safe, bounded depth)."""
    seen: set[int] = {root_id}
    frontier = [root_id]
    for _ in range(_MAX_LOCATION_DEPTH):
        if not frontier:
            break
        children = db.scalars(
            select(Location.id).where(Location.parent_location_id.in_(frontier))
        ).all()
        frontier = [c for c in children if c not in seen]
        seen.update(frontier)
    return list(seen)


def _file_id_from_payload(payload: dict[str, Any]) -> int | None:
    for key in ("file", "image"):
        val = payload.get(key)
        raw = val.get("id") if isinstance(val, dict) else None
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                raise CustomException(status_code=406, message="Invalid file reference") from None
    for key in ("fileId", "imageId"):
        if payload.get(key) is not None:
            try:
                return int(payload[key])
            except (TypeError, ValueError):
                raise CustomException(status_code=406, message="Invalid file reference") from None
    return None


def _assert_can_edit_location(db: Session, current_user: User, location_id: int | None) -> Location:
    if location_id is None:
        raise CustomException(status_code=406, message="A location is required")
    loc = db.get(Location, location_id)
    if loc is None:
        raise CustomException(status_code=404, message="Location not found")
    assert_company_access(current_user, loc.company_id)
    if not can_edit_object(current_user, PermissionEntity.LOCATIONS, loc, db):
        raise CustomException(status_code=403, message="Access is denied")
    return loc


def _validate_kind(kind: Any) -> str | None:
    if kind is None or kind == "":
        return None
    if kind not in {k.value for k in FloorPlanKind}:
        raise CustomException(
            status_code=406,
            message="kind must be one of " + ", ".join(k.value for k in FloorPlanKind),
        )
    return str(kind)


def _floor_plan_dtos(rows: list[FloorPlan], db: Session) -> list[dict[str, Any]]:
    ids = [r.id for r in rows]
    counts: dict[int, int] = {}
    if ids:
        counts = dict(
            db.execute(
                select(FloorPlanPin.floor_plan_id, func.count(FloorPlanPin.id))
                .where(FloorPlanPin.floor_plan_id.in_(ids))
                .group_by(FloorPlanPin.floor_plan_id)
            ).all()
        )
    source_ids = {r.source_file_id for r in rows if r.source_file_id is not None}
    sources: dict[int, File] = {}
    if source_ids:
        sources = {f.id: f for f in db.scalars(select(File).where(File.id.in_(source_ids))).all()}
    out: list[dict[str, Any]] = []
    for r in rows:
        dto = model_to_dict(r, db=db)
        dto.setdefault("image", None)
        src = sources.get(r.source_file_id) if r.source_file_id is not None else None
        dto["sourceFile"] = (
            {"id": src.id, "name": src.name, "url": src.path} if src is not None else None
        )
        dto["current"] = r.superseded_by_id is None
        dto["supersededById"] = r.superseded_by_id
        dto["pinCount"] = int(counts.get(r.id, 0))
        out.append(dto)
    return out


def _serialize_floor_plan(plan: FloorPlan, db: Session) -> dict[str, Any]:
    return _floor_plan_dtos([plan], db)[0]


def _before_create_floor_plan(
    plan: FloorPlan, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    from src.services.floor_plan_render import classify_file, render_pdf_first_page

    name = (plan.name or "").strip() if isinstance(plan.name, str) else ""
    if not name:
        raise CustomException(status_code=406, message="A name is required")
    plan.name = name
    _assert_can_edit_location(db, current_user, plan.location_id)
    plan.kind = _validate_kind(payload.get("kind"))
    plan.superseded_by_id = None
    plan.source_file_id = None
    plan.created_at = utcnow()
    plan.created_by = current_user.id
    plan.image_id = None
    file_id = _file_id_from_payload(payload)
    if file_id is None:
        return
    f = db.get(File, file_id)
    if f is None:
        raise CustomException(status_code=404, message="File not found")
    assert_company_access(current_user, f.company_id)
    kind = classify_file(f)
    if kind == "image":
        plan.image_id = f.id
    elif kind == "pdf":
        png = render_pdf_first_page(db, f, created_by=current_user.id)
        plan.image_id = png.id
        plan.source_file_id = f.id
    else:
        raise CustomException(
            status_code=406,
            message="Unsupported drawing file: upload a PNG, JPG, WEBP, SVG or PDF",
        )


def _after_create_floor_plan(
    plan: FloorPlan, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    stmt = select(FloorPlan).where(
        FloorPlan.location_id == plan.location_id,
        FloorPlan.name == plan.name,
        FloorPlan.id != plan.id,
        FloorPlan.superseded_by_id.is_(None),
    )
    stmt = stmt.where(FloorPlan.kind.is_(None) if plan.kind is None else FloorPlan.kind == plan.kind)
    olds = db.scalars(stmt.order_by(FloorPlan.id)).all()
    if not olds:
        return
    copied: set[int] = set()
    for old in olds:
        old.superseded_by_id = plan.id
        for pin in db.scalars(select(FloorPlanPin).where(FloorPlanPin.floor_plan_id == old.id)).all():
            if pin.asset_id in copied:
                continue
            copied.add(pin.asset_id)
            db.add(
                FloorPlanPin(
                    company_id=pin.company_id,
                    floor_plan_id=plan.id,
                    asset_id=pin.asset_id,
                    x=pin.x,
                    y=pin.y,
                    created_by=current_user.id,
                    updated_by=current_user.id,
                )
            )
    db.flush()


def _before_patch_floor_plan(
    plan: FloorPlan, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    from src.services.floor_plan_render import classify_file

    _assert_can_edit_location(db, current_user, plan.location_id)
    # Server-managed or structural fields are never client-writable.
    for key in (
        "supersededById", "superseded_by_id", "supersededBy", "sourceFileId", "source_file_id",
        "sourceFile", "createdAt", "createdBy", "location", "locationId", "location_id", "file", "fileId",
    ):
        payload.pop(key, None)
    if "kind" in payload:
        payload["kind"] = _validate_kind(payload["kind"])
    if "image" in payload or "imageId" in payload:
        file_id = _file_id_from_payload(payload)
        if file_id is not None:
            f = db.get(File, file_id)
            if f is None:
                raise CustomException(status_code=404, message="File not found")
            assert_company_access(current_user, f.company_id)
            if classify_file(f) != "image":
                raise CustomException(status_code=406, message="The drawing image must be an image file")


def _before_delete_floor_plan(plan: FloorPlan, current_user: User, db: Session) -> None:
    _assert_can_edit_location(db, current_user, plan.location_id)
    # SQLite test databases may not enforce FK cascades; delete pins explicitly.
    db.execute(delete(FloorPlanPin).where(FloorPlanPin.floor_plan_id == plan.id))
    # Deleting a revision restores the one it superseded.
    for prev in db.scalars(select(FloorPlan).where(FloorPlan.superseded_by_id == plan.id)).all():
        prev.superseded_by_id = None


floor_plans_router = build_crud_router(
    "/floor-plans",
    FloorPlan,
    custom_serializer=_serialize_floor_plan,
    before_create=_before_create_floor_plan,
    after_create=_after_create_floor_plan,
    before_patch=_before_patch_floor_plan,
    before_delete=_before_delete_floor_plan,
)

# Extra routes live on their own router, included BEFORE the generic CRUD router so they win over
# its unscoped GET "" / POST /search (FloorPlan has no company_id of its own).
floor_plans_extra_router = APIRouter(prefix="/floor-plans", tags=["floor-plans"])


def _company_floor_plan_stmt(current_user: User) -> Any:
    stmt = select(FloorPlan)
    if current_user.company_id is not None:
        stmt = stmt.where(
            FloorPlan.location_id.in_(
                select(Location.id).where(Location.company_id == current_user.company_id)
            )
        )
    return stmt


@floor_plans_extra_router.get("")
def list_floor_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    rows = db.scalars(_company_floor_plan_stmt(current_user).order_by(FloorPlan.id)).all()
    return _floor_plan_dtos(list(rows), db)


@floor_plans_extra_router.post("/search")
def search_floor_plans(
    criteria: SearchCriteria = Body(default_factory=SearchCriteria),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    return execute_search(
        db=db,
        model_cls=FloorPlan,
        criteria=criteria,
        company_id=current_user.company_id,
        base_stmt=_company_floor_plan_stmt(current_user),
        serializer=lambda row: _serialize_floor_plan(row, db),
    )


@floor_plans_extra_router.get("/location/{location_id:int}")
def list_floor_plans_by_location(
    location_id: int,
    include_superseded: bool = Query(default=False, alias="includeSuperseded"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    loc = db.get(Location, location_id)
    if loc is None:
        raise CustomException(status_code=404, message="Location not found")
    assert_company_access(current_user, loc.company_id)
    stmt = select(FloorPlan).where(FloorPlan.location_id == location_id)
    if not include_superseded:
        stmt = stmt.where(FloorPlan.superseded_by_id.is_(None))
    rows = db.scalars(stmt.order_by(FloorPlan.id)).all()
    return _floor_plan_dtos(list(rows), db)


def _load_floor_plan(
    db: Session, current_user: User, plan_id: int, *, write: bool
) -> tuple[FloorPlan, Location]:
    if write:
        plan = db.get(FloorPlan, plan_id)
        if plan is None:
            raise CustomException(status_code=404, message="Floor plan not found")
        return plan, _assert_can_edit_location(db, current_user, plan.location_id)
    if not can_view(current_user, PermissionEntity.LOCATIONS, db):
        raise CustomException(status_code=403, message="Access is denied")
    plan = db.get(FloorPlan, plan_id)
    if plan is None:
        raise CustomException(status_code=404, message="Floor plan not found")
    loc = db.get(Location, plan.location_id)
    if loc is None:
        raise CustomException(status_code=404, message="Location not found")
    assert_company_access(current_user, loc.company_id)
    return plan, loc


def _asset_mini(asset: Asset, image_url: str | None, open_wos: int | None = None) -> dict[str, Any]:
    dto: dict[str, Any] = {
        "id": asset.id,
        "name": asset.name,
        "customId": asset.custom_id,
        "status": resolve_enum_value("status", asset.status, "Asset") or "OPERATIONAL",
        "image": {"url": image_url} if image_url else None,
    }
    if open_wos is not None:
        dto["openWorkOrders"] = open_wos
    return dto


@floor_plans_extra_router.get("/{plan_id:int}/pins")
def list_floor_plan_pins(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    _load_floor_plan(db, current_user, plan_id, write=False)
    rows = db.execute(
        select(FloorPlanPin, Asset)
        .join(Asset, Asset.id == FloorPlanPin.asset_id)
        .where(FloorPlanPin.floor_plan_id == plan_id)
        .order_by(FloorPlanPin.id)
    ).all()
    asset_ids = [a.id for _, a in rows]
    wo_counts: dict[int, int] = {}
    images: dict[int, str] = {}
    if asset_ids:
        wo_counts = dict(
            db.execute(
                select(WorkOrder.asset_id, func.count(WorkOrder.id))
                .where(
                    WorkOrder.asset_id.in_(asset_ids),
                    WorkOrder.archived.is_(False),
                    or_(WorkOrder.status.is_(None), WorkOrder.status != _WO_COMPLETE),
                )
                .group_by(WorkOrder.asset_id)
            ).all()
        )
        image_ids = {a.image_id for _, a in rows if a.image_id is not None}
        if image_ids:
            images = {
                fid: path
                for fid, path in db.execute(
                    select(File.id, File.path).where(File.id.in_(image_ids))
                ).all()
            }
    return [
        {
            "id": pin.id,
            "x": pin.x,
            "y": pin.y,
            "asset": _asset_mini(
                a, images.get(a.image_id) if a.image_id is not None else None, int(wo_counts.get(a.id, 0))
            ),
        }
        for pin, a in rows
    ]


def _asset_in_plan_subtree(db: Session, asset: Asset, plan_location_id: int) -> bool:
    return asset.location_id is not None and plan_location_id in _location_ancestors(db, asset.location_id)


@floor_plans_extra_router.put("/{plan_id:int}/pins/{asset_id:int}")
def put_floor_plan_pin(
    plan_id: int,
    asset_id: int,
    payload: dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    plan, loc = _load_floor_plan(db, current_user, plan_id, write=True)
    coords: list[float] = []
    for key in ("x", "y"):
        v = payload.get(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (0 <= v <= 1):
            raise CustomException(status_code=406, message=f"{key} must be a number between 0 and 1")
        coords.append(float(v))
    if plan.superseded_by_id is not None:
        raise CustomException(status_code=406, message="This drawing has been superseded")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise CustomException(status_code=404, message="Asset not found")
    assert_company_access(current_user, asset.company_id)
    if asset.company_id != loc.company_id:
        raise CustomException(status_code=406, message="Asset and drawing belong to different companies")
    if not _asset_in_plan_subtree(db, asset, plan.location_id):
        raise CustomException(
            status_code=406, message="The asset is not located in this drawing's location"
        )
    pin = db.scalar(
        select(FloorPlanPin).where(
            FloorPlanPin.floor_plan_id == plan_id, FloorPlanPin.asset_id == asset_id
        )
    )
    if pin is None:
        pin = FloorPlanPin(
            company_id=loc.company_id,
            floor_plan_id=plan_id,
            asset_id=asset_id,
            x=coords[0],
            y=coords[1],
            created_by=current_user.id,
        )
        db.add(pin)
    pin.x, pin.y = coords
    pin.updated_by = current_user.id
    pin.updated_at = utcnow()
    db.commit()
    db.refresh(pin)
    image_url = db.scalar(select(File.path).where(File.id == asset.image_id)) if asset.image_id else None
    return {"id": pin.id, "x": pin.x, "y": pin.y, "asset": _asset_mini(asset, image_url)}


@floor_plans_extra_router.delete("/{plan_id:int}/pins/{asset_id:int}")
def delete_floor_plan_pin(
    plan_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _load_floor_plan(db, current_user, plan_id, write=True)
    db.execute(
        delete(FloorPlanPin).where(
            FloorPlanPin.floor_plan_id == plan_id, FloorPlanPin.asset_id == asset_id
        )
    )
    db.commit()
    return {"success": True}


@floor_plans_extra_router.get("/{plan_id:int}/pinnable-assets")
def list_pinnable_assets(
    plan_id: int,
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    plan, loc = _load_floor_plan(db, current_user, plan_id, write=False)
    stmt = select(Asset).where(
        Asset.company_id == loc.company_id,
        Asset.archived.is_(False),
        Asset.location_id.in_(_location_subtree_ids(db, plan.location_id)),
        Asset.id.not_in(select(FloorPlanPin.asset_id).where(FloorPlanPin.floor_plan_id == plan_id)),
    )
    if search and search.strip():
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(Asset.name.ilike(like), Asset.custom_id.ilike(like)))
    rows = db.scalars(stmt.order_by(Asset.name, Asset.id).limit(50)).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "customId": a.custom_id,
            "status": resolve_enum_value("status", a.status, "Asset") or "OPERATIONAL",
        }
        for a in rows
    ]


router.include_router(floor_plans_extra_router)
router.include_router(floor_plans_router)


# 6.6 Assets, AssetDowntime, AssetDeprecation
def is_really_down(status: int | None) -> bool:
    """Matches Java AssetStatus.isReallyDown(): DOWN (1) or EMERGENCY_SHUTDOWN (6)."""
    return status in (1, 6)


def trigger_asset_downtime(
    asset_id: int,
    db: Session,
    user_id: int | None = None,
    reason: str | None = None,
) -> None:
    """Create a running AssetDowntime on asset_id and cascade DOWN status to ancestors."""
    cur = db.get(Asset, asset_id)
    visited: set[int] = set()
    now = utcnow()
    while cur is not None and cur.id not in visited:
        visited.add(cur.id)
        if not is_really_down(cur.status):
            cur.status = 1  # DOWN
        running = db.scalar(
            select(AssetDowntime).where(
                AssetDowntime.asset_id == cur.id,
                or_(AssetDowntime.duration == 0, AssetDowntime.duration.is_(None)),
            )
        )
        if running is None:
            dt = AssetDowntime(
                asset_id=cur.id,
                company_id=cur.company_id,
                starts_on=now,
                duration=0,
                created_by=user_id,
            )
            db.add(dt)
        cur = db.get(Asset, cur.parent_asset_id) if cur.parent_asset_id else None
    db.flush()


def stop_asset_downtime(
    asset_id: int,
    db: Session,
    stop_children: bool = True,
    visited: set[int] | None = None,
) -> None:
    """Close running AssetDowntime rows on asset_id and recursively restore down children."""
    if visited is None:
        visited = set()
    if asset_id in visited:
        return
    visited.add(asset_id)

    now = utcnow()
    running_rows = db.scalars(
        select(AssetDowntime)
        .where(
            AssetDowntime.asset_id == asset_id,
            or_(AssetDowntime.duration == 0, AssetDowntime.duration.is_(None)),
        )
        .order_by(AssetDowntime.starts_on.desc())
    ).all()
    for dt in running_rows:
        if dt.starts_on is not None:
            elapsed = max(1, int((now - ensure_utc(dt.starts_on)).total_seconds()))
        else:
            elapsed = 1
        dt.duration = elapsed

    if stop_children:
        children = db.scalars(
            select(Asset).where(Asset.parent_asset_id == asset_id)
        ).all()
        for child in children:
            if is_really_down(child.status):
                child.status = 0  # OPERATIONAL
                stop_asset_downtime(child.id, db, stop_children=True, visited=visited)
    db.flush()


def _validate_asset_integrity(
    asset: Asset,
    current_user: User,
    db: Session,
) -> None:
    """Validate ancestor cycles and tenant-scoped uniqueness of custom_id, bar_code, nfc_id."""
    cid = asset.company_id or current_user.company_id

    # 1. Ancestor cycle check
    if asset.parent_asset_id is not None:
        if asset.id is not None and asset.parent_asset_id == asset.id:
            raise CustomException(
                status_code=400,
                message="An asset cannot be its own parent",
            )
        visited: set[int] = {asset.id} if asset.id is not None else set()
        cur_id: int | None = asset.parent_asset_id
        while cur_id is not None:
            if cur_id in visited:
                raise CustomException(
                    status_code=400,
                    message="Cyclic asset hierarchy is not allowed",
                )
            visited.add(cur_id)
            parent = db.get(Asset, cur_id)
            if parent is None:
                raise CustomException(status_code=400, message="Parent asset not found")
            if cid is not None and parent.company_id != cid:
                raise CustomException(
                    status_code=400,
                    message="Cross-tenant parent asset is not allowed",
                )
            cur_id = parent.parent_asset_id

    # 2. Normalize blank identifiers to None and check uniqueness per company_id
    for attr, label in (
        ("custom_id", "Custom ID"),
        ("bar_code", "Barcode"),
        ("nfc_id", "NFC ID"),
    ):
        raw_val = getattr(asset, attr, None)
        if isinstance(raw_val, str):
            raw_val = raw_val.strip() or None
            setattr(asset, attr, raw_val)
        if raw_val is not None and cid is not None:
            stmt = select(Asset.id).where(
                Asset.company_id == cid,
                getattr(Asset, attr) == raw_val,
            )
            if asset.id is not None:
                stmt = stmt.where(Asset.id != asset.id)
            existing_id = db.scalar(stmt.limit(1))
            if existing_id is not None:
                raise CustomException(
                    status_code=409,
                    message=f"An asset with this {label} already exists",
                )


def _sync_asset_relations(
    asset: Asset,
    payload: dict[str, Any],
    current_user: User,
    db: Session,
) -> None:
    if "parts" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_asset_part_associations,
            t_asset_part_associations.c.id_asset,
            asset.id,
            t_asset_part_associations.c.id_part,
            Part,
            payload["parts"],
        )
    if "files" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_asset_file_associations,
            t_asset_file_associations.c.id_asset,
            asset.id,
            t_asset_file_associations.c.id_file,
            File,
            payload["files"],
        )
    if "teams" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_asset_team_associations,
            t_asset_team_associations.c.id_asset,
            asset.id,
            t_asset_team_associations.c.id_team,
            Team,
            payload["teams"],
        )
    if "users" in payload or "assignedTo" in payload:
        raw_users = payload.get("users") if "users" in payload else payload.get("assignedTo")
        _verify_and_sync_m2m(
            db,
            current_user,
            t_asset_user_associations,
            t_asset_user_associations.c.id_asset,
            asset.id,
            t_asset_user_associations.c.id_user,
            User,
            raw_users,
        )
    if "vendors" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_asset_vendor_associations,
            t_asset_vendor_associations.c.id_asset,
            asset.id,
            t_asset_vendor_associations.c.id_vendor,
            Vendor,
            payload["vendors"],
        )
    if "customers" in payload:
        _verify_and_sync_m2m(
            db,
            current_user,
            t_asset_customer_associations,
            t_asset_customer_associations.c.id_asset,
            asset.id,
            t_asset_customer_associations.c.id_customer,
            Customer,
            payload["customers"],
        )
    _sync_entity_custom_fields(db, current_user, "asset_id", asset.id, payload)


def _serialize_asset(asset: Asset, db: Session) -> dict[str, Any]:
    res = model_to_dict(asset, db=db)
    if not res.get("status"):
        res["status"] = "OPERATIONAL"
    has_child = db.scalar(
        select(Asset.id).where(Asset.parent_asset_id == asset.id).limit(1)
    )
    res["hasChildren"] = has_child is not None
    if asset.location_id:
        loc = db.get(Location, asset.location_id)
        if loc:
            res["location"] = {"id": loc.id, "name": loc.name}
    if asset.parent_asset_id:
        pa = db.get(Asset, asset.parent_asset_id)
        if pa:
            res["parentAsset"] = {"id": pa.id, "name": pa.name}
    else:
        res["parentAsset"] = None
    if asset.category_id:
        cat = db.get(AssetCategory, asset.category_id)
        if cat:
            res["category"] = {"id": cat.id, "name": cat.name}
    if asset.primary_user_id:
        pu = db.get(User, asset.primary_user_id)
        if pu:
            res["primaryUser"] = {
                "id": pu.id,
                "firstName": pu.first_name,
                "lastName": pu.last_name,
                "email": pu.email,
            }

    # Hydrate M2M collections
    part_ids = db.scalars(
        select(t_asset_part_associations.c.id_part).where(
            t_asset_part_associations.c.id_asset == asset.id
        )
    ).all()
    res["parts"] = [
        model_to_dict(p, db=db)
        for pid in part_ids
        if (p := db.get(Part, pid)) is not None
    ]

    file_ids = db.scalars(
        select(t_asset_file_associations.c.id_file).where(
            t_asset_file_associations.c.id_asset == asset.id
        )
    ).all()
    res["files"] = [
        model_to_dict(f, db=db)
        for fid in file_ids
        if (f := db.get(File, fid)) is not None
    ]

    team_ids = db.scalars(
        select(t_asset_team_associations.c.id_team).where(
            t_asset_team_associations.c.id_asset == asset.id
        )
    ).all()
    res["teams"] = [
        {"id": t.id, "name": t.name, "description": t.description}
        for tid in team_ids
        if (t := db.get(Team, tid)) is not None
    ]

    user_ids = db.scalars(
        select(t_asset_user_associations.c.id_user).where(
            t_asset_user_associations.c.id_asset == asset.id
        )
    ).all()
    users = [
        {
            "id": u.id,
            "firstName": u.first_name,
            "lastName": u.last_name,
            "email": u.email,
            "role": {"id": u.role_id} if u.role_id else None,
        }
        for uid in user_ids
        if (u := db.get(User, uid)) is not None
    ]
    res["users"] = users
    res["assignedTo"] = users

    vendor_ids = db.scalars(
        select(t_asset_vendor_associations.c.id_vendor).where(
            t_asset_vendor_associations.c.id_asset == asset.id
        )
    ).all()
    res["vendors"] = [
        model_to_dict(v, db=db)
        for vid in vendor_ids
        if (v := db.get(Vendor, vid)) is not None
    ]

    customer_ids = db.scalars(
        select(t_asset_customer_associations.c.id_customer).where(
            t_asset_customer_associations.c.id_asset == asset.id
        )
    ).all()
    res["customers"] = [
        model_to_dict(c, db=db)
        for cid in customer_ids
        if (c := db.get(Customer, cid)) is not None
    ]

    res["customFieldValues"] = _hydrate_custom_field_values(db, "asset_id", asset.id)
    return res


def _before_create_asset(
    asset: Asset, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if asset.status is None:
        asset.status = 0  # OPERATIONAL
    if asset.archived is None:
        asset.archived = False
    if asset.parent_asset_id is not None and asset.location_id is None:
        parent = db.get(Asset, asset.parent_asset_id)
        if parent is not None and parent.location_id is not None:
            asset.location_id = parent.location_id
    _validate_asset_integrity(asset, current_user, db)


def _notify_asset_assignees(
    asset: Asset, current_user: User, db: Session, *, message: str
) -> None:
    from src.models.enums import NotificationType
    from src.services.notifications import create_in_app_notifications

    user_ids = list(
        db.scalars(
            select(t_asset_user_associations.c.id_user).where(
                t_asset_user_associations.c.id_asset == asset.id
            )
        ).all()
    )
    if asset.primary_user_id is not None:
        user_ids.append(asset.primary_user_id)
    team_ids = list(
        db.scalars(
            select(t_asset_team_associations.c.id_team).where(
                t_asset_team_associations.c.id_asset == asset.id
            )
        ).all()
    )
    create_in_app_notifications(
        db,
        user_ids=user_ids,
        team_ids=team_ids,
        message=message,
        notification_type=NotificationType.ASSET,
        resource_id=asset.id,
        exclude_user_id=current_user.id,
        created_by=current_user.id,
    )


def _after_create_asset(
    asset: Asset, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if not asset.custom_id:
        asset.custom_id = f"A{asset.id:06d}"
    _sync_asset_relations(asset, payload, current_user, db)
    if is_really_down(asset.status):
        trigger_asset_downtime(asset.id, db, user_id=current_user.id)
    _notify_asset_assignees(
        asset,
        current_user,
        db,
        message=f"You have been assigned to asset {asset.name}",
    )


def _prune_stale_pins(asset: Asset, db: Session) -> None:
    """Keep only pins whose drawing is at the asset's (new) location or one of its ancestors."""
    allowed = set(_location_ancestors(db, asset.location_id))
    rows = db.execute(
        select(FloorPlanPin.id, FloorPlan.location_id)
        .join(FloorPlan, FloorPlan.id == FloorPlanPin.floor_plan_id)
        .where(FloorPlanPin.asset_id == asset.id)
    ).all()
    stale = [pid for pid, plan_loc in rows if plan_loc not in allowed]
    if stale:
        db.execute(delete(FloorPlanPin).where(FloorPlanPin.id.in_(stale)))


def _before_delete_asset(asset: Asset, current_user: User, db: Session) -> None:
    # SQLite test databases may not enforce FK cascades; delete pins explicitly.
    db.execute(delete(FloorPlanPin).where(FloorPlanPin.asset_id == asset.id))


def _before_patch_asset(
    asset: Asset, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    asset._old_status = asset.status  # type: ignore[attr-defined]
    asset._old_location_id = asset.location_id  # type: ignore[attr-defined]


def _after_patch_asset(
    asset: Asset, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _validate_asset_integrity(asset, current_user, db)
    _sync_asset_relations(asset, payload, current_user, db)
    if asset.location_id != getattr(asset, "_old_location_id", asset.location_id):
        _prune_stale_pins(asset, db)
    old_down = is_really_down(getattr(asset, "_old_status", None))
    new_down = is_really_down(asset.status)
    if not old_down and new_down:
        trigger_asset_downtime(asset.id, db, user_id=current_user.id)
        _notify_asset_assignees(
            asset,
            current_user,
            db,
            message=f"Asset {asset.name} is down",
        )
    elif old_down and not new_down:
        stop_asset_downtime(asset.id, db, stop_children=True)
    elif any(k in payload for k in ("primaryUser", "users", "assignedTo", "teams")):
        _notify_asset_assignees(
            asset,
            current_user,
            db,
            message=f"Asset {asset.name} has been updated",
        )


assets_router = build_crud_router(
    "/assets",
    Asset,
    custom_serializer=_serialize_asset,
    before_create=_before_create_asset,
    after_create=_after_create_asset,
    before_patch=_before_patch_asset,
    after_patch=_after_patch_asset,
    before_delete=_before_delete_asset,
)


@assets_router.get("/mini")
def list_assets_mini(
    location_id: str | None = Query(default=None, alias="locationId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    stmt = select(Asset).where(Asset.company_id == current_user.company_id)
    if location_id and location_id.isdigit():
        stmt = stmt.where(Asset.location_id == int(location_id))
    rows = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "customId": r.custom_id,
            "parentId": r.parent_asset_id,
            "locationId": r.location_id,
        }
        for r in rows
    ]


@assets_router.get("/public/mini/{portal_uuid}")
@assets_router.get("/mini/{portal_uuid}")
def list_public_assets_mini(
    portal_uuid: str,
    location_id: str | None = Query(default=None, alias="locationId"),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    portal = db.scalar(select(RequestPortal).where(RequestPortal.uuid == portal_uuid))
    if portal is None:
        return []
    stmt = select(Asset).where(Asset.company_id == portal.company_id)
    if location_id and location_id.isdigit():
        stmt = stmt.where(Asset.location_id == int(location_id))
    rows = db.scalars(stmt).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "customId": r.custom_id,
            "parentId": r.parent_asset_id,
            "locationId": r.location_id,
        }
        for r in rows
    ]


@assets_router.get("/children/{parent_id:int}")
def list_asset_children(
    parent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    stmt = select(Asset).where(Asset.company_id == current_user.company_id)
    if parent_id == 0:
        stmt = stmt.where(Asset.parent_asset_id.is_(None))
    else:
        stmt = stmt.where(Asset.parent_asset_id == parent_id)
    rows = db.scalars(stmt.order_by(Asset.id.desc())).all()
    return [_serialize_asset(r, db) for r in rows]


@assets_router.get("/children/{parent_id:int}/paginated")
def list_asset_children_paginated(
    parent_id: int,
    page: int | None = Query(default=None),
    size: int | None = Query(default=None),
    page_num: int | None = Query(default=None, alias="pageNum"),
    page_size: int | None = Query(default=None, alias="pageSize"),
    sort: list[str] | None = Query(default=None),
    sort_field: str | None = Query(default=None, alias="sortField"),
    direction: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    eff_page = page if page is not None else (page_num if page_num is not None else 0)
    eff_size = size if size is not None else (page_size if page_size is not None else 40)

    base_stmt = select(Asset).where(Asset.company_id == current_user.company_id)
    if parent_id == 0:
        base_stmt = base_stmt.where(Asset.parent_asset_id.is_(None))
    else:
        base_stmt = base_stmt.where(Asset.parent_asset_id == parent_id)

    total_elements = (
        db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
    )
    sorted_stmt, resolved_field, resolved_dir = apply_spring_sort(
        base_stmt,
        Asset,
        sort=sort,
        sort_field=sort_field,
        direction=direction,
    )
    offset = max(0, eff_page) * max(1, eff_size)
    rows = db.scalars(sorted_stmt.offset(offset).limit(max(1, eff_size))).all()
    serialized = [_serialize_asset(r, db) for r in rows]
    return as_spring_page(
        items=serialized,
        total_elements=total_elements,
        page_num=eff_page,
        page_size=eff_size,
        sort_field=resolved_field,
        direction=resolved_dir,
    ).model_dump(by_alias=True)


@assets_router.get("/location/{location_id:int}")
def list_assets_by_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    rows = db.scalars(
        select(Asset).where(
            Asset.location_id == location_id,
            Asset.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_asset(r, db) for r in rows]


@assets_router.get("/part/{part_id:int}")
def list_assets_by_part(
    part_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    part = db.get(Part, part_id)
    if part is not None:
        assert_company_access(current_user, part.company_id)

    asset_ids = db.scalars(
        select(t_asset_part_associations.c.id_asset).where(
            t_asset_part_associations.c.id_part == part_id
        )
    ).all()
    if not asset_ids:
        return []
    rows = db.scalars(
        select(Asset).where(
            Asset.id.in_(asset_ids),
            Asset.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_asset(r, db) for r in rows]


@assets_router.get("/nfc")
def get_asset_by_nfc(
    nfc_id: str = Query(default="", alias="nfcId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    asset = db.scalar(
        select(Asset).where(
            Asset.nfc_id == nfc_id,
            Asset.company_id == current_user.company_id,
        )
    )
    if not asset:
        raise CustomException(status_code=404, message="Asset not found")
    return _serialize_asset(asset, db)


@assets_router.get("/barcode")
def get_asset_by_barcode(
    barcode: str | None = Query(default=None),
    data: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    code = barcode if barcode is not None else (data or "")
    asset = db.scalar(
        select(Asset).where(
            Asset.bar_code == code,
            Asset.company_id == current_user.company_id,
        )
    )
    if not asset:
        raise CustomException(status_code=404, message="Asset not found")
    return _serialize_asset(asset, db)


@assets_router.get("/{asset_id:int}/floor-plan-pins")
def list_asset_floor_plan_pins(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise CustomException(status_code=404, message="Asset not found")
    assert_company_access(current_user, asset.company_id)
    rows = db.execute(
        select(FloorPlanPin, FloorPlan)
        .join(FloorPlan, FloorPlan.id == FloorPlanPin.floor_plan_id)
        .where(FloorPlanPin.asset_id == asset_id, FloorPlan.superseded_by_id.is_(None))
        .order_by(FloorPlanPin.id)
    ).all()
    return [
        {
            "floorPlan": {
                "id": plan.id,
                "name": plan.name,
                "kind": plan.kind,
                "revision": plan.revision,
                "locationId": plan.location_id,
            },
            "x": pin.x,
            "y": pin.y,
        }
        for pin, plan in rows
    ]


router.include_router(assets_router)


# AssetDowntimes with Java overlap validation (HTTP 406)
def _check_downtime_overlapping(downtime: AssetDowntime, db: Session) -> None:
    if downtime.starts_on is None or downtime.asset_id is None:
        return
    dur = int(downtime.duration or 0)
    if dur <= 0:
        return
    starts = ensure_utc(downtime.starts_on)
    ends = starts + timedelta(seconds=dur)

    stmt = select(AssetDowntime).where(AssetDowntime.asset_id == downtime.asset_id)
    if downtime.id is not None:
        stmt = stmt.where(AssetDowntime.id != downtime.id)
    others = db.scalars(stmt).all()
    for other in others:
        if other.starts_on is None:
            continue
        other_dur = int(other.duration or 0)
        if other_dur <= 0:
            continue
        other_starts = ensure_utc(other.starts_on)
        other_ends = other_starts + timedelta(seconds=other_dur)
        if starts < other_ends and ends > other_starts:
            raise CustomException(
                status_code=406,
                message="The downtimes can't interweave",
            )


def _serialize_downtime(dt: AssetDowntime, db: Session) -> dict[str, Any]:
    res = model_to_dict(dt, db=db)
    if dt.starts_on is not None and dt.duration and int(dt.duration) > 0:
        res["endsOn"] = serialize_value(
            dt.starts_on + timedelta(seconds=int(dt.duration))
        )
    else:
        res["endsOn"] = None
    return res


def _before_create_downtime(
    dt: AssetDowntime, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _check_downtime_overlapping(dt, db)


def _after_patch_downtime(
    dt: AssetDowntime, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    _check_downtime_overlapping(dt, db)


downtimes_router = build_crud_router(
    "/asset-downtimes",
    AssetDowntime,
    custom_serializer=_serialize_downtime,
    before_create=_before_create_downtime,
    after_patch=_after_patch_downtime,
)


@downtimes_router.get("/asset/{asset_id:int}")
def list_downtimes_by_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.ASSETS, db):
        raise CustomException(status_code=403, message="Access is denied")
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise CustomException(status_code=404, message="Asset not found")
    assert_company_access(current_user, asset.company_id)
    rows = db.scalars(
        select(AssetDowntime).where(
            AssetDowntime.asset_id == asset_id,
            AssetDowntime.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_downtime(r, db) for r in rows]


router.include_router(downtimes_router)
router.include_router(build_crud_router("/asset-deprecations", AssetDeprecation))
router.include_router(build_crud_router("/deprecations", AssetDeprecation))


# 6.7 Vendors & Customers
def _serialize_vendor(vendor: Vendor, db: Session) -> dict[str, Any]:
    base = model_to_dict(vendor, db=db)
    base["customFieldValues"] = _hydrate_custom_field_values(
        db, "vendor_id", vendor.id
    )
    return base


def _sync_vendor_relations(
    vendor: Vendor, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if vendor.id is None:
        return
    _sync_entity_custom_fields(db, current_user, "vendor_id", vendor.id, payload)


vendors_router = build_crud_router(
    "/vendors",
    Vendor,
    custom_serializer=_serialize_vendor,
    after_create=_sync_vendor_relations,
    after_patch=_sync_vendor_relations,
)


@vendors_router.get("/mini")
def list_vendors_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.VENDORS_AND_CUSTOMERS, db):
        raise CustomException(status_code=403, message="Access is denied")
    rows = db.scalars(select(Vendor).where(Vendor.company_id == current_user.company_id)).all()
    return [{"id": r.id, "companyName": r.company_name, "name": r.name} for r in rows]


router.include_router(vendors_router)


def _serialize_customer(customer: Customer, db: Session) -> dict[str, Any]:
    base = model_to_dict(customer, db=db)
    base["customFieldValues"] = _hydrate_custom_field_values(
        db, "customer_id", customer.id
    )
    return base


def _sync_customer_relations(
    customer: Customer, payload: dict[str, Any], current_user: User, db: Session
) -> None:
    if customer.id is None:
        return
    _sync_entity_custom_fields(db, current_user, "customer_id", customer.id, payload)


customers_router = build_crud_router(
    "/customers",
    Customer,
    custom_serializer=_serialize_customer,
    after_create=_sync_customer_relations,
    after_patch=_sync_customer_relations,
)


@customers_router.get("/mini")
def list_customers_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if not can_view(current_user, PermissionEntity.VENDORS_AND_CUSTOMERS, db):
        raise CustomException(status_code=403, message="Access is denied")
    rows = db.scalars(select(Customer).where(Customer.company_id == current_user.company_id)).all()
    return [{"id": r.id, "name": r.name} for r in rows]


router.include_router(customers_router)

