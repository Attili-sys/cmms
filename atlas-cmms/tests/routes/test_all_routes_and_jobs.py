"""Comprehensive tests for all Phase 6 route groups, Phase 3 deps/auth/license, Phase 7 jobs, and Phase 10 contracts."""

from __future__ import annotations

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.deps.db import get_db
from src.jobs.cleanup import cleanup_expired_tokens
from src.jobs.pm_generator import generate_due_work_orders
from src.models import Base
from src.models._base import utcnow
from src.models.company import Company
from src.models.enums import PlanFeatures
from src.models.pm_schedule import PreventiveMaintenance, Schedule
from src.models.users import Role, User, VerificationToken
from src.services.license_service import LicenseService, serialize_subscription_plan


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    client = TestClient(app, headers={"X-Forwarded-Email": "admin@acme.test", "X-Forwarded-User": "Admin User"})
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def test_license_service_unrestricted_self_hosted() -> None:
    assert LicenseService.is_unrestricted_self_hosted() is True
    assert LicenseService.is_license_valid() is True
    for feat in PlanFeatures:
        assert LicenseService.has_feature(feat) is True
    plan_dict = serialize_subscription_plan(None)
    assert set(plan_dict["features"]) == {f.value for f in PlanFeatures}


def test_sso_bootstrap_and_auth_endpoints(api_client: TestClient, db_session: Session) -> None:
    # First request on empty DB bootstraps Company, ROLE_SUPER_ADMIN, and first User
    resp = api_client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@acme.test"
    assert data["ownsCompany"] is True
    assert data["role"]["name"] == "ROLE_SUPER_ADMIN"

    # Subsequent SSO user auto-joins the same company
    resp2 = api_client.get(
        "/api/auth/me",
        headers={"X-Forwarded-Email": "tech@acme.test", "X-Forwarded-User": "Tech Worker"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["email"] == "tech@acme.test"
    assert data2["companyId"] == data["companyId"]
    assert data2["ownsCompany"] is False

    # Signin & license validity
    assert api_client.post("/api/auth/signin", json={}).status_code == 200
    lic = api_client.get("/api/license/validity").json()
    assert lic["valid"] is True
    assert lic["unrestricted"] is True

    plans = api_client.get("/api/subscription-plans").json()
    assert len(plans) >= 1
    assert len(plans[0]["features"]) == len(PlanFeatures)


def test_api_key_bearer_auth(api_client: TestClient, db_session: Session) -> None:
    # Bootstrap first user
    me = api_client.get("/api/auth/me").json()
    # Create API key
    ak_resp = api_client.post("/api/api-keys", json={"name": "Integration Key"})
    assert ak_resp.status_code == 200
    ak_data = ak_resp.json()
    token = ak_data["code"]

    # Authenticate using Bearer token without SSO headers
    anon_client = TestClient(app)
    resp = anon_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == me["id"]

    # Revoke API key -> 401
    rev_resp = api_client.patch(f"/api/api-keys/{ak_data['id']}/revoke")
    assert rev_resp.status_code == 200
    resp_after = anon_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_after.status_code == 401


def test_locations_assets_categories_vendors_customers(api_client: TestClient) -> None:
    # Create Location
    loc_resp = api_client.post("/api/locations", json={"name": "Main Plant", "address": "100 Industrial Way"})
    assert loc_resp.status_code == 200
    loc_id = loc_resp.json()["id"]

    # Create child Location
    child_loc = api_client.post("/api/locations", json={"name": "Floor 1", "parentLocation": {"id": loc_id}}).json()
    assert child_loc["parentLocationId"] == loc_id

    children = api_client.get(f"/api/locations/children/{loc_id}").json()
    assert len(children) == 1
    assert children[0]["name"] == "Floor 1"

    loc_root_page = api_client.get("/api/locations/children/0/paginated?page=0&size=10").json()
    assert loc_root_page["totalElements"] == 1
    assert loc_root_page["content"][0]["id"] == loc_id
    assert loc_root_page["content"][0]["hasChildren"] is True

    # Create AssetCategory
    cat = api_client.post("/api/asset-categories", json={"name": "Rotating Equipment"}).json()
    assert cat["name"] == "Rotating Equipment"

    # Create Asset
    asset = api_client.post(
        "/api/assets",
        json={"name": "Main Compressor", "location": {"id": loc_id}, "category": {"id": cat["id"]}},
    ).json()
    assert asset["name"] == "Main Compressor"
    assert asset["customId"].startswith("A")

    asset_root_page = api_client.get("/api/assets/children/0/paginated?page=0&size=10").json()
    assert asset_root_page["totalElements"] == 1
    assert asset_root_page["content"][0]["name"] == "Main Compressor"

    assets_mini_empty_loc = api_client.get("/api/assets/mini?locationId=")
    assert assets_mini_empty_loc.status_code == 200
    assert len(assets_mini_empty_loc.json()) == 1

    # Search Assets
    search_res = api_client.post("/api/assets/search", json={"pageNum": 0, "pageSize": 10}).json()
    assert search_res["totalElements"] == 1
    assert search_res["content"][0]["name"] == "Main Compressor"

    # Vendors & Customers
    vendor = api_client.post("/api/vendors", json={"companyName": "SKF Bearings", "name": "John Doe"}).json()
    assert vendor["companyName"] == "SKF Bearings"
    cust = api_client.post("/api/customers", json={"name": "Airport Authority"}).json()
    assert cust["name"] == "Airport Authority"


def test_parts_purchase_orders_tasks_checklists(api_client: TestClient) -> None:
    # Create Part
    part = api_client.post(
        "/api/parts",
        json={"name": "Oil Filter", "cost": 25.5, "quantity": 10, "barcode": "FILT-001", "unit": "pcs"},
    ).json()
    assert part["name"] == "Oil Filter"

    # Lookup by barcode
    by_bc = api_client.get("/api/parts/barcode/FILT-001").json()
    assert by_bc["id"] == part["id"]

    # MultiParts
    mp = api_client.post("/api/multi-parts", json={"name": "Service Kit", "parts": [{"id": part["id"]}]}).json()
    assert len(mp["parts"]) == 1

    # PurchaseOrder + respond
    po = api_client.post("/api/purchase-orders", json={"name": "Q4 Restock"}).json()
    po_approved = api_client.patch(f"/api/purchase-orders/{po['id']}/respond", json={"approved": True}).json()
    assert po_approved["status"] == "APPROVED"

    # Checklist
    cl = api_client.post("/api/checklists", json={"name": "Monthly Inspection"}).json()
    assert cl["name"] == "Monthly Inspection"


def test_work_orders_pdf_labors_requests_meters_workflows(api_client: TestClient) -> None:
    # Create WorkOrder
    wo = api_client.post(
        "/api/work-orders",
        json={"title": "Replace Pump Seal", "priority": "HIGH", "estimatedDuration": 2.5},
    ).json()
    assert wo["title"] == "Replace Pump Seal"
    assert wo["priority"] == "HIGH"
    assert wo["customId"].startswith("WO")

    # Change status to COMPLETE
    wo_done = api_client.patch(
        f"/api/work-orders/{wo['id']}/change-status",
        json={"status": "COMPLETE"},
    ).json()
    assert wo_done["status"] == "COMPLETE"

    # Export PDF
    pdf_resp = api_client.get(f"/api/work-orders/pdf/{wo['id']}")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")

    # Labor timer
    labor = api_client.post(f"/api/labors/controlling-time-timer?action=START&workOrderId={wo['id']}").json()
    assert labor["workOrderId"] == wo["id"]

    # Request creation & approval -> creates WorkOrder
    req = api_client.post("/api/requests", json={"title": "Leaking pipe in lobby", "priority": "MEDIUM"}).json()
    assert req["customId"].startswith("R")
    assert api_client.get("/api/requests/pending").json() == {"success": True, "message": "1"}
    assert api_client.get("/api/work-orders/urgent").json()["success"] is True

    approved_wo = api_client.patch(f"/api/requests/{req['id']}/approve").json()
    assert approved_wo["title"] == "Leaking pipe in lobby"
    assert approved_wo["parentRequestId"] == req["id"]
    assert api_client.get("/api/requests/pending").json() == {"success": True, "message": "0"}

    # Meter & Reading trigger -> creates WorkOrder
    meter = api_client.post("/api/meters", json={"name": "Run Hours", "unit": "h", "updateFrequency": 1}).json()
    api_client.post(
        "/api/work-order-meter-triggers",
        json={"title": "500h Overhaul", "meter": {"id": meter["id"]}, "value": 500, "triggerCondition": 0},
    )
    api_client.post("/api/readings", json={"meter": {"id": meter["id"]}, "value": 550.0})

    wos_search = api_client.post("/api/work-orders/search", json={"pageNum": 0, "pageSize": 20}).json()
    titles = {w["title"] for w in wos_search["content"]}
    assert "500h Overhaul" in titles

    # Workflows
    wf = api_client.post(
        "/api/workflows",
        json={
            "title": "Auto High Priority",
            "mainCondition": 0,
            "action": {"workOrderAction": 0, "priority": 3},
        },
    ).json()
    assert wf["title"] == "Auto High Priority"

    # Analytics
    overview = api_client.post("/api/analytics/work-orders/complete/overview", json={}).json()
    assert overview["total"] >= 3
    assert overview["complete"] >= 1

    # Export CSV
    csv_resp = api_client.get("/api/export/work-orders")
    assert csv_resp.status_code == 200
    assert "Replace Pump Seal" in csv_resp.text

    # Import entities
    imp_resp = api_client.post("/api/import/locations", json=[{"name": "Imported Warehouse"}]).json()
    assert imp_resp["created"] == 1


def test_background_jobs(db_session: Session) -> None:
    # Seed Company & User
    comp = Company(name="Job Test Co", employees_count=5)
    db_session.add(comp)
    db_session.flush()
    role = Role(name="Admin", role_type=0, paid=True)
    db_session.add(role)
    db_session.flush()
    user = User(
        email="job@test.com",
        username="job@test.com",
        first_name="Job",
        last_name="Runner",
        company_id=comp.id,
        role_id=role.id,
        enabled=True,
        password="",
    )
    db_session.add(user)
    db_session.flush()

    # 1. PM Generator job
    sched = Schedule(
        starts_on=utcnow() - timedelta(days=2),
        next_due_date=utcnow() - timedelta(hours=1),
        frequency=7,
        disabled=False,
        recurrence_type="DAILY",
        recurrence_based_on="SCHEDULED_DATE",
    )
    db_session.add(sched)
    db_session.flush()
    pm = PreventiveMaintenance(
        name="Weekly Lube",
        title="Lubricate Bearings",
        priority=1,
        company_id=comp.id,
        primary_user_id=user.id,
        schedule_id=sched.id,
    )
    db_session.add(pm)
    db_session.commit()

    generated = generate_due_work_orders(db_session, now=utcnow())
    assert len(generated) == 1
    assert generated[0].title == "Lubricate Bearings"

    # 2. Cleanup job
    expired_token = VerificationToken(
        token="tok123",
        user_id=user.id,
        expiry_date=utcnow() - timedelta(hours=2),
    )
    db_session.add(expired_token)
    db_session.commit()
    cleanup_res = cleanup_expired_tokens(db_session, now=utcnow())
    assert cleanup_res["verification_tokens"] >= 1

