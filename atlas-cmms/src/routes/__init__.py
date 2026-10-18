"""Aggregate router combining all CMMS domain route modules."""

from fastapi import APIRouter

from src.routes.analytics import router as analytics_router
from src.routes.assets_locations import router as assets_locations_router
from src.routes.auth_users import router as auth_users_router
from src.routes.meters_requests_workflows_misc import router as misc_router
from src.routes.parts_po_tasks import router as parts_po_tasks_router
from src.routes.work_orders_pm import router as work_orders_pm_router

router = APIRouter()
router.include_router(auth_users_router)
router.include_router(assets_locations_router)
router.include_router(parts_po_tasks_router)
router.include_router(work_orders_pm_router)
router.include_router(misc_router)
router.include_router(analytics_router)

__all__ = ["router"]
