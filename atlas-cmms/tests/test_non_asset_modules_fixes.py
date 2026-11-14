"""Regression tests for NON_ASSET_MODULES_AUDIT_REPORT.md (all 6 non-asset domains)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.models  # noqa: F401
from src.app import app
from src.deps.current_user import get_current_user, get_optional_current_user
from src.deps.db import get_db
from src.jobs.pm_generator import generate_due_work_orders
from src.models._base import Base, utcnow
from src.models.associations import (
    role_create_permissions,
    role_delete_other_permissions,
    role_edit_other_permissions,
    role_view_other_permissions,
    role_view_permissions,
)
from src.models.company import Company
from src.models.settings import (
    CompanySettings,
    FieldConfiguration,
    GeneralPreferences,
    WorkOrderConfiguration,
)
from src.models.enums import PermissionEntity
from src.models.files_custom import CustomField, File as FileEntity
from src.models.parts_po import Customer, PartTransaction
from src.models.pm_schedule import PreventiveMaintenance, Schedule
from src.models.tasks import Task, TaskBase
from src.models.users import Role, User, UserSettings
from src.models.work_orders import Labor, WorkOrder
from src.routes import work_orders_pm as work_orders_pm_routes
from src.utils.dates import ensure_utc


@pytest.fixture()
def non_asset_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_local() as db:
        # Company A
        cs_a = CompanySettings()
        db.add(cs_a)
        db.flush()
        gp_a = GeneralPreferences(company_settings_id=cs_a.id)
        db.add(gp_a)
        comp_a = Company(name="Tenant Alpha", company_settings_id=cs_a.id)
        db.add(comp_a)
        db.flush()

        role_a = Role(
            name="Admin Alpha",
            code=0,
            role_type=1,
            company_settings_id=cs_a.id,
        )
        db.add(role_a)
        db.flush()
        for idx in range(len(PermissionEntity)):
            db.execute(
                role_view_permissions.insert().values(role_id=role_a.id, view_permissions=idx)
            )
            db.execute(
                role_view_other_permissions.insert().values(
                    role_id=role_a.id, view_other_permissions=idx
                )
            )
            db.execute(
                role_create_permissions.insert().values(
                    role_id=role_a.id, create_permissions=idx
                )
            )
            db.execute(
                role_edit_other_permissions.insert().values(
                    role_id=role_a.id, edit_other_permissions=idx
                )
            )
            db.execute(
                role_delete_other_permissions.insert().values(
                    role_id=role_a.id, delete_other_permissions=idx
                )
            )

        us_a = UserSettings()
        db.add(us_a)
        db.flush()
        user_a = User(
            first_name="Alice",
            last_name="Admin",
            email="alice@alpha.test",
            username="alice@alpha.test",
            password="hashed_password",
            company_id=comp_a.id,
            role_id=role_a.id,
            user_settings_id=us_a.id,
            enabled=True,
            owns_company=True,
            rate=50.0,
        )
        db.add(user_a)

        # Company B
        cs_b = CompanySettings()
        db.add(cs_b)
        db.flush()
        gp_b = GeneralPreferences(company_settings_id=cs_b.id)
        db.add(gp_b)
        comp_b = Company(name="Tenant Beta", company_settings_id=cs_b.id)
        db.add(comp_b)
        db.flush()

        role_b = Role(
            name="Admin Beta",
            code=0,
            role_type=1,
            company_settings_id=cs_b.id,
        )
        db.add(role_b)
        db.flush()
        for idx in range(len(PermissionEntity)):
            db.execute(
                role_view_permissions.insert().values(role_id=role_b.id, view_permissions=idx)
            )
            db.execute(
                role_view_other_permissions.insert().values(
                    role_id=role_b.id, view_other_permissions=idx
                )
            )
            db.execute(
                role_create_permissions.insert().values(
                    role_id=role_b.id, create_permissions=idx
                )
            )
            db.execute(
                role_edit_other_permissions.insert().values(
                    role_id=role_b.id, edit_other_permissions=idx
                )
            )
            db.execute(
                role_delete_other_permissions.insert().values(
                    role_id=role_b.id, delete_other_permissions=idx
                )
            )
        us_b = UserSettings()
        db.add(us_b)
        db.flush()
        user_b = User(
            first_name="Bob",
            last_name="Beta",
            email="bob@beta.test",
            username="bob@beta.test",
            password="hashed_password",
            company_id=comp_b.id,
            role_id=role_b.id,
            user_settings_id=us_b.id,
            enabled=True,
            owns_company=True,
        )
        db.add(user_b)
        db.commit()

        env_info = {
            "session_local": session_local,
            "comp_a_id": comp_a.id,
            "comp_b_id": comp_b.id,
            "cs_a_id": cs_a.id,
            "cs_b_id": cs_b.id,
            "gp_b_id": gp_b.id,
            "role_a_id": role_a.id,
            "role_b_id": role_b.id,
            "user_a_id": user_a.id,
            "user_b_id": user_b.id,
            "us_b_id": us_b.id,
            "current_user_id": user_a.id,
        }

    def _override_get_db():
        with session_local() as session:
            yield session

    def _override_current_user():
        uid = env_info["current_user_id"]
        if uid is None:
            from src.schemas.errors import CustomException

            raise CustomException(status_code=401, message="Unauthorized")
        with session_local() as session:
            u = session.get(User, uid)
            session.expunge(u)
            return u

    def _override_optional_user():
        uid = env_info["current_user_id"]
        if uid is None:
            return None
        with session_local() as session:
            u = session.get(User, uid)
            session.expunge(u)
            return u

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_current_user
    app.dependency_overrides[get_optional_current_user] = _override_optional_user

    with TestClient(app) as client:
        env_info["client"] = client
        yield env_info

    app.dependency_overrides.clear()


def test_auth_users_roles_and_tenant_admin_isolation(non_asset_env: dict) -> None:
    """AUTH-P0-01..04, AUTH-P1-01: Tenant admin isolation, per-user UserSettings, role scoping."""
    client: TestClient = non_asset_env["client"]
    comp_b_id = non_asset_env["comp_b_id"]
    cs_b_id = non_asset_env["cs_b_id"]
    gp_b_id = non_asset_env["gp_b_id"]
    us_b_id = non_asset_env["us_b_id"]
    role_b_id = non_asset_env["role_b_id"]
    role_a_id = non_asset_env["role_a_id"]

    # 1. Tenant A admin cannot access Tenant B's company, settings, preferences, or user-settings
    assert client.get(f"/api/companies/{comp_b_id}").status_code == 403
    assert client.patch(f"/api/companies/{comp_b_id}", json={"name": "Hacked"}).status_code == 403
    assert client.get(f"/api/company-settings/{cs_b_id}").status_code == 403
    assert client.get(f"/api/general-preferences/{gp_b_id}").status_code == 403
    assert (
        client.patch(f"/api/general-preferences/{gp_b_id}", json={"autoAssignWorkOrders": True}).status_code
        == 403
    )
    assert client.get(f"/api/user-settings/{us_b_id}").status_code == 403
    assert client.patch(f"/api/user-settings/{us_b_id}", json={"emailNotified": False}).status_code == 403

    # 2. Roles are strictly scoped to Tenant A; creating a role sets code="USER_CREATED"; system roles cannot be deleted
    roles_list = client.get("/api/roles").json()
    role_ids = {r["id"] for r in roles_list}
    assert role_a_id in role_ids
    assert role_b_id not in role_ids

    new_role_resp = client.post(
        "/api/roles",
        json={
            "name": "Custom Technician",
            "createPermissions": ["WORK_ORDERS"],
            "viewPermissions": ["WORK_ORDERS"],
        },
    )
    assert new_role_resp.status_code == 200
    new_role = new_role_resp.json()
    assert new_role["code"] == "USER_CREATED"

    # Cannot delete or patch system default role (role_a has code=ADMIN)
    assert client.delete(f"/api/roles/{role_a_id}").status_code in (400, 403)
    assert client.patch(f"/api/roles/{role_a_id}", json={"name": "Renamed Admin"}).status_code in (
        400,
        403,
    )

    # Can patch and delete user-created role
    assert (
        client.patch(f"/api/roles/{new_role['id']}", json={"name": "Updated Tech"}).status_code
        == 200
    )

    # 3. POST /users rejects cross-tenant role_b_id and provisions a dedicated UserSettings row
    bad_user_resp = client.post(
        "/api/users",
        json={
            "firstName": "Cross",
            "lastName": "Role",
            "email": "cross@alpha.test",
            "role": {"id": role_b_id},
        },
    )
    assert bad_user_resp.status_code in (400, 403)

    u1 = client.post(
        "/api/users",
        json={
            "firstName": "Tech",
            "lastName": "One",
            "email": "tech1@alpha.test",
            "role": {"id": new_role["id"]},
        },
    ).json()
    u2 = client.post(
        "/api/users",
        json={
            "firstName": "Tech",
            "lastName": "Two",
            "email": "tech2@alpha.test",
            "role": {"id": new_role["id"]},
        },
    ).json()
    assert u1["userSettings"]["id"] != u2["userSettings"]["id"]


def test_work_orders_labor_parts_tasks_and_m2m(non_asset_env: dict) -> None:
    """WO-P0-01..04, WO-P1-01..02: Labor timer, PartQuantity stock/tx, in-place Tasks, WO M2M/files."""
    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    comp_a_id = non_asset_env["comp_a_id"]
    cs_a_id = non_asset_env["cs_a_id"]
    user_a_id = non_asset_env["user_a_id"]

    with session_local() as db:
        cf = CustomField(
            label="WO Voltage",
            field_type="TEXT",
            entity_type="WORK_ORDER",
            required=False,
            copy_on_repeat=False,
            field_order=0,
            company_settings_id=cs_a_id,
        )
        f1 = FileEntity(
            name="manual.pdf",
            path="manual.pdf",
            type=0,
            hidden=False,
            company_id=comp_a_id,
            created_by=user_a_id,
        )
        db.add_all([cf, f1])
        db.commit()
        cf_id = cf.id
        file_id = f1.id

    cust = client.post("/api/customers", json={"name": "Acme Client"}).json()
    part = client.post(
        "/api/parts",
        json={"name": "Mechanical Seal", "cost": 25.0, "quantity": 10.0, "nonStock": False},
    ).json()

    # 1. Create WO with M2M assignedTo, customers, files, customFieldValues
    wo = client.post(
        "/api/work-orders",
        json={
            "title": "Overhaul Booster Pump",
            "priority": "HIGH",
            "assignedTo": [{"id": user_a_id}],
            "customers": [{"id": cust["id"]}],
            "files": [{"id": file_id}],
            "customFieldValues": [{"customField": {"id": cf_id}, "value": "480V"}],
        },
    ).json()
    wo_id = wo["id"]
    assert len(wo["assignedTo"]) == 1
    assert wo["assignedTo"][0]["id"] == user_a_id
    assert len(wo["customers"]) == 1
    assert wo["customers"][0]["id"] == cust["id"]
    assert len(wo["files"]) == 1
    assert wo["files"][0]["id"] == file_id
    assert len(wo["customFieldValues"]) == 1
    assert wo["customFieldValues"][0]["value"] == "480V"

    # 2. WO-P0-01: Start & stop labor timer via query param ?start=true|false
    start_resp = client.post(f"/api/labors/work-order/{wo_id}?start=true")
    assert start_resp.status_code == 200
    started_labor = start_resp.json()
    assert started_labor["status"] == "RUNNING"

    # Backdate started_at by 2 hours so stopping computes 7200s duration
    with session_local() as db:
        lb = db.get(Labor, started_labor["id"])
        lb.started_at = utcnow() - timedelta(hours=2)
        db.commit()

    stop_resp = client.post(f"/api/labors/work-order/{wo_id}?start=false")
    assert stop_resp.status_code == 200
    stopped_labor = stop_resp.json()
    assert stopped_labor["status"] == "STOPPED"
    assert stopped_labor["duration"] >= 7190

    # Verify WO moved to IN_PROGRESS and recorded firstTimeToReact
    wo_after_timer = client.get(f"/api/work-orders/{wo_id}").json()
    assert wo_after_timer["status"] == "IN_PROGRESS"
    assert wo_after_timer["firstTimeToReact"] is not None

    # 3. WO-P0-02: PartQuantity stock check, deduction, restoration, and PartTransaction logging
    over_stock = client.patch(
        f"/api/part-quantities/work-order/{wo_id}",
        json=[{"part": {"id": part["id"]}, "quantity": 50}],
    )
    assert over_stock.status_code == 406

    consume_resp = client.patch(
        f"/api/part-quantities/work-order/{wo_id}",
        json=[{"part": {"id": part["id"]}, "quantity": 3}],
    )
    assert consume_resp.status_code == 200
    assert len(consume_resp.json()) == 1
    assert consume_resp.json()[0]["quantity"] == 3

    part_after = client.get(f"/api/parts/{part['id']}").json()
    assert part_after["quantity"] == 7.0
    assert part_after["openWorkOrders"] == 1

    # Verify GET /work-orders/part/{part_id} returns this WO
    wos_for_part = client.get(f"/api/work-orders/part/{part['id']}").json()
    assert len(wos_for_part) == 1
    assert wos_for_part[0]["id"] == wo_id

    with session_local() as db:
        txs = db.scalars(
            select(PartTransaction).where(PartTransaction.work_order_id == wo_id)
        ).all()
        assert len(txs) == 1
        assert txs[0].quantity == 3

    # 4. WO-P0-03: In-place Task reconciliation (preserves IDs and task options)
    t_initial = client.patch(
        f"/api/tasks/work-order/{wo_id}",
        json=[
            {
                "taskBase": {
                    "label": "Check alignment",
                    "taskType": "MULTIPLE",
                    "options": ["PASS", "FAIL"],
                },
                "value": "PASS",
                "notes": "Aligned within 0.02mm",
            }
        ],
    ).json()
    assert len(t_initial) == 1
    task_id = t_initial[0]["id"]
    assert [
        o["label"] if isinstance(o, dict) else o for o in t_initial[0]["taskBase"]["options"]
    ] == ["PASS", "FAIL"]

    t_updated = client.patch(
        f"/api/tasks/work-order/{wo_id}",
        json=[
            {
                "id": task_id,
                "taskBase": {
                    "label": "Check alignment (updated)",
                    "taskType": "MULTIPLE",
                    "options": ["PASS", "FAIL", "N/A"],
                },
                "value": "PASS",
                "notes": "Verified twice",
            }
        ],
    ).json()
    assert len(t_updated) == 1
    assert t_updated[0]["id"] == task_id
    assert t_updated[0]["notes"] == "Verified twice"
    assert [
        o["label"] if isinstance(o, dict) else o for o in t_updated[0]["taskBase"]["options"]
    ] == ["PASS", "FAIL", "N/A"]


def test_pm_trigger_schedule_advancement_and_workload(non_asset_env: dict) -> None:
    """PM-P0-01..03, PM-P1-01: PM M2M, trigger-work-order task/relation cloning, schedule advance, workload."""
    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    user_a_id = non_asset_env["user_a_id"]

    pm = client.post(
        "/api/preventive-maintenances",
        json={
            "name": "Monthly Chiller PM",
            "title": "Inspect Chiller Coils",
            "description": "Full coil cleaning",
            "priority": "MEDIUM",
            "assignedTo": [{"id": user_a_id}],
        },
    ).json()
    pm_id = pm["id"]
    sched_id = pm["schedule"]["id"]
    assert len(pm["assignedTo"]) == 1

    # Patch schedule with daysOfWeek and past nextDueDate
    past_due = (utcnow() - timedelta(days=2)).isoformat()
    sched = client.patch(
        f"/api/schedules/{sched_id}",
        json={
            "frequency": 1,
            "recurrenceType": "WEEKLY",
            "daysOfWeek": [1, 3, 5],
            "nextDueDate": past_due,
        },
    ).json()
    assert sched["daysOfWeek"] == [1, 3, 5]

    # Add task to PM
    pm_tasks = client.patch(
        f"/api/tasks/preventive-maintenance/{pm_id}",
        json=[{"taskBase": {"label": "Clean condenser fins", "taskType": "SUBTASK"}}],
    ).json()
    assert len(pm_tasks) == 1

    # Trigger WorkOrder from PM via endpoint
    triggered_wo = client.post(f"/api/preventive-maintenances/{pm_id}/trigger-work-order").json()
    assert triggered_wo["title"] == "Inspect Chiller Coils"
    assert triggered_wo["parentPreventiveMaintenance"]["id"] == pm_id
    assert len(triggered_wo["assignedTo"]) == 1

    wo_tasks = client.get(f"/api/tasks/work-order/{triggered_wo['id']}").json()
    assert len(wo_tasks) == 1
    assert wo_tasks[0]["taskBase"]["label"] == "Clean condenser fins"

    # Also test background pm_generator advancing schedule next_due_date
    with session_local() as db:
        sched_row = db.get(Schedule, sched_id)
        sched_row.next_due_date = utcnow() - timedelta(days=1)
        db.commit()

        generated_wos = generate_due_work_orders(db)
        assert len(generated_wos) == 1
        db.refresh(sched_row)
        assert ensure_utc(sched_row.next_due_date) > utcnow()

    # Workload endpoints
    wl_overview = client.get("/api/workload/overview").json()
    assert "teamAllocatedMinutes" in wl_overview
    assert "days" in wl_overview

    wl_unscheduled = client.get("/api/workload/unscheduled").json()
    assert "workOrders" in wl_unscheduled

    pm_wl = client.post("/api/preventive-maintenances/workload", json={}).json()
    assert isinstance(pm_wl, list)


def test_purchase_orders_parts_vendors_customers_and_requests(non_asset_env: dict) -> None:
    """PO-P0-01..03, REQ-P0-01..03: PO line items & approval stock reception, public portal request, request approve/cancel."""
    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    cs_a_id = non_asset_env["cs_a_id"]
    cs_b_id = non_asset_env["cs_b_id"]
    user_a_id = non_asset_env["user_a_id"]

    with session_local() as db:
        cf_vendor = CustomField(
            label="Vendor Tier",
            field_type="TEXT",
            entity_type="VENDOR",
            required=False,
            copy_on_repeat=False,
            field_order=0,
            company_settings_id=cs_a_id,
        )
        db.add(cf_vendor)
        db.commit()
        cf_vendor_id = cf_vendor.id

    # 1. Vendor with customFieldValues
    vendor = client.post(
        "/api/vendors",
        json={
            "companyName": "Grainger",
            "name": "Account Rep",
            "customFieldValues": [{"customField": {"id": cf_vendor_id}, "value": "Gold"}],
        },
    ).json()
    assert len(vendor["customFieldValues"]) == 1
    assert vendor["customFieldValues"][0]["value"] == "Gold"

    # 2. Part & PurchaseOrder line items + approval stock increment
    part = client.post(
        "/api/parts",
        json={
            "name": "HEPA Filter",
            "cost": 40.0,
            "quantity": 5.0,
            "assignedTo": [{"id": user_a_id}],
            "vendors": [{"id": vendor["id"]}],
        },
    ).json()
    assert len(part["assignedTo"]) == 1
    assert len(part["vendors"]) == 1

    po = client.post(
        "/api/purchase-orders",
        json={"name": "PO-2026-001", "vendor": {"id": vendor["id"]}},
    ).json()
    po_id = po["id"]

    po_pqs = client.patch(
        f"/api/part-quantities/purchase-order/{po_id}",
        json=[{"part": {"id": part["id"]}, "quantity": 10}],
    ).json()
    assert len(po_pqs) == 1
    assert po_pqs[0]["quantity"] == 10

    po_hydrated = client.get(f"/api/purchase-orders/{po_id}").json()
    assert len(po_hydrated["partQuantities"]) == 1

    # Approve PO via query param ?approved=true -> increments Part.quantity by 10
    po_approved = client.patch(f"/api/purchase-orders/{po_id}/respond?approved=true").json()
    assert po_approved["status"] == "APPROVED"

    part_after_po = client.get(f"/api/parts/{part['id']}").json()
    assert part_after_po["quantity"] == 15.0

    # 3. Public RequestPortal submission (unauthenticated) + Request approve/cancel
    portal = client.post("/api/request-portals", json={"title": "Lobby Helpdesk"}).json()
    portal_uuid = portal["uuid"]

    non_asset_env["current_user_id"] = None
    portal_req_resp = client.post(
        f"/api/requests/portal/{portal_uuid}",
        json={"title": "Broken AC in Conference Room", "priority": "HIGH"},
    )
    assert portal_req_resp.status_code == 200
    portal_req = portal_req_resp.json()
    assert portal_req["companyId"] == non_asset_env["comp_a_id"]
    non_asset_env["current_user_id"] = user_a_id

    # Approve request -> creates WO and copies relations; double approve returns 406
    approved_wo = client.patch(f"/api/requests/{portal_req['id']}/approve").json()
    assert approved_wo["title"] == "Broken AC in Conference Room"
    assert client.patch(f"/api/requests/{portal_req['id']}/approve").status_code == 406

    # Cancel request via query param ?reason=...
    req2 = client.post("/api/requests", json={"title": "Duplicate Request"}).json()
    cancelled_req = client.patch(
        f"/api/requests/{req2['id']}/cancel?reason=Already+fixed"
    ).json()
    assert cancelled_req["cancelled"] is True
    assert cancelled_req["cancellationReason"] == "Already fixed"

    # 4. REQ-P0-03: GET /checklists/mini tenant isolation
    from src.models.tasks import Checklist

    with session_local() as db:
        cl_a = Checklist(name="Checklist Alpha", company_settings_id=cs_a_id)
        cl_b = Checklist(name="Checklist Beta", company_settings_id=cs_b_id)
        db.add_all([cl_a, cl_b])
        db.commit()

    mini_checklists = client.get("/api/checklists/mini").json()
    names = [c["name"] for c in mini_checklists]
    assert "Checklist Alpha" in names
    assert "Checklist Beta" not in names


def test_analytics_contracts_for_wo_parts_requests_and_users(non_asset_env: dict) -> None:
    """AN-P0-01..04: Verify analytics URL paths, response shapes, and calculations."""
    client: TestClient = non_asset_env["client"]
    user_a_id = non_asset_env["user_a_id"]
    user_b_id = non_asset_env["user_b_id"]

    # Complete a WO so completed_count >= 1
    wo = client.post("/api/work-orders", json={"title": "Analytics WO"}).json()
    client.patch(f"/api/work-orders/{wo['id']}/change-status", json={"status": "COMPLETE"})

    # 1. AN-P0-01: /analytics/work-orders/complete/costs-time
    costs_time = client.post("/api/analytics/work-orders/complete/costs-time", json={})
    assert costs_time.status_code == 200
    ct_data = costs_time.json()
    assert "total" in ct_data and "average" in ct_data

    # 2. AN-P0-02: /analytics/parts/consumptions/*
    part_ov = client.post("/api/analytics/parts/consumptions/overview", json={}).json()
    assert "totalConsumptionCost" in part_ov and "consumedCount" in part_ov
    assert client.post("/api/analytics/parts/consumptions/pareto", json={}).status_code == 200
    assert client.post("/api/analytics/parts/consumptions/assets", json={}).status_code == 200
    assert (
        client.post("/api/analytics/parts/consumptions/parts-category", json={}).status_code == 200
    )
    assert (
        client.post("/api/analytics/parts/consumptions/work-order-category", json={}).status_code
        == 200
    )
    assert client.post("/api/analytics/parts/consumptions/date", json={}).status_code == 200

    # 3. AN-P0-03: /analytics/requests/overview & /priority ({count: int} objects)
    req_ov = client.post("/api/analytics/requests/overview", json={}).json()
    assert {"approved", "pending", "cancelled", "cycleTime"} <= set(req_ov.keys())

    req_prio = client.post("/api/analytics/requests/priority", json={}).json()
    assert isinstance(req_prio["none"], dict) and "count" in req_prio["none"]
    assert isinstance(req_prio["high"], dict) and "count" in req_prio["high"]
    assert client.post("/api/analytics/requests/cycle-time/date", json={}).status_code == 200
    assert client.post("/api/analytics/requests/received-and-resolved", json={}).status_code == 200
    assert client.post("/api/analytics/requests/counts/category", json={}).status_code == 200

    # 4. AN-P0-04: /analytics/users/*
    u_comp = client.get("/api/analytics/users/complete/work-orders").json()
    assert "completed" in u_comp and "Completed" not in u_comp

    u_me = client.get("/api/analytics/users/me/work-orders/overview").json()
    assert u_me["created"] >= 1 and u_me["completed"] >= 1

    two_weeks = client.get(f"/api/analytics/users/two-weeks/work-orders/{user_a_id}")
    assert two_weeks.status_code == 200
    assert len(two_weeks.json()) == 14
    assert {"created", "completed", "date"} <= set(two_weeks.json()[0].keys())

    # Cross-tenant user_b_id is rejected with 403
    assert client.get(f"/api/analytics/users/two-weeks/work-orders/{user_b_id}").status_code == 403


def test_additional_audit_regressions_and_workflows_engine(non_asset_env: dict) -> None:
    """Verify WO-P0-02 (int array part quantities), WO-P0-03 (direct PQ patch/delete stock),
    PO-P0-01 (PO rejection stock reversal), WO-P1-01 (change-status signature/reopen/timer),
    auxiliary list/search tenant isolation, and REQ-P1-01 (Workflows execution engine)."""
    client: TestClient = non_asset_env["client"]
    user_a_id = non_asset_env["user_a_id"]
    user_b_id = non_asset_env["user_b_id"]

    # 1. WO-P0-02 & WO-P0-03: React editWOPartQuantities sends int[] (e.g. [part1_id, part2_id])
    p1 = client.post("/api/parts", json={"name": "Valve A", "cost": 10.0, "quantity": 20.0}).json()
    p2 = client.post("/api/parts", json={"name": "Valve B", "cost": 15.0, "quantity": 10.0}).json()
    wo = client.post(
        "/api/work-orders",
        json={"title": "Valve Replacement", "requiredSignature": True},
    ).json()
    wo_id = wo["id"]

    # Initial add via int[] -> creates quantity=1.0 for p1, stock becomes 19.0
    pqs_1 = client.patch(f"/api/part-quantities/work-order/{wo_id}", json=[p1["id"]]).json()
    assert len(pqs_1) == 1
    assert pqs_1[0]["quantity"] == 1.0
    assert client.get(f"/api/parts/{p1['id']}").json()["quantity"] == 19.0

    # WO-P0-03: Direct PATCH /api/part-quantities/{id} to quantity=4.0 -> stock decrements by 3 -> 16.0
    pq1_id = pqs_1[0]["id"]
    patched_pq = client.patch(f"/api/part-quantities/{pq1_id}", json={"quantity": 4.0}).json()
    assert patched_pq["quantity"] == 4.0
    assert client.get(f"/api/parts/{p1['id']}").json()["quantity"] == 16.0

    # Re-sending int[] [p1_id, p2_id] preserves p1's quantity=4.0 and adds p2 with quantity=1.0!
    pqs_2 = client.patch(
        f"/api/part-quantities/work-order/{wo_id}", json=[p1["id"], p2["id"]]
    ).json()
    assert len(pqs_2) == 2
    by_part = {item["part"]["id"]: item for item in pqs_2}
    assert by_part[p1["id"]]["quantity"] == 4.0
    assert by_part[p2["id"]]["quantity"] == 1.0
    assert client.get(f"/api/parts/{p1['id']}").json()["quantity"] == 16.0
    assert client.get(f"/api/parts/{p2['id']}").json()["quantity"] == 9.0

    # WO-P0-03: Direct DELETE /api/part-quantities/{id} restores p2 stock back to 10.0
    pq2_id = by_part[p2["id"]]["id"]
    assert client.delete(f"/api/part-quantities/{pq2_id}").status_code == 200
    assert client.get(f"/api/parts/{p2['id']}").json()["quantity"] == 10.0

    # 2. PO-P0-01: Rejecting an already-approved PO reverses the added stock and sets REJECTED
    po = client.post("/api/purchase-orders", json={"name": "PO-Reversal-Test"}).json()
    client.patch(
        f"/api/part-quantities/purchase-order/{po['id']}",
        json=[{"part": {"id": p2["id"]}, "quantity": 5.0}],
    )
    po_app = client.patch(f"/api/purchase-orders/{po['id']}/respond?approved=true").json()
    assert po_app["status"] == "APPROVED"
    assert client.get(f"/api/parts/{p2['id']}").json()["quantity"] == 15.0

    po_rej = client.patch(f"/api/purchase-orders/{po['id']}/respond?approved=false").json()
    assert po_rej["status"] == "REJECTED"
    assert client.get(f"/api/parts/{p2['id']}").json()["quantity"] == 10.0

    # 3. WO-P1-01: change-status enforces requiredSignature, stops timer when leaving IN_PROGRESS,
    # and clears completedOn when reopening from COMPLETE
    assert (
        client.patch(
            f"/api/work-orders/{wo_id}/change-status", json={"status": "COMPLETE"}
        ).status_code
        == 406
    )
    # Turn off requiredSignature, complete, then reopen
    client.patch(f"/api/work-orders/{wo_id}", json={"requiredSignature": False})
    comp_wo = client.patch(
        f"/api/work-orders/{wo_id}/change-status", json={"status": "COMPLETE"}
    ).json()
    assert comp_wo["status"] == "COMPLETE"
    assert comp_wo["completedOn"] is not None

    reopened_wo = client.patch(
        f"/api/work-orders/{wo_id}/change-status", json={"status": "OPEN"}
    ).json()
    assert reopened_wo["status"] == "OPEN"
    assert reopened_wo["completedOn"] is None
    assert reopened_wo["completedBy"] is None

    # 4. Auxiliary GET list & POST search tenant isolation (Schedule, AdditionalCost)
    non_asset_env["current_user_id"] = user_b_id
    pm_b = client.post("/api/preventive-maintenances", json={"title": "Tenant B PM"}).json()
    sched_b_id = pm_b["schedule"]["id"]
    wo_b = client.post("/api/work-orders", json={"title": "Tenant B WO"}).json()
    ac_b = client.post(
        "/api/additional-costs",
        json={"description": "Tenant B Secret Cost", "cost": 999.0, "workOrder": {"id": wo_b["id"]}},
    ).json()

    non_asset_env["current_user_id"] = user_a_id
    sched_list_a = client.get("/api/schedules").json()
    assert all(s["id"] != sched_b_id for s in sched_list_a)
    sched_search_a = client.post("/api/schedules/search", json={}).json()["content"]
    assert all(s["id"] != sched_b_id for s in sched_search_a)

    ac_list_a = client.get("/api/additional-costs").json()
    assert all(ac["id"] != ac_b["id"] for ac in ac_list_a)
    assert client.patch(f"/api/schedules/{sched_b_id}/reschedule", json={}).status_code == 403

    # 5. REQ-P1-01: Workflows execution engine automatically fires on WORK_ORDER_CREATED
    wf_resp = client.post(
        "/api/workflows",
        json={
            "title": "Auto High Priority & Assign",
            "mainCondition": "WORK_ORDER_CREATED",
            "secondaryConditions": [
                {
                    "workOrderCondition": "PRIORITY_IS",
                    "priority": "LOW",
                }
            ],
            "action": {
                "workOrderAction": "ASSIGN_PRIORITY",
                "priority": "HIGH",
            },
        },
    )
    assert wf_resp.status_code == 200

    auto_wo = client.post(
        "/api/work-orders",
        json={"title": "Triggered by Workflow", "priority": "LOW"},
    ).json()
    assert auto_wo["priority"] == "HIGH"


def test_calendar_events_accept_blank_company_id(non_asset_env):
    """The calendar posts companyId= when no company filter is selected.

    FastAPI used to reject that empty query as 422, and the React thunk left
    loadingGet true, so the calendar spinner never stopped.
    """
    from datetime import datetime, timedelta, timezone

    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    window_start = now + timedelta(days=2)
    window_end = window_start + timedelta(days=7)
    in_range = window_start + timedelta(days=1)
    out_of_range = window_end + timedelta(days=20)

    with session_local() as db:
        visible = WorkOrder(
            title="Visible in week",
            company_id=non_asset_env["comp_a_id"],
            due_date=in_range,
            estimated_duration=2.0,
            priority=3,
            status=0,
            archived=False,
            required_signature=False,
            is_demo=False,
            created_by=non_asset_env["user_a_id"],
        )
        hidden = WorkOrder(
            title="Other tenant",
            company_id=non_asset_env["comp_b_id"],
            due_date=in_range,
            estimated_duration=1.0,
            priority=1,
            status=0,
            archived=False,
            required_signature=False,
            is_demo=False,
        )
        later = WorkOrder(
            title="Outside the visible week",
            company_id=non_asset_env["comp_a_id"],
            due_date=out_of_range,
            estimated_duration=1.0,
            priority=1,
            status=0,
            archived=False,
            required_signature=False,
            is_demo=False,
        )
        pm = PreventiveMaintenance(
            title="Weekly inspection",
            company_id=non_asset_env["comp_a_id"],
            estimated_duration=1.0,
            priority=2,
            required_signature=False,
            is_demo=False,
            created_at=window_start - timedelta(days=30),
        )
        db.add_all([visible, hidden, later, pm])
        db.flush()
        schedule = Schedule(
            starts_on=in_range + timedelta(days=1),
            frequency=1,
            recurrence_type="WEEKLY",
            recurrence_based_on="SCHEDULED_DATE",
            preventive_maintenance_id=pm.id,
            disabled=False,
            is_demo=False,
        )
        db.add(schedule)
        db.flush()
        pm.schedule_id = schedule.id
        db.commit()
        visible_id = visible.id
        pm_id = pm.id

    body = {
        "start": window_start.isoformat(),
        "end": window_end.isoformat(),
        "filterFields": [
            {"field": "archived", "operation": "eq", "value": False},
            {
                "field": "priority",
                "operation": "in",
                "values": ["NONE", "LOW", "MEDIUM", "HIGH"],
                "enumName": "PRIORITY",
            },
            {
                "field": "status",
                "operation": "in",
                "values": ["OPEN", "IN_PROGRESS", "ON_HOLD"],
                "enumName": "STATUS",
            },
        ],
    }
    blank = client.post("/api/work-orders/events?companyId=", json=body)
    assert blank.status_code == 200, blank.text
    events = blank.json()
    titles = {event["event"]["title"] for event in events}
    assert "Visible in week" in titles
    assert "Other tenant" not in titles
    assert "Outside the visible week" not in titles
    visible_event = next(event for event in events if event["event"]["id"] == visible_id)
    assert visible_event["type"] == "WORK_ORDER"
    assert visible_event["endDate"]
    assert visible_event["event"]["priority"] == "HIGH"
    assert visible_event["event"]["status"] == "OPEN"
    pm_events = [
        event
        for event in events
        if event["type"] == "PREVENTIVE_MAINTENANCE" and event["event"]["id"] == pm_id
    ]
    assert pm_events
    assert pm_events[0]["type"] == "PREVENTIVE_MAINTENANCE"
    assert pm_events[0]["endDate"]

    omitted = client.post("/api/work-orders/events", json=body)
    assert omitted.status_code == 200
    denied = client.post(
        f"/api/work-orders/events?companyId={non_asset_env['comp_b_id']}",
        json=body,
    )
    assert denied.status_code == 403


def test_users_mini_excludes_requesters_unless_requested(non_asset_env):
    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    with session_local() as db:
        requester_role = Role(
            name="Requester",
            code=5,
            role_type=1,
            company_settings_id=non_asset_env["cs_a_id"],
        )
        settings = UserSettings()
        db.add_all([requester_role, settings])
        db.flush()
        requester = User(
            first_name="Rita",
            last_name="Requester",
            email="requester@alpha.test",
            username="requester@alpha.test",
            password="hashed_password",
            company_id=non_asset_env["comp_a_id"],
            role_id=requester_role.id,
            user_settings_id=settings.id,
            enabled=True,
        )
        db.add(requester)
        db.commit()

    workers = client.get("/api/users/mini")
    assert workers.status_code == 200
    assert "requester@alpha.test" not in {user["email"] for user in workers.json()}

    everyone = client.get("/api/users/mini?withRequesters=true")
    assert everyone.status_code == 200
    assert "requester@alpha.test" in {user["email"] for user in everyone.json()}


def test_work_order_completion_enforces_required_tasks_and_time(non_asset_env):
    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    with session_local() as db:
        configuration = WorkOrderConfiguration(
            company_settings_id=non_asset_env["cs_a_id"]
        )
        db.add(configuration)
        db.flush()
        db.add_all(
            [
                FieldConfiguration(
                    field_name="completeTasks",
                    field_type=2,
                    work_order_configuration_id=configuration.id,
                ),
                FieldConfiguration(
                    field_name="completeTime",
                    field_type=2,
                    work_order_configuration_id=configuration.id,
                ),
            ]
        )
        work_order = WorkOrder(
            title="Guarded completion",
            company_id=non_asset_env["comp_a_id"],
            status=0,
            priority=1,
            estimated_duration=1.0,
            archived=False,
            required_signature=False,
            is_demo=False,
            created_by=non_asset_env["user_a_id"],
        )
        db.add(work_order)
        db.flush()
        task_base = TaskBase(
            label="Inspect unit",
            task_type=0,
            company_id=non_asset_env["comp_a_id"],
        )
        db.add(task_base)
        db.flush()
        task = Task(
            company_id=non_asset_env["comp_a_id"],
            task_base_id=task_base.id,
            work_order_id=work_order.id,
            value="",
        )
        db.add(task)
        db.commit()
        work_order_id = work_order.id
        task_id = task.id

    incomplete = client.patch(
        f"/api/work-orders/{work_order_id}/change-status",
        json={"status": "COMPLETE"},
    )
    assert incomplete.status_code == 406
    assert "tasks" in incomplete.json()["message"].lower()

    with session_local() as db:
        task = db.get(Task, task_id)
        task.value = "Done"
        db.commit()
    no_time = client.patch(
        f"/api/work-orders/{work_order_id}/change-status",
        json={"status": "COMPLETE"},
    )
    assert no_time.status_code == 406
    assert "time" in no_time.json()["message"].lower()

    with session_local() as db:
        db.add(
            Labor(
                duration=30,
                work_order_id=work_order_id,
                company_id=non_asset_env["comp_a_id"],
            )
        )
        db.commit()
    completed = client.patch(
        f"/api/work-orders/{work_order_id}/change-status",
        json={"status": "COMPLETE"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETE"


def test_welcome_email_is_bilingual_and_an_invitation_creates_the_account(
    non_asset_env, monkeypatch
):
    from src.services import account_invitations, welcome_email

    sent: list[tuple[list[str], str, str]] = []
    monkeypatch.setattr(
        welcome_email,
        "send",
        lambda to, subject, text: sent.append((to, subject, text)) or 20,
    )
    monkeypatch.setattr(account_invitations, "send_welcome", welcome_email.send_welcome)

    subject, text = welcome_email.welcome_message(
        first_name="Elradie",
        role_name="Administrator",
        company_name="AJ CAFM",
    )
    assert len(subject) <= 200 and "\n" not in subject
    assert "Welcome to AJ CAFM" in subject
    assert "أهلاً بك في نظام إدارة المرافق" in subject
    assert "Hello Elradie," in text
    assert "مرحباً Elradie،" in text
    assert "Role: Administrator" in text
    assert "الدور: مسؤول" in text
    assert "Open AJ CAFM" in text
    assert "افتح النظام" in text

    client: TestClient = non_asset_env["client"]
    response = client.post(
        "/api/users/invite",
        json={
            "email": "elradie@aljazeera.net",
            "role": {"id": non_asset_env["role_a_id"]},
        },
    )
    assert response.status_code == 200
    assert response.json()["welcomed"] == ["elradie@aljazeera.net"]
    assert sent[-1][0] == ["elradie@aljazeera.net"]
    assert "Tenant Alpha" in sent[-1][2]
    assert "Admin Alpha" in sent[-1][2]
    assert "مرحباً Elradie،" in sent[-1][2]

    with non_asset_env["session_local"]() as db:
        created = db.scalar(select(User).where(User.email == "elradie@aljazeera.net"))
        assert created is not None
        assert created.role_id == non_asset_env["role_a_id"]
        assert created.company_id == non_asset_env["comp_a_id"]
        assert created.enabled is True


def test_send_work_order_report_uses_canvas_email(non_asset_env, monkeypatch):
    client: TestClient = non_asset_env["client"]
    session_local = non_asset_env["session_local"]
    with session_local() as db:
        work_order = WorkOrder(
            title="AHU inspection",
            description="Inspect the air handling unit.",
            company_id=non_asset_env["comp_a_id"],
            status=0,
            priority=2,
            estimated_duration=2.0,
            archived=False,
            required_signature=False,
            is_demo=False,
            created_by=non_asset_env["user_a_id"],
        )
        customer = Customer(
            name="Facilities Client",
            email="facilities@example.test",
            company_id=non_asset_env["comp_a_id"],
        )
        db.add_all([work_order, customer])
        db.commit()
        work_order_id = work_order.id
        customer_id = customer.id

    sent: dict[str, object] = {}

    def fake_send(to: list[str], subject: str, text: str) -> int:
        sent.update(to=to, subject=subject, text=text)
        return 19

    monkeypatch.setattr(work_orders_pm_routes, "send_email", fake_send)
    response = client.post(
        f"/api/work-orders/{work_order_id}/report/send",
        json={
            "customers": [{"id": customer_id}],
            "message": "Please review this work order.",
            "config": {"workOrderInformation": True},
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert sent["to"] == ["facilities@example.test"]
    assert "AHU inspection" in str(sent["subject"])
    assert "Please review this work order." in str(sent["text"])

    def refuse(*_args, **_kwargs):
        raise work_orders_pm_routes.EmailRefused("403: email.recipient")

    monkeypatch.setattr(work_orders_pm_routes, "send_email", refuse)
    refused = client.post(
        f"/api/work-orders/{work_order_id}/report/send",
        json={"customers": [{"id": customer_id}]},
    )
    assert refused.status_code == 200
    assert refused.json() == {
        "success": False,
        "message": "403: email.recipient",
    }

