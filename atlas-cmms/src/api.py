"""JSON API router mounted under /api (and root-level legacy endpoints)."""

from fastapi import APIRouter

from src.routes import router as cmms_router

router = APIRouter()
router.include_router(cmms_router)
