"""Floor-plan drawing helpers: classify an uploaded File and render a PDF's first page to PNG."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Literal

from sqlalchemy.orm import Session

from src.models.files_custom import File
from src.schemas.errors import CustomException

MAX_PDF_PAGES = 50
MAX_RENDER_EDGE_PX = 4000
MAX_RENDER_SCALE = 4.0
MAX_PDF_BYTES = 25 * 1024 * 1024

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}

FileClass = Literal["image", "pdf", "other"]


def _storage_path(file: File) -> Path:
    # Reuse the upload endpoint's storage layout so downloads resolve the rendered file.
    from src.routes.meters_requests_workflows_misc import _get_upload_root, _sanitize_filename

    root = _get_upload_root(file.company_id)
    return (root / f"{file.id}_{_sanitize_filename(file.name or 'upload.bin')}").resolve()


def read_file_bytes(file: File, limit: int = MAX_PDF_BYTES + 1) -> bytes:
    path = _storage_path(file)
    if not path.is_file():
        raise CustomException(status_code=406, message="The uploaded file could not be found on disk")
    with path.open("rb") as fh:
        return fh.read(limit)


def _sniff(head: bytes) -> str | None:
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n") or head.startswith(b"\xff\xd8\xff"):
        return "image"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image"
    text = head.lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if (text.startswith(b"<?xml") or text.startswith(b"<svg")) and b"<svg" in text:
        return "image"
    return None


def classify_file(file: File) -> FileClass:
    """image / pdf / other, from the extension AND the leading bytes (never the extension alone)."""
    name = file.name or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext != "pdf" and ext not in IMAGE_EXTENSIONS:
        return "other"
    try:
        head = read_file_bytes(file, 2048)
    except (CustomException, OSError):
        return "other"
    return _sniff(head) or "other"  # type: ignore[return-value]


def render_pdf_first_page(db: Session, pdf_file: File, created_by: int | None = None) -> File:
    """Render page 1 of an uploaded PDF to a PNG (longest edge <= 4000 px) and return the new image File."""
    import pypdfium2 as pdfium

    from src.models.enums import FileType
    from src.routes.meters_requests_workflows_misc import (
        _get_upload_root,
        _resolve_file_type,
        _sanitize_filename,
    )

    data = read_file_bytes(pdf_file)
    if len(data) > MAX_PDF_BYTES:
        raise CustomException(status_code=406, message="PDF exceeds the 25 MB limit")
    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        if "password" in str(exc).lower():
            raise CustomException(
                status_code=406, message="Encrypted or password-protected PDFs are not supported"
            ) from exc
        raise CustomException(status_code=406, message="The PDF is unreadable or corrupt") from exc
    except Exception as exc:  # noqa: BLE001
        raise CustomException(status_code=406, message="The PDF is unreadable or corrupt") from exc
    try:
        pages = len(pdf)
        if pages < 1:
            raise CustomException(status_code=406, message="The PDF has no pages")
        if pages > MAX_PDF_PAGES:
            raise CustomException(
                status_code=406, message=f"The PDF has more than {MAX_PDF_PAGES} pages"
            )
        try:
            page = pdf[0]
            width, height = page.get_size()
            if width <= 0 or height <= 0:
                raise CustomException(status_code=406, message="The PDF page has no size")
            scale = min(MAX_RENDER_EDGE_PX / max(width, height), MAX_RENDER_SCALE)
            pil = page.render(scale=scale).to_pil().convert("RGB")
        except CustomException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise CustomException(status_code=406, message="The PDF could not be rendered") from exc
    finally:
        pdf.close()

    buf = io.BytesIO()
    pil.save(buf, format="PNG", optimize=True)
    stem = (pdf_file.name or "drawing").rsplit(".", 1)[0] or "drawing"
    name = f"{stem}.png"
    fe = File(
        name=name,
        path="",
        type=_resolve_file_type(FileType.IMAGE.value),
        hidden=False,
        company_id=pdf_file.company_id,
        created_by=created_by,
    )
    db.add(fe)
    db.flush()
    root = _get_upload_root(pdf_file.company_id)
    target = (root / f"{fe.id}_{_sanitize_filename(name)}").resolve()
    if not target.is_relative_to(root):
        raise CustomException(status_code=400, message="Invalid upload file name")
    target.write_bytes(buf.getvalue())
    fe.path = f"/api/files/download/{fe.id}"
    return fe
