"""Generic CRUD router factory for Company-scoped entities matching Spring controllers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.deps.company import assert_company_access, is_super_admin
from src.deps.current_user import get_current_user
from src.deps.db import get_db
from src.models.company import Company
from src.models.settings import CompanySettings
from src.models.users import User
from src.schemas.errors import CustomException, SuccessResponse
from src.services.serializer import apply_patch, model_to_dict
from src.utils.search import SearchCriteria, execute_search


def _ensure_company_settings_id(current_user: User, db: Session) -> int:
    cs = db.scalar(select(CompanySettings).where(CompanySettings.company_id == current_user.company_id))
    if cs is None:
        cs = CompanySettings(company_id=current_user.company_id)
        db.add(cs)
        db.flush()
        comp = db.get(Company, current_user.company_id) if current_user.company_id else None
        if comp is not None and comp.company_settings_id is None:
            comp.company_settings_id = cs.id
            db.flush()
    return cs.id


def build_crud_router(
    prefix: str,
    model_cls: type,
    tags: list[str] | None = None,
    custom_serializer: Callable[[Any, Session], dict[str, Any]] | None = None,
    before_create: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
    after_create: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
    after_patch: Callable[[Any, dict[str, Any], User, Session], None] | None = None,
) -> APIRouter:
    """Create a standard Spring-compatible CRUD + /search router for model_cls."""
    router = APIRouter(prefix=prefix, tags=tags or [prefix.strip("/")])

    def _serialize(obj: Any, db: Session) -> dict[str, Any]:
        if custom_serializer is not None:
            return custom_serializer(obj, db)
        return model_to_dict(obj, db=db)

    @router.post("/search")
    def search_items(
        criteria: SearchCriteria = Body(default_factory=SearchCriteria),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return execute_search(
            db=db,
            model_cls=model_cls,
            criteria=criteria,
            company_id=current_user.company_id,
            serializer=lambda row: _serialize(row, db),
        )

    @router.get("")
    def list_items(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> list[dict[str, Any]]:
        stmt = select(model_cls)
        if hasattr(model_cls, "company_id") and current_user.company_id is not None:
            stmt = stmt.where(model_cls.company_id == current_user.company_id)
        rows = db.scalars(stmt).all()
        return [_serialize(r, db) for r in rows]

    @router.post("")
    def create_item(
        payload: dict[str, Any] = Body(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        obj = model_cls()
        apply_patch(obj, payload)
        if hasattr(obj, "company_id") and getattr(obj, "company_id", None) is None:
            obj.company_id = current_user.company_id
        if hasattr(obj, "company_settings_id") and getattr(obj, "company_settings_id", None) is None:
            obj.company_settings_id = _ensure_company_settings_id(current_user, db)
        if hasattr(obj, "created_by") and getattr(obj, "created_by", None) is None:
            obj.created_by = current_user.id
        if before_create is not None:
            before_create(obj, payload, current_user, db)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        if after_create is not None:
            after_create(obj, payload, current_user, db)
            db.commit()
            db.refresh(obj)
        return _serialize(obj, db)

    @router.get("/{item_id:int}")
    def get_item(
        item_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        obj = db.get(model_cls, item_id)
        if obj is None:
            raise CustomException(status_code=404, message=f"{model_cls.__name__} not found")
        if hasattr(obj, "company_id") and getattr(obj, "company_id", None) is not None:
            assert_company_access(current_user, obj, is_super_admin=is_super_admin(current_user, db))
        return _serialize(obj, db)

    @router.patch("/{item_id:int}")
    def patch_item(
        item_id: int,
        payload: dict[str, Any] = Body(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        obj = db.get(model_cls, item_id)
        if obj is None:
            raise CustomException(status_code=404, message=f"{model_cls.__name__} not found")
        if hasattr(obj, "company_id") and getattr(obj, "company_id", None) is not None:
            assert_company_access(current_user, obj, is_super_admin=is_super_admin(current_user, db))
        apply_patch(obj, payload)
        if hasattr(obj, "updated_by"):
            obj.updated_by = current_user.id
        if after_patch is not None:
            after_patch(obj, payload, current_user, db)
        db.commit()
        db.refresh(obj)
        return _serialize(obj, db)

    @router.delete("/{item_id:int}")
    def delete_item(
        item_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        obj = db.get(model_cls, item_id)
        if obj is None:
            raise CustomException(status_code=404, message=f"{model_cls.__name__} not found")
        if hasattr(obj, "company_id") and getattr(obj, "company_id", None) is not None:
            assert_company_access(current_user, obj, is_super_admin=is_super_admin(current_user, db))
        db.delete(obj)
        db.commit()
        return SuccessResponse(success=True, message="Deleted successfully").model_dump()

    return router
