"""Floor-plan drawings (PNG / PDF upload, revisions) and asset pins."""

from __future__ import annotations

from collections.abc import Iterator
import io

from fastapi.testclient import TestClient
from PIL import Image
import pytest
from reportlab.pdfgen import canvas as rl_canvas
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src import envs
from src.app import app
from src.deps.db import get_db
from src.models import (
    Base,
    Company,
    CompanySettings,
    FloorPlanPin,
    Location,
    Role,
    User,
    WorkOrder,
)
from src.models.associations import role_view_other_permissions, role_view_permissions
from src.models.enums import PermissionEntity

B_HEADERS = {"X-authentik-email": "admin@tenant-b.local", "X-authentik-name": "Tenant B Admin"}
VIEWER_HEADERS = {"X-authentik-email": "viewer@tenant-a.local", "X-authentik-name": "Viewer"}


def _png(width: int = 400, height: int = 200) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (240, 240, 240)).save(buf, format="PNG")
    return buf.getvalue()


def _pdf(pages: int = 1, encrypt: str | None = None) -> bytes:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(842, 595), encrypt=encrypt)
    for i in range(pages):
        c.drawString(100, 300, f"Floor plan page {i + 1}")
        c.rect(50, 50, 700, 450)
        c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture(scope="module")
def env(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    mp = pytest.MonkeyPatch()
    mp.setattr(envs, "DATA_DIR", tmp_path_factory.mktemp("data"))
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override() -> Iterator[Session]:
        with session_local() as db:
            yield db

    app.dependency_overrides[get_db] = _override
    try:
        with TestClient(
            app,
            headers={"X-authentik-email": "admin@tenant-a.local", "X-authentik-name": "Admin A"},
        ) as client:
            me = client.get("/api/auth/me")
            assert me.status_code == 200
            company_a = me.json()["companyId"]
            with session_local() as db:
                cs_b = CompanySettings()
                db.add(cs_b)
                db.flush()
                comp_b = Company(name="Tenant B Corp", company_settings_id=cs_b.id)
                db.add(comp_b)
                db.flush()
                cs_b.company_id = comp_b.id
                cs_a_id = db.get(Company, company_a).company_settings_id
                perms = list(PermissionEntity)
                view_only = Role(
                    name="View Only", company_settings_id=cs_a_id, role_type=1, code=3, paid=True
                )
                db.add(view_only)
                db.flush()
                for ent in (PermissionEntity.LOCATIONS, PermissionEntity.ASSETS):
                    idx = perms.index(ent)
                    db.execute(role_view_permissions.insert().values(role_id=view_only.id, view_permissions=idx))
                    db.execute(
                        role_view_other_permissions.insert().values(
                            role_id=view_only.id, view_other_permissions=idx
                        )
                    )
                role_b = Role(
                    name="B Admin", company_settings_id=cs_b.id, role_type=1, code=4, paid=True
                )
                db.add(role_b)
                db.flush()
                for ent in (PermissionEntity.LOCATIONS, PermissionEntity.ASSETS):
                    idx = perms.index(ent)
                    db.execute(role_view_permissions.insert().values(role_id=role_b.id, view_permissions=idx))
                    db.execute(
                        role_view_other_permissions.insert().values(
                            role_id=role_b.id, view_other_permissions=idx
                        )
                    )
                for email, cid, rid, owns in (
                    ("viewer@tenant-a.local", company_a, view_only.id, False),
                    ("admin@tenant-b.local", comp_b.id, role_b.id, True),
                ):
                    db.add(
                        User(
                            email=email, username=email, first_name="T", last_name="U",
                            password="x", company_id=cid, role_id=rid, enabled=True,
                            enabled_in_subscription=True, created_via_sso=True,
                            owns_company=owns, rate=0,
                        )
                    )
                loc_b = Location(name="B Site", company_id=comp_b.id)
                db.add(loc_b)
                db.commit()
                loc_b_id = loc_b.id
            yield {
                "client": client,
                "session_local": session_local,
                "engine": engine,
                "company_a": company_a,
                "loc_b": loc_b_id,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        mp.undo()


def _upload(client: TestClient, name: str, data: bytes, headers: dict | None = None) -> dict:
    r = client.post(
        "/api/files/upload",
        data={"folder": "floorplans", "type": "OTHER"},
        files=[("files", (name, io.BytesIO(data), "application/octet-stream"))],
        headers=headers or {},
    )
    assert r.status_code == 200, r.text
    return r.json()[0]


def _location(client: TestClient, name: str, parent: int | None = None) -> int:
    body: dict = {"name": name, "address": "x"}
    if parent is not None:
        body["parentLocation"] = {"id": parent}
    r = client.post("/api/locations", json=body)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _asset(client: TestClient, name: str, location_id: int | None) -> int:
    body: dict = {"name": name}
    if location_id is not None:
        body["location"] = {"id": location_id}
    r = client.post("/api/assets", json=body)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _plan(client: TestClient, location_id: int, name: str = "Ground", **extra) -> dict:
    png = _upload(client, f"{name}.png", _png())
    body = {"name": name, "area": 10, "locationId": location_id, "file": {"id": png["id"]}, **extra}
    r = client.post("/api/floor-plans", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_create_plan_legacy_frontend_shape(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Legacy site")
    png = _upload(client, "legacy.png", _png())
    # Exactly what slices/floorPlan.ts posts: values (name, area?, image) + location:{id}
    r = client.post(
        "/api/floor-plans",
        json={"name": "Legacy", "area": 5, "image": {"id": png["id"]}, "location": {"id": loc}},
    )
    assert r.status_code == 200, r.text
    dto = r.json()
    assert dto["name"] == "Legacy"
    assert dto["image"]["id"] == png["id"]
    assert dto["sourceFile"] is None
    assert dto["current"] is True
    assert dto["kind"] is None
    assert dto["createdAt"]
    # without an image and area is also accepted (image was optional before)
    r2 = client.post("/api/floor-plans", json={"name": "Bare", "location": {"id": loc}})
    assert r2.status_code == 200, r2.text
    assert r2.json()["image"] is None


def test_create_plan_png_with_metadata_and_list(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Meta site")
    dto = _plan(client, loc, "MEP L1", kind="MEP", revision="A", note="first issue")
    assert (dto["kind"], dto["revision"], dto["note"]) == ("MEP", "A", "first issue")
    assert dto["pinCount"] == 0
    listed = client.get(f"/api/floor-plans/location/{loc}").json()
    assert [p["id"] for p in listed] == [dto["id"]]
    assert listed[0]["image"]["url"].startswith("/api/files/download/")
    bad = client.post(
        "/api/floor-plans",
        json={"name": "x", "locationId": loc, "kind": "NOPE"},
    )
    assert bad.status_code == 406


def test_create_plan_from_pdf_renders_png(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "PDF site")
    pdf = _upload(client, "plan.pdf", _pdf())
    r = client.post(
        "/api/floor-plans",
        json={"name": "From PDF", "area": 1, "locationId": loc, "file": {"id": pdf["id"]}},
    )
    assert r.status_code == 200, r.text
    dto = r.json()
    assert dto["sourceFile"]["id"] == pdf["id"]
    assert dto["sourceFile"]["name"] == "plan.pdf"
    assert dto["image"]["id"] != pdf["id"]
    assert dto["image"]["name"].endswith(".png")
    content = client.get(dto["image"]["url"]).content
    assert content.startswith(b"\x89PNG")
    width, height = Image.open(io.BytesIO(content)).size
    assert max(width, height) <= 4000 and width > height  # landscape page


def test_create_plan_rejects_bad_files(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Reject site")
    cases = {
        "encrypted.pdf": _pdf(encrypt="secret"),
        "garbage.pdf": b"this is not a pdf at all",
        "many.pdf": _pdf(pages=51),
        "tool.exe": b"MZ\x90\x00 fake executable",
        "disguised.png": b"MZ\x90\x00 fake executable",
        "notes.txt": b"hello",
    }
    for name, data in cases.items():
        f = _upload(client, name, data)
        r = client.post(
            "/api/floor-plans",
            json={"name": name, "locationId": loc, "file": {"id": f["id"]}},
        )
        assert r.status_code == 406, (name, r.status_code, r.text)
    assert client.get(f"/api/floor-plans/location/{loc}").json() == []


def test_revision_chain_copies_pins_and_blocks_old_writes(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Rev site")
    a1 = _asset(client, "Pump 1", loc)
    a2 = _asset(client, "Pump 2", loc)
    old = _plan(client, loc, "Level 1", kind="ARCHITECTURAL", revision="A")
    for aid, xy in ((a1, (0.1, 0.2)), (a2, (0.9, 0.8))):
        r = client.put(f"/api/floor-plans/{old['id']}/pins/{aid}", json={"x": xy[0], "y": xy[1]})
        assert r.status_code == 200, r.text
    new = _plan(client, loc, "Level 1", kind="ARCHITECTURAL", revision="B")
    assert new["current"] is True and new["pinCount"] == 2
    current = client.get(f"/api/floor-plans/location/{loc}").json()
    assert [p["id"] for p in current] == [new["id"]]
    both = client.get(f"/api/floor-plans/location/{loc}?includeSuperseded=true").json()
    by_id = {p["id"]: p for p in both}
    assert by_id[old["id"]]["current"] is False
    assert by_id[old["id"]]["supersededById"] == new["id"]
    pins = {p["asset"]["id"]: (p["x"], p["y"]) for p in client.get(f"/api/floor-plans/{new['id']}/pins").json()}
    assert pins == {a1: (0.1, 0.2), a2: (0.9, 0.8)}
    # pins on the old revision are read-only
    r = client.put(f"/api/floor-plans/{old['id']}/pins/{a1}", json={"x": 0.5, "y": 0.5})
    assert r.status_code == 406 and "superseded" in r.text
    assert client.get(f"/api/floor-plans/{old['id']}/pins").status_code == 200
    # different kind with the same name is NOT a new revision
    other = _plan(client, loc, "Level 1", kind="MEP")
    assert other["current"] is True
    assert client.get(f"/api/floor-plans/location/{loc}").json().__len__() == 2
    # deleting the newest revision restores the previous one and removes its pins
    assert client.delete(f"/api/floor-plans/{new['id']}").status_code == 200
    with env["session_local"]() as db:
        assert db.scalars(select(FloorPlanPin).where(FloorPlanPin.floor_plan_id == new["id"])).all() == []
    ids = {p["id"] for p in client.get(f"/api/floor-plans/location/{loc}").json()}
    assert old["id"] in ids


def test_pin_upsert_move_delete_and_validation(env: dict) -> None:
    client = env["client"]
    site = _location(client, "Site")
    floor = _location(client, "Floor 2", site)
    other = _location(client, "Other site")
    plan = _plan(client, site, "Site plan")
    inside = _asset(client, "Chiller", floor)  # descendant of the plan's location
    outside = _asset(client, "Outsider", other)
    nowhere = _asset(client, "Unplaced", None)
    url = f"/api/floor-plans/{plan['id']}/pins/{inside}"

    r = client.put(url, json={"x": 0.25, "y": 0.75})
    assert r.status_code == 200, r.text
    pin = r.json()
    assert (pin["x"], pin["y"]) == (0.25, 0.75) and pin["asset"]["name"] == "Chiller"
    moved = client.put(url, json={"x": 0.5, "y": 0.5}).json()
    assert moved["id"] == pin["id"] and (moved["x"], moved["y"]) == (0.5, 0.5)
    assert client.get(f"/api/floor-plans/location/{site}").json()[0]["pinCount"] == 1

    for bad in ({"x": 1.01, "y": 0.5}, {"x": -0.1, "y": 0.5}, {"x": 0.5}, {"x": "a", "y": 0.1}, {"x": True, "y": 0}):
        assert client.put(url, json=bad).status_code == 406, bad
    for aid in (outside, nowhere):
        r = client.put(f"/api/floor-plans/{plan['id']}/pins/{aid}", json={"x": 0.1, "y": 0.1})
        assert r.status_code == 406, r.text
    assert client.put(f"/api/floor-plans/{plan['id']}/pins/99999999", json={"x": 0.1, "y": 0.1}).status_code == 404
    assert client.put("/api/floor-plans/99999999/pins/1", json={"x": 0.1, "y": 0.1}).status_code == 404

    assert client.delete(url).json() == {"success": True}
    assert client.get(f"/api/floor-plans/{plan['id']}/pins").json() == []


def test_asset_location_change_prunes_pins_and_delete_cascades(env: dict) -> None:
    client = env["client"]
    site = _location(client, "Move site")
    floor_a = _location(client, "Move floor A", site)
    floor_b = _location(client, "Move floor B", site)
    elsewhere = _location(client, "Move elsewhere")
    plan_site = _plan(client, site, "Site drawing")
    plan_a = _plan(client, floor_a, "Floor A drawing")
    aid = _asset(client, "Mover", floor_a)
    for plan in (plan_site, plan_a):
        assert client.put(f"/api/floor-plans/{plan['id']}/pins/{aid}", json={"x": 0.3, "y": 0.3}).status_code == 200
    assert len(client.get(f"/api/assets/{aid}/floor-plan-pins").json()) == 2

    # floor A -> floor B: still inside the site drawing, no longer on floor A's drawing
    r = client.patch(f"/api/assets/{aid}", json={"location": {"id": floor_b}})
    assert r.status_code == 200, r.text
    remaining = client.get(f"/api/assets/{aid}/floor-plan-pins").json()
    assert [p["floorPlan"]["id"] for p in remaining] == [plan_site["id"]]
    assert remaining[0]["floorPlan"]["locationId"] == site

    # leaving the site removes the rest
    assert client.patch(f"/api/assets/{aid}", json={"location": {"id": elsewhere}}).status_code == 200
    assert client.get(f"/api/assets/{aid}/floor-plan-pins").json() == []

    # delete cascades
    back = _asset(client, "Doomed", floor_a)
    assert client.put(f"/api/floor-plans/{plan_a['id']}/pins/{back}", json={"x": 0.1, "y": 0.1}).status_code == 200
    assert client.delete(f"/api/assets/{back}").status_code == 200
    with env["session_local"]() as db:
        assert db.scalars(select(FloorPlanPin).where(FloorPlanPin.asset_id == back)).all() == []
    assert client.get(f"/api/floor-plans/{plan_a['id']}/pins").json() == []


def test_asset_pins_only_current_plans(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Current site")
    aid = _asset(client, "Fan", loc)
    old = _plan(client, loc, "Roof", kind="OTHER")
    client.put(f"/api/floor-plans/{old['id']}/pins/{aid}", json={"x": 0.4, "y": 0.6})
    new = _plan(client, loc, "Roof", kind="OTHER", revision="2")
    rows = client.get(f"/api/assets/{aid}/floor-plan-pins").json()
    assert len(rows) == 1
    assert rows[0]["floorPlan"] == {
        "id": new["id"], "name": "Roof", "kind": "OTHER", "revision": "2", "locationId": loc,
    }
    assert (rows[0]["x"], rows[0]["y"]) == (0.4, 0.6)


def test_pinnable_assets(env: dict) -> None:
    client = env["client"]
    site = _location(client, "Pinnable site")
    floor = _location(client, "Pinnable floor", site)
    plan = _plan(client, site, "P")
    a1 = _asset(client, "Boiler Alpha", site)
    a2 = _asset(client, "Boiler Beta", floor)
    _asset(client, "Elsewhere boiler", _location(client, "Pinnable other"))
    archived = _asset(client, "Boiler Archived", site)
    assert client.patch(f"/api/assets/{archived}", json={"archived": True}).status_code == 200
    client.put(f"/api/floor-plans/{plan['id']}/pins/{a1}", json={"x": 0.1, "y": 0.1})

    names = [a["name"] for a in client.get(f"/api/floor-plans/{plan['id']}/pinnable-assets").json()]
    assert names == ["Boiler Beta"]
    res = client.get(f"/api/floor-plans/{plan['id']}/pinnable-assets?search=BETA").json()
    assert [a["id"] for a in res] == [a2] and set(res[0]) == {"id", "name", "customId", "status"}
    assert client.get(f"/api/floor-plans/{plan['id']}/pinnable-assets?search=zzz").json() == []

    for i in range(55):
        _asset(client, f"Bulk {i:02d}", site)
    assert len(client.get(f"/api/floor-plans/{plan['id']}/pinnable-assets").json()) == 50


def test_pins_open_work_orders_and_constant_query_count(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "WO site")
    plan = _plan(client, loc, "WO plan")
    assets = [_asset(client, f"Unit {i:02d}", loc) for i in range(30)]

    with env["session_local"]() as db:
        def wo(asset_id: int, status: int, archived: bool = False) -> None:
            db.add(
                WorkOrder(
                    title="t", asset_id=asset_id, status=status, archived=archived,
                    company_id=env["company_a"], estimated_duration=0.0, required_signature=False,
                )
            )

        wo(assets[0], 0)  # OPEN
        wo(assets[0], 1)  # IN_PROGRESS
        wo(assets[0], 2)  # ON_HOLD
        wo(assets[0], 3)  # COMPLETE -> not counted
        wo(assets[0], 0, archived=True)  # archived -> not counted
        wo(assets[1], 3)
        db.commit()

    counts: list[int] = []

    def _count(fn) -> None:
        n = 0

        def _hook(*_a) -> None:
            nonlocal n
            n += 1

        event.listen(env["engine"], "before_cursor_execute", _hook)
        try:
            fn()
        finally:
            event.remove(env["engine"], "before_cursor_execute", _hook)
        counts.append(n)

    def _get() -> None:
        r = client.get(f"/api/floor-plans/{plan['id']}/pins")
        assert r.status_code == 200
        _get.last = r.json()  # type: ignore[attr-defined]

    client.put(f"/api/floor-plans/{plan['id']}/pins/{assets[0]}", json={"x": 0.1, "y": 0.1})
    _count(_get)
    one = _get.last  # type: ignore[attr-defined]
    for aid in assets[1:]:
        assert client.put(f"/api/floor-plans/{plan['id']}/pins/{aid}", json={"x": 0.2, "y": 0.2}).status_code == 200
    _count(_get)
    many = _get.last  # type: ignore[attr-defined]

    assert len(one) == 1 and len(many) == 30
    assert one[0]["asset"]["openWorkOrders"] == 3
    by_asset = {p["asset"]["id"]: p["asset"] for p in many}
    assert by_asset[assets[0]]["openWorkOrders"] == 3
    assert by_asset[assets[1]]["openWorkOrders"] == 0
    assert set(by_asset[assets[2]]) == {"id", "name", "customId", "status", "image", "openWorkOrders"}
    assert counts[0] == counts[1], counts


def test_cross_tenant_reads_and_writes_denied(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Tenant A site")
    plan = _plan(client, loc, "Secret plan")
    aid = _asset(client, "Secret asset", loc)
    client.put(f"/api/floor-plans/{plan['id']}/pins/{aid}", json={"x": 0.1, "y": 0.1})
    pid = plan["id"]
    png = _upload(client, "x.png", _png())
    b = B_HEADERS

    def denied(r) -> None:
        assert r.status_code in (403, 404), (r.request.method, r.request.url, r.status_code, r.text)

    denied(client.get(f"/api/floor-plans/location/{loc}", headers=b))
    denied(client.get(f"/api/floor-plans/{pid}/pins", headers=b))
    denied(client.get(f"/api/floor-plans/{pid}/pinnable-assets", headers=b))
    denied(client.put(f"/api/floor-plans/{pid}/pins/{aid}", json={"x": 0.9, "y": 0.9}, headers=b))
    denied(client.delete(f"/api/floor-plans/{pid}/pins/{aid}", headers=b))
    denied(client.get(f"/api/assets/{aid}/floor-plan-pins", headers=b))
    denied(client.get(f"/api/floor-plans/{pid}", headers=b))
    # generic CRUD write path
    denied(client.post("/api/floor-plans", json={"name": "evil", "locationId": loc}, headers=b))
    denied(client.post("/api/floor-plans", json={"name": "evil", "location": {"id": loc}, "image": {"id": png["id"]}}, headers=b))
    denied(client.patch(f"/api/floor-plans/{pid}", json={"name": "pwned"}, headers=b))
    denied(client.patch(f"/api/floor-plans/{pid}", json={"location": {"id": env["loc_b"]}}, headers=b))
    denied(client.delete(f"/api/floor-plans/{pid}", headers=b))
    # tenant A writing into tenant B's location, or using B's pin target
    denied(client.post("/api/floor-plans", json={"name": "evil", "locationId": env["loc_b"]}))
    # list endpoints never leak A's plan to B
    for resp in (
        client.get("/api/floor-plans", headers=b),
        client.post("/api/floor-plans/search", json={}, headers=b),
    ):
        assert resp.status_code == 200
        assert "Secret plan" not in resp.text
    # nothing changed
    still = client.get(f"/api/floor-plans/location/{loc}").json()
    assert [p["name"] for p in still] == ["Secret plan"]
    assert len(client.get(f"/api/floor-plans/{pid}/pins").json()) == 1
    # tenant A can still see it in its own lists
    assert "Secret plan" in client.get("/api/floor-plans").text


def test_view_only_user_cannot_write(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Perm site")
    plan = _plan(client, loc, "Perm plan")
    aid = _asset(client, "Perm asset", loc)
    v = VIEWER_HEADERS
    assert client.get(f"/api/floor-plans/{plan['id']}/pins", headers=v).status_code == 200
    assert client.get(f"/api/floor-plans/location/{loc}", headers=v).status_code == 200
    assert client.put(f"/api/floor-plans/{plan['id']}/pins/{aid}", json={"x": 0.1, "y": 0.1}, headers=v).status_code == 403
    assert client.delete(f"/api/floor-plans/{plan['id']}/pins/{aid}", headers=v).status_code == 403
    assert client.patch(f"/api/floor-plans/{plan['id']}", json={"name": "n"}, headers=v).status_code == 403
    assert client.delete(f"/api/floor-plans/{plan['id']}", headers=v).status_code == 403
    assert client.post("/api/floor-plans", json={"name": "n", "locationId": loc}, headers=v).status_code == 403


def test_patch_cannot_tamper_with_revision_fields(env: dict) -> None:
    client = env["client"]
    loc = _location(client, "Patch site")
    plan = _plan(client, loc, "Patchable")
    r = client.patch(
        f"/api/floor-plans/{plan['id']}",
        json={"note": "updated", "kind": "SECURITY", "supersededById": 12345, "sourceFileId": 7},
    )
    assert r.status_code == 200, r.text
    dto = r.json()
    assert dto["note"] == "updated" and dto["kind"] == "SECURITY"
    assert dto["current"] is True and dto["sourceFile"] is None
    assert client.patch(f"/api/floor-plans/{plan['id']}", json={"kind": "BAD"}).status_code == 406
