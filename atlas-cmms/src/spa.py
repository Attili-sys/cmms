"""Client-side routes of the CMMS screens. Included last so /api and /healthz win."""

from fastapi import APIRouter

from src.schemas.errors import CustomException
from src.views import cmms_page

router = APIRouter()


@router.get("/{full_path:path}")
def screens(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        raise CustomException(status_code=404, message="API endpoint not found")
    return cmms_page(full_path)
