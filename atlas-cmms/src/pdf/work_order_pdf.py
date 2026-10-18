"""Work order PDF report generator (pure Python, valid %PDF-1.4 output)."""

from typing import Any


def _escape(text: Any) -> str:
    """Escape text for PDF literal strings."""
    if text is None:
        return ""
    s = str(text)
    s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return s.encode("latin-1", "replace").decode("latin-1")


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract property or dict key."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


STATUS_NAMES = {
    0: "OPEN",
    1: "ON_HOLD",
    2: "IN_PROGRESS",
    3: "COMPLETE",
}

PRIORITY_NAMES = {
    0: "NONE",
    1: "LOW",
    2: "MEDIUM",
    3: "HIGH",
}


def render_work_order_pdf(
    work_order: Any,
    company_name: str = "Atlas CMMS",
    tasks: list[Any] | None = None,
    labors: list[Any] | None = None,
) -> bytes:
    """Render a WorkOrder to valid %PDF-1.4 bytes without external native dependencies.

    Includes work order title, custom_id, status, priority, description, asset/location,
    tasks, labors, and signature block.
    """
    title = _get_val(work_order, "title", "Untitled Work Order")
    custom_id = _get_val(work_order, "custom_id", "N/A")
    raw_status = _get_val(work_order, "status", 0)
    status_str = STATUS_NAMES.get(raw_status, str(raw_status) if raw_status is not None else "OPEN")
    raw_priority = _get_val(work_order, "priority", 0)
    priority_str = PRIORITY_NAMES.get(raw_priority, str(raw_priority) if raw_priority is not None else "NONE")
    description = _get_val(work_order, "description", "") or ""

    asset = _get_val(work_order, "asset", None)
    asset_str = _get_val(asset, "name", None) if asset else None
    if not asset_str:
        asset_id = _get_val(work_order, "asset_id", None)
        asset_str = f"Asset #{asset_id}" if asset_id is not None else "None"

    location = _get_val(work_order, "location", None)
    location_str = _get_val(location, "name", None) if location else None
    if not location_str:
        location_id = _get_val(work_order, "location_id", None)
        location_str = f"Location #{location_id}" if location_id is not None else "None"

    due_date = _get_val(work_order, "due_date", None)
    due_date_str = str(due_date) if due_date else "Not set"

    estimated_duration = _get_val(work_order, "estimated_duration", None)
    duration_str = f"{estimated_duration} hours" if estimated_duration is not None else "N/A"

    ops: list[str] = []

    # Draw header line
    ops.append("0.5 w")
    ops.append("50 715 m 562 715 l S")

    # Company name and document title
    ops.append(f"BT /F2 16 Tf 50 740 Td ({_escape(company_name)}) Tj ET")
    ops.append("BT /F1 11 Tf 50 723 Td (WORK ORDER SUMMARY REPORT) Tj ET")

    # Work Order identifier & Title
    ops.append(f"BT /F2 12 Tf 50 690 Td (Work Order: {_escape(custom_id)}) Tj ET")
    ops.append(f"BT /F2 11 Tf 50 670 Td (Title:) Tj /F1 11 Tf 40 0 Td ({_escape(title)}) Tj ET")

    # Metadata Grid
    ops.append(f"BT /F2 10 Tf 50 645 Td (Status:) Tj /F1 10 Tf 45 0 Td ({_escape(status_str)}) Tj ET")
    ops.append(f"BT /F2 10 Tf 280 645 Td (Priority:) Tj /F1 10 Tf 50 0 Td ({_escape(priority_str)}) Tj ET")

    ops.append(f"BT /F2 10 Tf 50 625 Td (Asset:) Tj /F1 10 Tf 45 0 Td ({_escape(asset_str)}) Tj ET")
    ops.append(f"BT /F2 10 Tf 280 625 Td (Location:) Tj /F1 10 Tf 55 0 Td ({_escape(location_str)}) Tj ET")

    ops.append(f"BT /F2 10 Tf 50 605 Td (Due Date:) Tj /F1 10 Tf 60 0 Td ({_escape(due_date_str)}) Tj ET")
    ops.append(f"BT /F2 10 Tf 280 605 Td (Est. Duration:) Tj /F1 10 Tf 80 0 Td ({_escape(duration_str)}) Tj ET")

    # Description Section
    ops.append("50 590 m 562 590 l S")
    ops.append("BT /F2 10 Tf 50 575 Td (Description:) Tj ET")
    desc_lines = description.splitlines() if description else ["No description provided."]
    y = 558
    for line in desc_lines[:5]:
        ops.append(f"BT /F1 9 Tf 55 {y} Td ({_escape(line[:90])}) Tj ET")
        y -= 14

    # Tasks Section
    y -= 10
    ops.append(f"50 {y + 12} m 562 {y + 12} l S")
    ops.append(f"BT /F2 10 Tf 50 {y} Td (Tasks / Checklist:) Tj ET")
    y -= 16

    tasks_list = tasks or []
    if not tasks_list:
        ops.append(f"BT /F1 9 Tf 55 {y} Td (No checklist tasks attached.) Tj ET")
        y -= 16
    else:
        for idx, t in enumerate(tasks_list[:8], start=1):
            t_notes = _get_val(t, "notes", "") or ""
            t_val = _get_val(t, "value", "") or ""
            t_label = _get_val(t, "label", "") or _get_val(t, "name", "")
            summary = t_label or t_notes or (f"Task #{idx}" + (f": {t_val}" if t_val else ""))
            ops.append(f"BT /F1 9 Tf 55 {y} Td ([  ] {_escape(summary[:80])}) Tj ET")
            y -= 14

    # Labors Section
    labors_list = labors or []
    if labors_list:
        y -= 10
        ops.append(f"50 {y + 12} m 562 {y + 12} l S")
        ops.append(f"BT /F2 10 Tf 50 {y} Td (Labor Recorded:) Tj ET")
        y -= 16
        for l_item in labors_list[:5]:
            dur = _get_val(l_item, "duration", 0)
            rate = _get_val(l_item, "hourly_rate", 0)
            ops.append(f"BT /F1 9 Tf 55 {y} Td (- Duration: {dur} min, Rate: ${rate}/hr) Tj ET")
            y -= 14

    # Signature Block (anchored near bottom)
    ops.append("50 120 m 562 120 l S")
    ops.append("BT /F2 10 Tf 50 102 Td (Signature:) Tj /F1 10 Tf 60 0 Td (__________________________________________) Tj ET")
    ops.append(
        "BT /F2 10 Tf 50 80 Td (Date:) Tj /F1 10 Tf 35 0 Td (____________________) Tj "
        "/F2 10 Tf 140 0 Td (Technician Name:) Tj /F1 10 Tf 100 0 Td (____________________) Tj ET"
    )

    stream_content = "\n".join(ops)
    stream_bytes = stream_content.encode("latin-1")
    stream_length = len(stream_bytes)

    # Assemble PDF-1.4 file
    body = bytearray()
    body.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets: dict[int, int] = {}

    # Object 1: Catalog
    offsets[1] = len(body)
    body.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    # Object 2: Pages
    offsets[2] = len(body)
    body.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

    # Object 3: Page
    offsets[3] = len(body)
    body.extend(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n"
    )

    # Object 4: Contents Stream
    offsets[4] = len(body)
    body.extend(f"4 0 obj\n<< /Length {stream_length} >>\nstream\n".encode("latin-1"))
    body.extend(stream_bytes)
    body.extend(b"\nendstream\nendobj\n")

    # Object 5: Font F1 (Helvetica)
    offsets[5] = len(body)
    body.extend(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    # Object 6: Font F2 (Helvetica-Bold)
    offsets[6] = len(body)
    body.extend(b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")

    # xref table
    xref_offset = len(body)
    body.extend(b"xref\n0 7\n0000000000 65535 f \n")
    for i in range(1, 7):
        body.extend(f"{offsets[i]:010d} 00000 n \n".encode("latin-1"))

    # Trailer
    body.extend(
        f"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
    )

    return bytes(body)
