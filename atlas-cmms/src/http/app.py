"""HTTP application export matching src.app:app with registered exception handlers."""

from src.app import app
from src.schemas.errors import register_exception_handlers

register_exception_handlers(app)

__all__ = ["app"]
