"""Tests for WorkOrder PDF generator."""

from datetime import datetime, timezone

from src.models import WorkOrder
from src.pdf.work_order_pdf import render_work_order_pdf


def test_render_work_order_pdf_basic() -> None:
    wo = WorkOrder(
        id=101,
        custom_id="WO-101",
        title="Quarterly HVAC Filter Inspection",
        description="Inspect and replace filters in building B.",
        status=0,
        priority=3,
        estimated_duration=2.5,
        required_signature=True,
        company_id=1,
        asset_id=55,
        location_id=12,
        due_date=datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
        archived=False,
        is_demo=False,
    )

    tasks = [
        {"notes": "Check supply air filter", "value": "Done"},
        {"notes": "Check return fan belt", "value": "Pass"},
    ]
    labors = [
        {"duration": 120, "hourly_rate": 75},
    ]

    pdf_bytes = render_work_order_pdf(
        work_order=wo,
        company_name="Acme Maintenance Corp",
        tasks=tasks,
        labors=labors,
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_bytes.endswith(b"%%EOF\n")

    # Verify content strings exist within the PDF
    assert b"Acme Maintenance Corp" in pdf_bytes
    assert b"WO-101" in pdf_bytes
    assert b"Quarterly HVAC Filter Inspection" in pdf_bytes
    assert b"Inspect and replace filters in building B." in pdf_bytes
    assert b"Asset #55" in pdf_bytes
    assert b"Location #12" in pdf_bytes
    assert b"Check supply air filter" in pdf_bytes
    assert b"Signature:" in pdf_bytes
    assert b"Technician Name:" in pdf_bytes


def test_render_work_order_pdf_dict() -> None:
    wo_dict = {
        "custom_id": "WO-9999",
        "title": "Emergency Generator Repair",
        "description": "Generator unit failed to start during storm.",
        "status": 2,
        "priority": 3,
        "asset_id": 99,
        "location_id": 88,
    }

    pdf_bytes = render_work_order_pdf(work_order=wo_dict)

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"WO-9999" in pdf_bytes
    assert b"Emergency Generator Repair" in pdf_bytes
    assert b"Generator unit failed to start" in pdf_bytes
    assert b"IN_PROGRESS" in pdf_bytes
    assert b"HIGH" in pdf_bytes
    assert b"Signature:" in pdf_bytes
