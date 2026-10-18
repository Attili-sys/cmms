"""Routes for Categories, Locations, FloorPlans, Assets, AssetDowntimes, AssetDeprecations, Vendors, Customers."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models.categories import (
    AssetCategory,
    CostCategory,
    MeterCategory,
    PartCategory,
    PurchaseOrderCategory,
    TimeCategory,
    WorkOrderCategory,
)
from src.models.location_asset import (
    Asset,
    AssetDowntime,
    Deprecation as AssetDeprecation,
    FloorPlan,
    Location,
)
from src.models.parts_po import Customer, Vendor
from src.models.users import User
from src.routes._crud import build_crud_router
from src.services.serializer import model_to_dict

router = APIRouter()

# 6.4 Category controllers (all 7)
def _add_category_mini_route(cat_router: APIRouter, cls: type) -> None:
    @cat_router.get("/mini")
    def _list_cat_mini(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[dict[str, Any]]:
        stmt = select(cls)
        if hasattr(cls, "company_id") and current_user.company_id is not None:
            stmt = stmt.where(cls.company_id == current_user.company_id)
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
def _serialize_location(loc: Location, db: Session) -> dict[str, Any]:
    res = model_to_dict(loc, db=db)
    children = db.scalars(select(Location).where(Location.parent_location_id == loc.id)).all()
    res["hasChildren"] = len(children) > 0
    return res


locations_router = build_crud_router("/locations", Location, custom_serializer=_serialize_location)


@locations_router.get("/mini")
def list_locations_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Location).where(Location.company_id == current_user.company_id)).all()
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
    stmt = select(Location).where(Location.company_id == current_user.company_id)
    if parent_id == 0:
        stmt = stmt.where(Location.parent_location_id.is_(None))
    else:
        stmt = stmt.where(Location.parent_location_id == parent_id)
    rows = db.scalars(stmt).all()
    return [_serialize_location(r, db) for r in rows]


router.include_router(locations_router)

floor_plans_router = build_crud_router("/floor-plans", FloorPlan)


@floor_plans_router.get("/location/{location_id:int}")
def list_floor_plans_by_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(FloorPlan).where(
            FloorPlan.location_id == location_id,
            FloorPlan.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(floor_plans_router)


# 6.6 Assets, AssetDowntime, AssetDeprecation
def _serialize_asset(asset: Asset, db: Session) -> dict[str, Any]:
    res = model_to_dict(asset, db=db)
    children = db.scalars(select(Asset).where(Asset.parent_asset_id == asset.id)).all()
    res["hasChildren"] = len(children) > 0
    if asset.location_id:
        loc = db.get(Location, asset.location_id)
        if loc:
            res["location"] = {"id": loc.id, "name": loc.name}
    return res


def _before_create_asset(asset: Asset, payload: dict[str, Any], current_user: User, db: Session) -> None:
    if not asset.custom_id:
        asset.custom_id = f"A{asset.id or 1:06d}"


assets_router = build_crud_router(
    "/assets",
    Asset,
    custom_serializer=_serialize_asset,
    before_create=_before_create_asset,
)


@assets_router.get("/mini")
def list_assets_mini(
    location_id: int | None = Query(default=None, alias="locationId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = select(Asset).where(Asset.company_id == current_user.company_id)
    if location_id is not None:
        stmt = stmt.where(Asset.location_id == location_id)
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
    stmt = select(Asset).where(Asset.company_id == current_user.company_id)
    if parent_id == 0:
        stmt = stmt.where(Asset.parent_asset_id.is_(None))
    else:
        stmt = stmt.where(Asset.parent_asset_id == parent_id)
    rows = db.scalars(stmt).all()
    return [_serialize_asset(r, db) for r in rows]


@assets_router.get("/location/{location_id:int}")
def list_assets_by_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Asset).where(
            Asset.location_id == location_id,
            Asset.company_id == current_user.company_id,
        )
    ).all()
    return [_serialize_asset(r, db) for r in rows]


router.include_router(assets_router)

downtimes_router = build_crud_router("/asset-downtimes", AssetDowntime)


@downtimes_router.get("/asset/{asset_id:int}")
def list_downtimes_by_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(AssetDowntime).where(
            AssetDowntime.asset_id == asset_id,
            AssetDowntime.company_id == current_user.company_id,
        )
    ).all()
    return [model_to_dict(r, db=db) for r in rows]


router.include_router(downtimes_router)
router.include_router(build_crud_router("/asset-deprecations", AssetDeprecation))


# 6.7 Vendors & Customers
vendors_router = build_crud_router("/vendors", Vendor)


@vendors_router.get("/mini")
def list_vendors_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Vendor).where(Vendor.company_id == current_user.company_id)).all()
    return [{"id": r.id, "companyName": r.company_name, "name": r.name} for r in rows]


router.include_router(vendors_router)

customers_router = build_crud_router("/customers", Customer)


@customers_router.get("/mini")
def list_customers_mini(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.scalars(select(Customer).where(Customer.company_id == current_user.company_id)).all()
    return [{"id": r.id, "name": r.name} for r in rows]


router.include_router(customers_router)
