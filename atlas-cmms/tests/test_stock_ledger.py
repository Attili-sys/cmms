"""Stock ledger: every quantity change is one part_transaction row (plan 02 §1A, §3)."""

from __future__ import annotations

from collections.abc import Iterator
import random

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.deps.db import get_db
from src.models import Base, Company, CompanySettings, Role, User
from src.models.associations import role_view_other_permissions, role_view_permissions
from src.models.enums import MovementType, PermissionEntity, PurchaseOrderAction
from src.models.parts_po import Part, PartQuantity, PartTransaction, PurchaseOrder
from src.models.workflows import WorkflowAction
from src.services.workflow_engine import _apply_po_action

ADMIN_A = {"X-authentik-email": "admin@stock-a.local", "X-authentik-name": "Stock Admin"}
VIEWER_A = {"X-authentik-email": "viewer@stock-a.local", "X-authentik-name": "Stock Viewer"}
ADMIN_B = {"X-authentik-email": "admin@stock-b.local", "X-authentik-name": "Other Tenant"}


@pytest.fixture(scope="module")
def env() -> Iterator[dict]:
    """Tenant A (admin + parts viewer) and tenant B (its own administrator) on an in-memory database."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_db() -> Iterator[Session]:
        with session_local() as db:
            yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, headers=ADMIN_A) as admin:
            me = admin.get("/api/auth/me").json()
            company_a_id = me["companyId"]
            with session_local() as db:
                cs_b = CompanySettings()
                db.add(cs_b)
                db.flush()
                comp_b = Company(name="Stock Tenant B", company_settings_id=cs_b.id)
                db.add(comp_b)
                db.flush()
                cs_b.company_id = comp_b.id
                admin_role = db.scalar(select(Role).where(Role.name == "Administrator"))
                viewer_role = Role(
                    name="Parts Viewer",
                    company_settings_id=db.get(Company, company_a_id).company_settings_id,
                    role_type=1,
                    code=2,
                    paid=True,
                )
                db.add(viewer_role)
                db.flush()
                parts_ord = list(PermissionEntity).index(PermissionEntity.PARTS_AND_MULTIPARTS)
                db.execute(
                    role_view_permissions.insert().values(
                        role_id=viewer_role.id, view_permissions=parts_ord
                    )
                )
                db.execute(
                    role_view_other_permissions.insert().values(
                        role_id=viewer_role.id, view_other_permissions=parts_ord
                    )
                )
                common = {
                    "password": "hashed",
                    "enabled": True,
                    "enabled_in_subscription": True,
                    "created_via_sso": True,
                    "rate": 0,
                }
                db.add_all(
                    [
                        User(
                            email=VIEWER_A["X-authentik-email"],
                            username=VIEWER_A["X-authentik-email"],
                            first_name="Stock",
                            last_name="Viewer",
                            company_id=company_a_id,
                            role_id=viewer_role.id,
                            owns_company=False,
                            **common,
                        ),
                        User(
                            email=ADMIN_B["X-authentik-email"],
                            username=ADMIN_B["X-authentik-email"],
                            first_name="Other",
                            last_name="Tenant",
                            company_id=comp_b.id,
                            role_id=admin_role.id,
                            owns_company=True,
                            **common,
                        ),
                    ]
                )
                db.commit()
                company_b_id = comp_b.id
            with TestClient(app, headers=ADMIN_B) as admin_b, TestClient(
                app, headers=VIEWER_A
            ) as viewer:
                wo = admin.post("/api/work-orders", json={"title": "Stock WO"})
                assert wo.status_code == 200, wo.text
                yield {
                    "admin": admin,
                    "admin_b": admin_b,
                    "viewer": viewer,
                    "session_local": session_local,
                    "company_a_id": company_a_id,
                    "company_b_id": company_b_id,
                    "user_id": me["id"],
                    "wo_id": wo.json()["id"],
                }
    finally:
        app.dependency_overrides.pop(get_db, None)


def _part(client: TestClient, name: str, quantity: float = 0, **extra) -> dict:
    resp = client.post(
        "/api/parts", json={"name": name, "cost": 10.0, "quantity": quantity, **extra}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _rows(env: dict, part_id: int) -> list[PartTransaction]:
    """Ledger rows oldest first."""
    with env["session_local"]() as db:
        return list(
            db.scalars(
                select(PartTransaction)
                .where(PartTransaction.part_id == part_id)
                .order_by(PartTransaction.created_at, PartTransaction.id)
            )
        )


def _quantity(env: dict, part_id: int) -> float:
    with env["session_local"]() as db:
        return db.get(Part, part_id).quantity


def _assert_ledger_explains_quantity(env: dict, part_id: int) -> None:
    rows = _rows(env, part_id)
    quantity = _quantity(env, part_id)
    balance = 0.0
    for r in rows:
        balance += r.change
        assert r.balance_after == balance, (r.movement_type, r.change, r.balance_after)
    assert sum(r.change for r in rows) == quantity
    if rows:
        assert rows[-1].balance_after == quantity


def test_create_with_quantity_writes_opening(env: dict) -> None:
    part = _part(env["admin"], "Opening Part", 12)
    assert part["quantity"] == 12
    rows = _rows(env, part["id"])
    assert [(r.movement_type, r.change, r.balance_after, r.reason) for r in rows] == [
        ("OPENING", 12, 12, "Initial quantity")
    ]
    assert rows[0].created_by == env["user_id"]
    assert _rows(env, _part(env["admin"], "Empty Part", 0)["id"]) == []


def test_receive_issue_count_happy_paths(env: dict) -> None:
    admin = env["admin"]
    part = _part(admin, "Happy Part", 5)
    pid = part["id"]

    rec = admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 10, "reason": "Delivery", "unitCost": 4.5})
    assert rec.status_code == 200, rec.text
    assert rec.json()["quantity"] == 15
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.unit_cost, last.reason) == (
        "RECEIPT", 10, 15, 4.5, "Delivery"
    )

    iss = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 4, "reason": "Shop use"})
    assert iss.status_code == 200, iss.text
    assert iss.json()["quantity"] == 11
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.unit_cost) == ("ISSUE", -4, 11, 10.0)

    iss_wo = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1, "workOrderId": env["wo_id"]})
    assert iss_wo.status_code == 200, iss_wo.text
    assert _rows(env, pid)[-1].work_order_id == env["wo_id"]

    cnt = admin.post(f"/api/parts/{pid}/stock/count", json={"counted": 7, "reason": "Shelf count"})
    assert cnt.status_code == 200, cnt.text
    assert cnt.json()["quantity"] == 7
    assert cnt.json()["variance"] == -3
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after) == ("COUNT_LOSS", -3, 7)

    gain = admin.post(f"/api/parts/{pid}/stock/count", json={"counted": 9, "reason": "Found two"})
    assert gain.json()["variance"] == 2
    assert _rows(env, pid)[-1].movement_type == "COUNT_GAIN"
    _assert_ledger_explains_quantity(env, pid)


def test_receive_against_purchase_order(env: dict) -> None:
    admin = env["admin"]
    pid = _part(admin, "PO Receive Part")["id"]
    po = admin.post("/api/purchase-orders", json={"name": "PO-RECV-1"}).json()
    resp = admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 3, "purchaseOrderId": po["id"]})
    assert resp.status_code == 200, resp.text
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.purchase_order_id) == ("PO_RECEIPT", po["id"])


def test_validation_errors(env: dict) -> None:
    admin = env["admin"]
    pid = _part(admin, "Validation Part", 5)["id"]
    before = len(_rows(env, pid))

    no_reason = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1})
    assert no_reason.status_code == 406
    blank_reason = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1, "reason": "  "})
    assert blank_reason.status_code == 406

    too_many = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 6, "reason": "x"})
    assert too_many.status_code == 406
    assert too_many.json()["message"] == "Insufficient stock for part Validation Part"

    assert admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 0}).status_code == 400
    assert admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 1, "unitCost": -1}).status_code == 400
    assert admin.post(f"/api/parts/{pid}/stock/count", json={"counted": -1}).status_code == 400

    same = admin.post(f"/api/parts/{pid}/stock/count", json={"counted": 5})
    assert same.status_code == 200
    assert same.json()["variance"] == 0

    no_count_reason = admin.post(f"/api/parts/{pid}/stock/count", json={"counted": 4})
    assert no_count_reason.status_code == 406

    assert len(_rows(env, pid)) == before
    assert _quantity(env, pid) == 5
    assert admin.post("/api/parts/999999/stock/receive", json={"quantity": 1}).status_code == 404


def test_viewer_cannot_change_stock_but_can_read_movements(env: dict) -> None:
    pid = _part(env["admin"], "Viewer Part", 5)["id"]
    viewer = env["viewer"]
    assert viewer.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 1}).status_code == 403
    assert viewer.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1, "reason": "x"}).status_code == 403
    assert viewer.post(f"/api/parts/{pid}/stock/count", json={"counted": 1, "reason": "x"}).status_code == 403
    listed = viewer.get(f"/api/parts/{pid}/stock/movements")
    assert listed.status_code == 200
    assert listed.json()["totalElements"] == 1


def test_non_stock_parts(env: dict) -> None:
    admin = env["admin"]
    part = _part(admin, "Consumable Rag", 0, nonStock=True)
    pid = part["id"]
    msg = "Stock actions are not available for non-stock parts"
    for path, body in (
        ("receive", {"quantity": 1}),
        ("issue", {"quantity": 1, "reason": "x"}),
        ("count", {"counted": 1, "reason": "x"}),
    ):
        resp = admin.post(f"/api/parts/{pid}/stock/{path}", json=body)
        assert resp.status_code == 406, path
        assert resp.json()["message"] == msg
    assert admin.patch(f"/api/parts/{pid}/restock", json={"quantity": 1}).status_code == 406

    # WO consumption of a non-stock part still writes a row, with no balance.
    pq = admin.post(
        "/api/part-quantities",
        json={"part": {"id": pid}, "workOrder": {"id": env["wo_id"]}, "quantity": 3},
    )
    assert pq.status_code == 200, pq.text
    rows = _rows(env, pid)
    assert [(r.movement_type, r.change, r.balance_after) for r in rows] == [
        ("WO_CONSUMPTION", -3, None)
    ]
    assert _quantity(env, pid) == 0


def test_wo_part_lines_consume_and_return(env: dict) -> None:
    admin = env["admin"]
    wo_id = env["wo_id"]
    pid = _part(admin, "WO Line Part", 10)["id"]

    pq = admin.post(
        "/api/part-quantities",
        json={"part": {"id": pid}, "workOrder": {"id": wo_id}, "quantity": 4},
    ).json()
    assert _quantity(env, pid) == 6
    assert admin.patch(f"/api/part-quantities/{pq['id']}", json={"quantity": 1}).status_code == 200
    assert _quantity(env, pid) == 9
    assert admin.delete(f"/api/part-quantities/{pq['id']}").status_code == 200
    assert _quantity(env, pid) == 10

    rows = _rows(env, pid)
    assert [(r.movement_type, r.change, r.work_order_id) for r in rows[1:]] == [
        ("WO_CONSUMPTION", -4, wo_id),
        ("WO_RETURN", 3, wo_id),
        ("WO_RETURN", 1, wo_id),
    ]
    assert rows[1].description == "PART_CONSUMPTION"

    # The bulk WO endpoint goes through the same helper.
    wo2 = admin.post("/api/work-orders", json={"title": "Bulk WO"}).json()["id"]
    assert admin.patch(f"/api/part-quantities/work-order/{wo2}", json=[{"part": {"id": pid}, "quantity": 5}]).status_code == 200
    assert admin.patch(f"/api/part-quantities/work-order/{wo2}", json=[{"part": {"id": pid}, "quantity": 2}]).status_code == 200
    assert admin.patch(f"/api/part-quantities/work-order/{wo2}", json=[]).status_code == 200
    assert [r.movement_type for r in _rows(env, pid)[4:]] == ["WO_CONSUMPTION", "WO_RETURN", "WO_RETURN"]
    assert _quantity(env, pid) == 10
    _assert_ledger_explains_quantity(env, pid)


def test_purchase_order_approve_and_unapprove(env: dict) -> None:
    admin = env["admin"]
    pid = _part(admin, "PO Part", 2)["id"]
    po = admin.post("/api/purchase-orders", json={"name": "PO-LEDGER-1"}).json()
    admin.patch(f"/api/part-quantities/purchase-order/{po['id']}", json=[{"part": {"id": pid}, "quantity": 8}])

    assert admin.patch(f"/api/purchase-orders/{po['id']}/respond?approved=true").status_code == 200
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.purchase_order_id) == (
        "PO_RECEIPT", 8, 10, po["id"]
    )
    assert last.description == "PART_RECEPTION"

    # Use most of it, then reverse: the reversal is recorded even though it takes stock negative.
    admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 9, "reason": "Used"})
    assert admin.patch(f"/api/purchase-orders/{po['id']}/respond?approved=false").status_code == 200
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.purchase_order_id) == (
        "PO_REVERSAL", -8, -7, po["id"]
    )
    assert _quantity(env, pid) == -7
    _assert_ledger_explains_quantity(env, pid)


def test_workflow_approve_records_po_receipt(env: dict) -> None:
    admin = env["admin"]
    pid = _part(admin, "Workflow PO Part", 1)["id"]
    po_id = admin.post("/api/purchase-orders", json={"name": "PO-WF-1"}).json()["id"]
    admin.patch(f"/api/part-quantities/purchase-order/{po_id}", json=[{"part": {"id": pid}, "quantity": 4}])
    approve = list(PurchaseOrderAction).index(PurchaseOrderAction.APPROVE)
    with env["session_local"]() as db:
        po = db.get(PurchaseOrder, po_id)
        _apply_po_action(po, WorkflowAction(purchase_order_action=approve), db)
        db.commit()
        assert po.status == 0
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.purchase_order_id) == (
        "PO_RECEIPT", 4, 5, po_id
    )
    assert _quantity(env, pid) == 5


def test_part_form_patch_writes_adjustment(env: dict) -> None:
    admin = env["admin"]
    pid = _part(admin, "Form Part", 10)["id"]

    resp = admin.patch(f"/api/parts/{pid}", json={"quantity": 14})
    assert resp.status_code == 200, resp.text
    assert resp.json()["quantity"] == 14
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.reason) == (
        "ADJUSTMENT", 4, 14, "Edited on part form"
    )

    admin.patch(f"/api/parts/{pid}", json={"quantity": 11, "stockReason": "Damaged in storage"})
    last = _rows(env, pid)[-1]
    assert (last.change, last.balance_after, last.reason) == (-3, 11, "Damaged in storage")

    count = len(_rows(env, pid))
    admin.patch(f"/api/parts/{pid}", json={"quantity": 11, "description": "same qty"})
    admin.patch(f"/api/parts/{pid}", json={"description": "no qty"})
    assert len(_rows(env, pid)) == count
    assert admin.patch(f"/api/parts/{pid}", json={"quantity": -1}).status_code == 406
    assert _quantity(env, pid) == 11
    _assert_ledger_explains_quantity(env, pid)


def test_csv_import_writes_movements(env: dict) -> None:
    admin = env["admin"]
    resp = admin.post("/api/import/parts", json=[{"name": "Imported Bearing", "cost": 3, "quantity": 7}])
    assert resp.status_code == 200, resp.text
    with env["session_local"]() as db:
        pid = db.scalar(select(Part.id).where(Part.name == "Imported Bearing"))
    rows = _rows(env, pid)
    assert [(r.movement_type, r.change, r.reason) for r in rows] == [("OPENING", 7, "CSV import")]

    resp = admin.post("/api/import/parts", json=[{"id": pid, "name": "Imported Bearing", "quantity": 10}])
    assert resp.json()["updated"] == 1
    last = _rows(env, pid)[-1]
    assert (last.movement_type, last.change, last.balance_after, last.reason) == (
        "ADJUSTMENT", 3, 10, "CSV import"
    )
    admin.post("/api/import/parts", json=[{"id": pid, "name": "Imported Bearing", "quantity": 10}])
    assert len(_rows(env, pid)) == 2
    assert _quantity(env, pid) == 10


def test_restock_alias_still_works(env: dict) -> None:
    admin = env["admin"]
    pid = _part(admin, "Restock Part", 10)["id"]
    assert admin.patch(f"/api/parts/{pid}/restock", json={"quantity": -5}).status_code == 406
    resp = admin.patch(f"/api/parts/{pid}/restock", json={"quantity": 5})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 15
    assert admin.post(f"/api/parts/{pid}/restock", json={"quantity": 1}).json()["quantity"] == 16
    rows = _rows(env, pid)
    assert [(r.movement_type, r.change, r.description) for r in rows[1:]] == [
        ("RECEIPT", 5, "PART_RESTOCK"),
        ("RECEIPT", 1, "PART_RESTOCK"),
    ]


def test_movements_list_contract(env: dict) -> None:
    admin = env["admin"]
    wo_id = env["wo_id"]
    pid = _part(admin, "Listed Part", 3)["id"]
    po = admin.post("/api/purchase-orders", json={"name": "PO-LIST-1"}).json()
    admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 2, "purchaseOrderId": po["id"]})
    admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1, "workOrderId": wo_id})
    for _ in range(3):
        admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 1})

    body = admin.get(f"/api/parts/{pid}/stock/movements").json()
    assert body["totalElements"] == 6
    assert (body["page"], body["size"]) == (0, 20)
    content = body["content"]
    assert [m["movementType"] for m in content] == [
        "RECEIPT", "RECEIPT", "RECEIPT", "ISSUE", "PO_RECEIPT", "OPENING"
    ]
    newest = content[0]
    assert set(newest) == {
        "id", "createdAt", "movementType", "change", "balanceAfter", "quantity", "reason",
        "unitCost", "createdBy", "workOrder", "purchaseOrder",
    }
    assert newest["balanceAfter"] == 7
    assert newest["createdBy"] == {"id": env["user_id"], "firstName": "Stock", "lastName": "Admin"}
    issue = content[3]
    assert issue["workOrder"]["id"] == wo_id and issue["workOrder"]["title"] == "Stock WO"
    assert "customId" in issue["workOrder"]
    assert content[4]["purchaseOrder"] == {"id": po["id"], "name": "PO-LIST-1"}
    assert content[5]["workOrder"] is None and content[5]["purchaseOrder"] is None

    page1 = admin.get(f"/api/parts/{pid}/stock/movements?page=1&size=4").json()
    assert [m["id"] for m in page1["content"]] == [m["id"] for m in content[4:]]
    assert admin.get(f"/api/parts/{pid}/stock/movements?size=500").json()["size"] == 100
    # The router is mounted at the site root too.
    assert admin.get(f"/parts/{pid}/stock/movements").json()["totalElements"] == 6


def test_cross_tenant_access(env: dict) -> None:
    admin, admin_b = env["admin"], env["admin_b"]
    pid = _part(admin, "Tenant A Secret Part", 5)["id"]
    for method, path, body in (
        ("post", "stock/receive", {"quantity": 1}),
        ("post", "stock/issue", {"quantity": 1, "reason": "x"}),
        ("post", "stock/count", {"counted": 1, "reason": "x"}),
        ("post", "restock", {"quantity": 1}),
        ("patch", "restock", {"quantity": 1}),
    ):
        resp = getattr(admin_b, method)(f"/api/parts/{pid}/{path}", json=body)
        assert resp.status_code in (403, 404), (method, path, resp.status_code)
    assert admin_b.get(f"/api/parts/{pid}/stock/movements").status_code in (403, 404)
    assert admin_b.patch(f"/api/parts/{pid}", json={"quantity": 50}).status_code in (403, 404)
    assert _quantity(env, pid) == 5
    assert len(_rows(env, pid)) == 1

    # Tenant B's own part lists only its own rows; A cannot attach B's PO or WO to its stock.
    pid_b = _part(admin_b, "Tenant B Part", 2)["id"]
    listed = admin_b.get(f"/api/parts/{pid_b}/stock/movements").json()
    assert [m["movementType"] for m in listed["content"]] == ["OPENING"]
    with env["session_local"]() as db:
        assert db.get(Part, pid_b).company_id == env["company_b_id"]
    po_b = admin_b.post("/api/purchase-orders", json={"name": "PO-B"})
    assert po_b.status_code == 200, po_b.text
    wo_b = admin_b.post("/api/work-orders", json={"title": "WO-B"})
    assert wo_b.status_code == 200, wo_b.text
    assert admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 1, "purchaseOrderId": po_b.json()["id"]}).status_code == 403
    assert admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1, "workOrderId": wo_b.json()["id"]}).status_code == 403
    assert len(_rows(env, pid)) == 1


def test_analytics_consumption_nets_returns(env: dict) -> None:
    admin = env["admin"]
    wo_id = env["wo_id"]
    pid = _part(admin, "Analytics Part", 20)["id"]  # cost 10
    pq = admin.post(
        "/api/part-quantities",
        json={"part": {"id": pid}, "workOrder": {"id": wo_id}, "quantity": 5},
    ).json()
    admin.patch(f"/api/part-quantities/{pq['id']}", json={"quantity": 2})  # WO_RETURN 3
    admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 1, "workOrderId": wo_id})  # counts
    admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": 4, "reason": "Shop"})  # no WO: not consumption
    admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": 6})
    admin.post(f"/api/parts/{pid}/stock/count", json={"counted": 3, "reason": "Recount"})
    admin.patch(f"/api/parts/{pid}", json={"quantity": 9})

    pareto = admin.post("/api/analytics/parts/consumptions/pareto", json={}).json()
    entry = next(r for r in pareto if r["id"] == pid)
    assert entry["cost"] == 30.0  # (5 - 3 + 1) x 10

    # A part whose WO line was fully returned has no consumption at all.
    pid2 = _part(admin, "Returned Part", 5)["id"]
    pq2 = admin.post(
        "/api/part-quantities",
        json={"part": {"id": pid2}, "workOrder": {"id": wo_id}, "quantity": 2},
    ).json()
    admin.delete(f"/api/part-quantities/{pq2['id']}")
    pareto = admin.post("/api/analytics/parts/consumptions/pareto", json={}).json()
    assert all(r["id"] != pid2 for r in pareto)
    overview = admin.post("/api/analytics/parts/consumptions/overview", json={})
    assert overview.status_code == 200


def test_ledger_invariant_after_random_operations(env: dict) -> None:
    """50 mixed operations (some rejected); every part's ledger must still explain its quantity."""
    admin = env["admin"]
    wo_id = env["wo_id"]
    rng = random.Random(20261114)  # noqa: S311 - a reproducible test sequence, not a secret
    part_ids = [_part(admin, f"Random Part {i}", rng.randint(0, 10))["id"] for i in range(3)]
    lines: list[int] = []
    approved_pos: list[int] = []
    rejected = 0

    for _ in range(50):
        pid = rng.choice(part_ids)
        op = rng.choice(
            ["receive", "issue", "issue_wo", "count", "patch", "restock", "wo_add", "wo_edit", "wo_delete", "po"]
        )
        if op == "receive":
            r = admin.post(f"/api/parts/{pid}/stock/receive", json={"quantity": rng.randint(1, 8)})
        elif op == "issue":
            r = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": rng.randint(1, 8), "reason": "Random"})
        elif op == "issue_wo":
            r = admin.post(f"/api/parts/{pid}/stock/issue", json={"quantity": rng.randint(1, 5), "workOrderId": wo_id})
        elif op == "count":
            r = admin.post(f"/api/parts/{pid}/stock/count", json={"counted": rng.randint(0, 15), "reason": "Random"})
        elif op == "patch":
            r = admin.patch(f"/api/parts/{pid}", json={"quantity": rng.randint(0, 20)})
        elif op == "restock":
            r = admin.patch(f"/api/parts/{pid}/restock", json={"quantity": rng.randint(1, 4)})
        elif op == "wo_add":
            r = admin.post(
                "/api/part-quantities",
                json={"part": {"id": pid}, "workOrder": {"id": wo_id}, "quantity": rng.randint(1, 6)},
            )
            if r.status_code == 200:
                lines.append(r.json()["id"])
        elif op == "wo_edit" and lines:
            r = admin.patch(f"/api/part-quantities/{rng.choice(lines)}", json={"quantity": rng.randint(1, 8)})
        elif op == "wo_delete" and lines:
            line = lines.pop(rng.randrange(len(lines)))
            r = admin.delete(f"/api/part-quantities/{line}")
        elif op == "po" and approved_pos and rng.random() < 0.4:
            r = admin.patch(f"/api/purchase-orders/{approved_pos.pop()}/respond?approved=false")
        else:
            po_id = admin.post("/api/purchase-orders", json={"name": "Random PO"}).json()["id"]
            admin.patch(
                f"/api/part-quantities/purchase-order/{po_id}",
                json=[{"part": {"id": pid}, "quantity": rng.randint(1, 6)}],
            )
            r = admin.patch(f"/api/purchase-orders/{po_id}/respond?approved=true")
            approved_pos.append(po_id)
        assert r.status_code in (200, 406), (op, r.status_code, r.text)
        rejected += r.status_code == 406

    assert rejected > 0  # the sequence exercised the insufficient-stock guard
    for pid in part_ids:
        rows = _rows(env, pid)
        quantity = _quantity(env, pid)
        has_opening = rows[0].movement_type == MovementType.OPENING
        opening = rows[0].change if has_opening else 0.0
        later = rows[1:] if has_opening else rows
        assert rows[-1].balance_after == quantity
        assert sum(r.change for r in later) == quantity - opening
        _assert_ledger_explains_quantity(env, pid)
    with env["session_local"]() as db:
        open_lines = db.scalars(select(PartQuantity).where(PartQuantity.id.in_(lines))).all()
        assert len(open_lines) == len(lines)
