"""Error schema and exception handlers matching Java's GlobalExceptionHandlerController / RestExceptionHandlerController."""

from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.schemas._base import CamelModel


class CustomException(Exception):
    """Application custom exception matching com.grash.exception.CustomException."""

    def __init__(
        self,
        status_code: int = 400,
        message: str = "",
        *,
        detail: str | None = None,
    ) -> None:
        # Flexible positional handling: CustomException(404, "Not Found") or CustomException("Not Found", 404)
        if isinstance(status_code, str) and isinstance(message, int):
            status_code, message = message, status_code
        self.status_code = status_code if isinstance(status_code, int) else 400
        self.message = detail or (message if isinstance(message, str) else str(message))
        super().__init__(self.message)


class ErrorResponse(CamelModel):
    """Standard error response payload."""

    success: bool = False
    message: str


class SuccessResponse(CamelModel):
    """Standard success response payload matching com.grash.dto.SuccessResponse."""

    success: bool = True
    message: str = ""


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers matching Java GlobalExceptionHandlerController."""

    @app.exception_handler(CustomException)
    async def custom_exception_handler(_request: Request, exc: CustomException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message, "success": False},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": detail, "success": False},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors: list[dict[str, Any]] = exc.errors()
        messages: list[str] = []
        for err in errors:
            loc = " -> ".join(str(item) for item in err.get("loc", []) if item != "body")
            msg = err.get("msg", "Validation error")
            if loc:
                messages.append(f"{loc}: {msg}")
            else:
                messages.append(msg)
        joined_message = ", ".join(messages) if messages else "Validation failed"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": joined_message, "success": False},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_request: Request, _exc: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"message": "Database integrity violation", "success": False},
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(_request: Request, exc: PermissionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": str(exc) or "Access is denied", "success": False},
        )
