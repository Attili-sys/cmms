"""Comprehensive regression tests for all 30 non-asset backend & security audit fixes."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.deps.db import get_db
from src.jobs.pm_generator import generate_due_work_orders
from src.models import (
    Asset as AssetModel,
    Base,
    Company,
    CompanySettings,
    GeneralPreferences,
    Location as LocationModel,
    Role,
    Subscription,
    SubscriptionPlan,
    User,
)
from src.models.associations import (
    role_create_permissions,
    role_edit_other_permissions,
    role_view_other_permissions,
    role_view_permissions,
)
from src.models.enums import PermissionEntity


@pytest.fixture(scope="module")
def audit_env() -> Iterator[dict]:
    """Isolated test database with Tenant A, Tenant B, Admin User, and Limited Tech User."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_db() -> Iterator[Session]:
        with testing_session_local() as db:
            yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-authentik-email": "admin@tenant-a.local",
                "X-authentik-name": "Tenant A Admin",
            },
        ) as admin_client:
            me = admin_client.get("/api/auth/me").json()
            company_a_id = me["companyId"]
            admin_user_id = me["id"]

            with testing_session_local() as db:
                plan_b = SubscriptionPlan(
                    name="Standard",
                    code="STANDARD",
                    monthly_cost_per_user=0.0,
                    yearly_cost_per_user=0.0,
                )
                db.add(plan_b)
                db.flush()
                sub_b = Subscription(
                    users_count=10,
                    monthly=True,
                    activated=True,
                    downgrade_needed=False,
                    upgrade_needed=False,
                    subscription_plan_id=plan_b.id,
                )
                db.add(sub_b)
                db.flush()
                cs_b = CompanySettings()
                db.add(cs_b)
                db.flush()
                comp_b = Company(
                    name="Tenant B Corp",
                    company_settings_id=cs_b.id,
                    subscription_id=sub_b.id,
                )
                db.add(comp_b)
                db.flush()
                cs_b.company_id = comp_b.id
                company_b_id = comp_b.id
                sub_b_id = sub_b.id

                comp_a = db.get(Company, company_a_id)
                cs_a_id = comp_a.company_settings_id

                # Role with only WORK_ORDERS and REQUESTS view/create (no SETTINGS, no ANALYTICS, no PEOPLE_AND_TEAMS)
                tech_role = Role(
                    name="Limited Tech",
                    company_settings_id=cs_a_id,
                    role_type=1,
                    code=2,
                    paid=True,
                )
                db.add(tech_role)
                db.flush()
                perm_entities = list(PermissionEntity)
                for perm in (PermissionEntity.WORK_ORDERS, PermissionEntity.REQUESTS):
                    ord_val = perm_entities.index(perm)
                    db.execute(
                        role_view_permissions.insert().values(
                            role_id=tech_role.id, view_permissions=ord_val
                        )
                    )
                    db.execute(
                        role_view_other_permissions.insert().values(
                            role_id=tech_role.id, view_other_permissions=ord_val
                        )
                    )
                    db.execute(
                        role_create_permissions.insert().values(
                            role_id=tech_role.id, create_permissions=ord_val
                        )
                    )

                # Sub-admin role with SETTINGS view permission (and WORK_ORDERS view/create), but NOT PEOPLE_AND_TEAMS
                settings_role = Role(
                    name="Settings Manager",
                    company_settings_id=cs_a_id,
                    role_type=1,
                    code=6,
                    paid=True,
                )
                db.add(settings_role)
                db.flush()
                for perm in (PermissionEntity.SETTINGS, PermissionEntity.WORK_ORDERS):
                    ord_val = perm_entities.index(perm)
                    db.execute(
                        role_view_permissions.insert().values(
                            role_id=settings_role.id, view_permissions=ord_val
                        )
                    )
                    db.execute(
                        role_edit_other_permissions.insert().values(
                            role_id=settings_role.id, edit_other_permissions=ord_val
                        )
                    )

                tech_user = User(
                    email="tech@tenant-a.local",
                    username="tech@tenant-a.local",
                    first_name="Tech",
                    last_name="One",
                    password="sso",
                    company_id=company_a_id,
                    role_id=tech_role.id,
                    enabled=True,
                    enabled_in_subscription=True,
                    created_via_sso=True,
                    owns_company=False,
                    rate=50,
                )
                settings_user = User(
                    email="settings@tenant-a.local",
                    username="settings@tenant-a.local",
                    first_name="Settings",
                    last_name="Mgr",
                    password="sso",
                    company_id=company_a_id,
                    role_id=settings_role.id,
                    enabled=True,
                    enabled_in_subscription=True,
                    created_via_sso=True,
                    owns_company=False,
                    rate=60,
                )
                tenant_b_user = User(
                    email="user@tenant-b.local",
                    username="user@tenant-b.local",
                    first_name="TenantB",
                    last_name="User",
                    password="sso",
                    company_id=company_b_id,
                    role_id=tech_role.id,
                    enabled=True,
                    enabled_in_subscription=True,
                    created_via_sso=True,
                    owns_company=True,
                    rate=40,
                )
                loc_b = LocationModel(name="Tenant B Site", company_id=company_b_id)
                asset_b = AssetModel(name="Tenant B Asset", company_id=company_b_id)
                db.add_all([tech_user, settings_user, tenant_b_user, loc_b, asset_b])
                db.commit()
                tech_user_id = tech_user.id
                tenant_b_user_id = tenant_b_user.id
                asset_b_id = asset_b.id

            yield {
                "admin_client": admin_client,
                "session_local": testing_session_local,
                "company_a_id": company_a_id,
                "company_b_id": company_b_id,
                "sub_b_id": sub_b_id,
                "admin_user_id": admin_user_id,
                "tech_user_id": tech_user_id,
                "tenant_b_user_id": tenant_b_user_id,
                "asset_b_id": asset_b_id,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_auth_and_rbac_protections(audit_env: dict) -> None:
    """Verify AUTH-P0-01 to AUTH-P0-05 and SYS-P0-01 to SYS-P0-02."""
    admin_client: TestClient = audit_env["admin_client"]
    sub_b_id: int = audit_env["sub_b_id"]
    admin_user_id: int = audit_env["admin_user_id"]
    tech_user_id: int = audit_env["tech_user_id"]
    tenant_b_user_id: int = audit_env["tenant_b_user_id"]

    # AUTH-P0-01: Cross-tenant subscription access blocked
    assert admin_client.get(f"/api/subscriptions/{sub_b_id}").status_code == 403
    assert admin_client.patch(f"/api/subscriptions/{sub_b_id}", json={"usersCount": 999}).status_code == 403

    # AUTH-P0-02: Admin cannot disable or delete self or company owner
    assert admin_client.patch(f"/api/users/{admin_user_id}/disable").status_code == 406
    assert admin_client.delete(f"/api/users/{admin_user_id}").status_code == 406

    # AUTH-P0-05: Cross-tenant user injection into Team blocked
    assert (
        admin_client.post(
            "/api/teams",
            json={"name": "Cross Tenant Team", "users": [{"id": tenant_b_user_id}]},
        ).status_code
        == 400
    )

    with TestClient(
        app,
        headers={
            "X-authentik-email": "tech@tenant-a.local",
            "X-authentik-name": "Tech One",
        },
    ) as tech_client:
        # AUTH-P0-02: Non-privileged user cannot create user, disable user, or escalate own role/company
        assert tech_client.post("/api/users", json={"email": "new@tenant-a.local"}).status_code == 403
        assert tech_client.patch(f"/api/users/{admin_user_id}/disable").status_code == 403
        self_patch = tech_client.patch(
            f"/api/users/{tech_user_id}",
            json={"firstName": "TechRenamed", "ownsCompany": True, "roleId": 1},
        )
        assert self_patch.status_code == 200
        assert self_patch.json()["firstName"] == "TechRenamed"
        assert self_patch.json()["ownsCompany"] is False

        # AUTH-P0-03 & AUTH-P0-04: Tech without SETTINGS cannot create roles or mutate company settings
        assert tech_client.post("/api/roles", json={"name": "Rogue Role"}).status_code == 403
        assert tech_client.patch("/api/ui-configurations", json={"requests": False}).status_code == 403

        # SYS-P0-01: Tech without SETTINGS cannot create CustomField or Workflow
        assert tech_client.post("/api/custom-fields", json={"name": "Rogue CF"}).status_code == 403
        assert tech_client.post("/api/workflows", json={"title": "Rogue WF", "mainCondition": "WORK_ORDER_CREATED"}).status_code == 403

    with TestClient(
        app,
        headers={
            "X-authentik-email": "settings@tenant-a.local",
            "X-authentik-name": "Settings Mgr",
        },
    ) as settings_client:
        # SYS-P0-02: Role with SETTINGS in viewPermissions CAN create/edit SETTINGS-scoped entities (CustomField)
        cf_resp = settings_client.post(
            "/api/custom-fields",
            json={"label": "Valid CF", "fieldType": "SHORT_TEXT", "entityType": "WORK_ORDER"},
        )
        assert cf_resp.status_code == 200

        # AUTH-P0-03: Settings user cannot grant permissions they do not possess (e.g. PEOPLE_AND_TEAMS)
        escalate_role = settings_client.post(
            "/api/roles",
            json={"name": "Escalated Role", "createPermissions": ["PEOPLE_AND_TEAMS"]},
        )
        assert escalate_role.status_code == 403


def test_work_orders_comments_relations_and_triggers(audit_env: dict) -> None:
    """Verify WO-P0-01 to WO-P1-04."""
    admin_client: TestClient = audit_env["admin_client"]
    session_local = audit_env["session_local"]
    company_a_id: int = audit_env["company_a_id"]
    tech_user_id: int = audit_env["tech_user_id"]

    # Enable autoAssignWorkOrders and create WO as tech
    with session_local() as db:
        comp_a = db.get(Company, company_a_id)
        gp = db.scalar(
            select(GeneralPreferences).where(
                GeneralPreferences.company_settings_id == comp_a.company_settings_id
            )
        )
        if gp:
            gp.auto_assign_work_orders = True
            db.commit()

    with TestClient(
        app,
        headers={
            "X-authentik-email": "tech@tenant-a.local",
            "X-authentik-name": "Tech One",
        },
    ) as tech_client:
        wo_resp = tech_client.post("/api/work-orders", json={"title": "Auto Assigned WO"})
        assert wo_resp.status_code == 200
        wo1 = wo_resp.json()
        assert wo1["primaryUser"]["id"] == tech_user_id

    # WO-P0-02 & WO-P1-02: Comment payload {"text": ...}, count contract, and flat list with histories
    c_resp = admin_client.post(
        "/api/comments",
        json={"workOrder": {"id": wo1["id"]}, "text": "Checked bearings"},
    )
    assert c_resp.status_code == 200
    c_dto = c_resp.json()
    assert c_dto["text"] == "Checked bearings"
    assert c_dto["user"] is not None

    cnt_resp = admin_client.get(f"/api/comments/count/{wo1['id']}")
    assert cnt_resp.status_code == 200
    assert cnt_resp.json() == {"count": 1, "withFilesCount": 0}

    hist_resp = admin_client.post(
        f"/api/comments/search/{wo1['id']}",
        json={"pageNum": 0, "pageSize": 10},
    )
    assert hist_resp.status_code == 200
    assert isinstance(hist_resp.json(), list)
    assert any(item.get("text") == "Checked bearings" for item in hist_resp.json())

    # Comment sets firstTimeToReact on WO
    wo1_refreshed = admin_client.get(f"/api/work-orders/{wo1['id']}").json()
    assert wo1_refreshed["firstTimeToReact"] is not None

    # WO-P0-03: Relation self-link rejected (406), inverse normalized (BLOCKS -> BLOCKED_BY), duplicate rejected (406)
    wo2 = admin_client.post("/api/work-orders", json={"title": "Second WO"}).json()
    assert (
        admin_client.post(
            "/api/relations",
            json={
                "parent": {"id": wo1["id"]},
                "child": {"id": wo1["id"]},
                "relationType": "RELATED_TO",
            },
        ).status_code
        == 406
    )
    rel_resp = admin_client.post(
        "/api/relations",
        json={
            "parent": {"id": wo1["id"]},
            "child": {"id": wo2["id"]},
            "relationType": "BLOCKED_BY",
        },
    )
    assert rel_resp.status_code == 200
    rel = rel_resp.json()
    assert rel["relationType"] == "BLOCKS"
    assert rel["parent"]["id"] == wo2["id"]
    assert rel["child"]["id"] == wo1["id"]

    # Duplicate relation rejected
    assert (
        admin_client.post(
            "/api/relations",
            json={
                "parent": {"id": wo1["id"]},
                "child": {"id": wo2["id"]},
                "relationType": "BLOCKED_BY",
            },
        ).status_code
        == 406
    )


def test_pm_completed_date_and_parts_barcode_restock_workflows(audit_env: dict) -> None:
    """Verify PM-P0-01, PM-P1-01, PO-P0-01, PO-P0-02, WF-P0-01, WF-P0-02."""
    admin_client: TestClient = audit_env["admin_client"]
    session_local = audit_env["session_local"]
    tech_user_id: int = audit_env["tech_user_id"]

    # PM-P0-01: PM with recurrenceBasedOn=COMPLETED_DATE does not advance next_due_date until WO completes
    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    pm_resp = admin_client.post(
        "/api/preventive-maintenances",
        json={
            "name": "Completed Date PM",
            "title": "PM Generated WO",
            "recurrenceBasedOn": "COMPLETED_DATE",
            "schedule": {
                "frequency": 7,
                "recurrenceType": "DAILY",
                "startsOn": past_due,
                "nextDueDate": past_due,
            },
        },
    )
    assert pm_resp.status_code == 200
    pm = pm_resp.json()

    with session_local() as db:
        created_wos = generate_due_work_orders(db)
        assert len(created_wos) >= 1

    pm_after_gen = admin_client.get(f"/api/preventive-maintenances/{pm['id']}").json()
    # nextDueDate stays at past_due while generated WO is still OPEN
    assert pm_after_gen["schedule"]["nextDueDate"].startswith(past_due[:10])

    # PO-P0-01: Duplicate part barcode rejected with 406
    p1_resp = admin_client.post(
        "/api/parts",
        json={"name": "Filter Element", "barcode": "BC-PART-100", "quantity": 10, "minQuantity": 5, "cost": 15.0},
    )
    assert p1_resp.status_code == 200
    part_id = p1_resp.json()["id"]

    assert (
        admin_client.post(
            "/api/parts",
            json={"name": "Duplicate Barcode Part", "barcode": "BC-PART-100", "quantity": 1},
        ).status_code
        == 406
    )

    # PO-P0-02: Negative restock rejected (406); positive restock succeeds
    assert (
        admin_client.patch(f"/api/parts/{part_id}/restock", json={"quantity": -5}).status_code
        == 406
    )
    restock_ok = admin_client.patch(f"/api/parts/{part_id}/restock", json={"quantity": 5})
    assert restock_ok.status_code == 200
    assert restock_ok.json()["quantity"] == 15

    # WF-P0-01 & WF-P0-02: Create workflow, then PATCH its action and secondaryConditions
    wf_create = admin_client.post(
        "/api/workflows",
        json={
            "title": "Auto High Priority WF",
            "mainCondition": "WORK_ORDER_CREATED",
            "secondaryConditions": [{"workOrderCondition": "PRIORITY_IS", "priority": "LOW"}],
            "action": {"workOrderAction": "ASSIGN_PRIORITY", "priority": "MEDIUM"},
        },
    )
    assert wf_create.status_code == 200
    wf_id = wf_create.json()["id"]

    # Patch workflow to assign user and set priority HIGH when title contains 'CRITICAL'
    wf_patch = admin_client.patch(
        f"/api/workflows/{wf_id}",
        json={
            "title": "Auto High Priority WF Patched",
            "secondaryConditions": [
                {"workOrderCondition": "TITLE_CONTAINS", "label": "CRITICAL"}
            ],
            "action": {
                "workOrderAction": "ASSIGN_PRIORITY",
                "priority": "HIGH",
                "user": {"id": tech_user_id},
            },
        },
    )
    assert wf_patch.status_code == 200
    wf_patched = wf_patch.json()
    assert len(wf_patched["secondaryConditions"]) == 1
    assert wf_patched["secondaryConditions"][0]["workOrderCondition"] == "TITLE_CONTAINS"
    assert wf_patched["action"]["priority"] == "HIGH"
    assert wf_patched["action"]["user"]["id"] == tech_user_id

    # Verify patched workflow fires on matching WO and does NOT fire on non-matching WO
    wo_match = admin_client.post("/api/work-orders", json={"title": "CRITICAL Boiler Leak"}).json()
    assert wo_match["priority"] == "HIGH"
    wo_non_match = admin_client.post("/api/work-orders", json={"title": "Routine Check"}).json()
    assert wo_non_match["priority"] == "NONE"


def test_meters_requests_search_import_export_and_analytics(audit_env: dict) -> None:
    """Verify MTR-P0-01, REQ-P0-02, REQ-P1-01, IMP-P1-01, IMP-P1-02, AN-P0-01 to AN-P1-01."""
    admin_client: TestClient = audit_env["admin_client"]
    tech_user_id: int = audit_env["tech_user_id"]

    # MTR-P0-01: WorkOrderMeterTrigger LESS_THAN (0) vs MORE_THAN (1) and M2M hydration
    m_resp = admin_client.post(
        "/api/meters",
        json={"name": "Tank Level", "unit": "%", "updateFrequency": 1},
    )
    assert m_resp.status_code == 200
    meter_id = m_resp.json()["id"]

    trig_resp = admin_client.post(
        "/api/work-order-meter-triggers",
        json={
            "name": "Low Level Trigger",
            "title": "Refill Tank WO",
            "meter": {"id": meter_id},
            "triggerCondition": "LESS_THAN",
            "value": 20,
            "assignedTo": [{"id": tech_user_id}],
        },
    )
    assert trig_resp.status_code == 200
    trig = trig_resp.json()
    assert trig["triggerCondition"] == "LESS_THAN"
    assert len(trig["assignedTo"]) == 1 and trig["assignedTo"][0]["id"] == tech_user_id

    # Reading of 50 (> 20) should NOT trigger LESS_THAN 20
    admin_client.post("/api/readings", json={"meter": {"id": meter_id}, "value": 50})
    wos_after_50 = admin_client.post("/api/work-orders/search", json={"pageNum": 0, "pageSize": 50}).json()["content"]
    assert not any(w["title"] == "Refill Tank WO" for w in wos_after_50)

    # Reading of 10 (< 20) MUST trigger LESS_THAN 20 and copy assignedTo
    admin_client.post("/api/readings", json={"meter": {"id": meter_id}, "value": 10})
    wos_after_10 = admin_client.post("/api/work-orders/search", json={"pageNum": 0, "pageSize": 50}).json()["content"]
    refill_wo = next((w for w in wos_after_10 if w["title"] == "Refill Tank WO"), None)
    assert refill_wo is not None
    assert len(refill_wo["assignedTo"]) == 1 and refill_wo["assignedTo"][0]["id"] == tech_user_id

    # REQ-P0-02 & REQ-P1-01: Request virtual status search and CustomFieldValue cloning on approve
    cf_id = admin_client.post("/api/custom-fields", json={"name": "Room Number"}).json()["id"]
    req = admin_client.post(
        "/api/requests",
        json={
            "title": "Broken AC Request",
            "customFieldValues": [{"customField": {"id": cf_id}, "value": "Room 302"}],
        },
    ).json()

    pending_search = admin_client.post(
        "/api/requests/search",
        json={
            "pageNum": 0,
            "pageSize": 10,
            "filterFields": [{"field": "status", "operation": "in", "values": ["PENDING"]}],
        },
    )
    assert pending_search.status_code == 200
    assert any(r["id"] == req["id"] for r in pending_search.json()["content"])

    approved_wo = admin_client.patch(f"/api/requests/{req['id']}/approve").json()
    assert len(approved_wo["customFieldValues"]) == 1
    assert approved_wo["customFieldValues"][0]["value"] == "Room 302"

    approved_search = admin_client.post(
        "/api/requests/search",
        json={
            "pageNum": 0,
            "pageSize": 10,
            "filterFields": [{"field": "status", "operation": "in", "values": ["APPROVED"]}],
        },
    )
    assert approved_search.status_code == 200
    assert any(r["id"] == req["id"] for r in approved_search.json()["content"])

    # IMP-P1-01: Import parts with YES/NO nonStock and relational names
    imp_parts = admin_client.post(
        "/api/import/parts",
        json=[
            {
                "name": "Imported Consumable Seal",
                "cost": 5.5,
                "quantity": 100,
                "nonStock": "YES",
                "category": "Seals",
                "assignedToEmails": ["tech@tenant-a.local"],
            }
        ],
    )
    assert imp_parts.status_code == 200
    assert imp_parts.json()["created"] == 1
    all_parts = admin_client.post("/api/parts/search", json={"pageNum": 0, "pageSize": 50}).json()["content"]
    seal = next(p for p in all_parts if p["name"] == "Imported Consumable Seal")
    assert seal["nonStock"] is True
    assert seal["category"]["name"] == "Seals"
    assert len(seal["assignedTo"]) == 1 and seal["assignedTo"][0]["id"] == tech_user_id

    # AN-P0-01 to AN-P1-01: Analytics contracts and RBAC
    assert isinstance(admin_client.post("/api/analytics/work-orders/statuses", json={}).json(), list)
    assert isinstance(admin_client.post("/api/analytics/work-orders/incomplete/statuses", json={}).json(), dict)
    hours_dto = admin_client.post("/api/analytics/work-orders/hours", json={}).json()
    assert "estimated" in hours_dto and "actual" in hours_dto
    inc_prio = admin_client.post("/api/analytics/work-orders/incomplete/priority", json={}).json()
    assert "high" in inc_prio and "count" in inc_prio["high"]
    assert isinstance(admin_client.post("/api/analytics/work-orders/incomplete/age/assets", json={}).json(), list)
    assert isinstance(admin_client.post("/api/analytics/work-orders/complete/counts/primaryUser", json={}).json(), list)

    with TestClient(
        app,
        headers={
            "X-authentik-email": "tech@tenant-a.local",
            "X-authentik-name": "Tech One",
        },
    ) as tech_client:
        # Tech without ANALYTICS view permission receives 403 on analytics overview
        assert tech_client.post("/api/analytics/work-orders/complete/overview", json={}).status_code == 403


def test_deep_parity_remaining_fixes(audit_env: dict) -> None:
    """Verify P0-05 (RequestPortal FK cascades), P1-06 (In-App Notifications & user scoping), P1-10 (Subscription upgrade/downgrade), and P1-11 (License state entitlements)."""
    from src.models.requests import RequestPortal, RequestPortalField

    admin_client: TestClient = audit_env["admin_client"]
    tech_user_id: int = audit_env["tech_user_id"]

    # 1. P0-05: RequestPortal & RequestPortalField foreign key ondelete metadata
    rp_fks = {fk.parent.name: fk.ondelete for fk in RequestPortal.__table__.foreign_keys}
    assert rp_fks["company_id"] == "CASCADE"

    rpf_fks = {fk.parent.name: fk.ondelete for fk in RequestPortalField.__table__.foreign_keys}
    assert rpf_fks["company_id"] == "CASCADE"
    assert rpf_fks["location_id"] == "SET NULL"
    assert rpf_fks["asset_id"] == "SET NULL"
    assert rpf_fks["request_portal_id"] == "CASCADE"

    # 2. P1-10: POST /subscriptions/upgrade and GET /subscriptions/downgrade
    up_res = admin_client.post("/api/subscriptions/upgrade", json=10)
    assert up_res.status_code == 200
    assert up_res.json()["success"] is True
    assert "url" in up_res.json() and "message" in up_res.json()

    down_res = admin_client.get("/api/subscriptions/downgrade?usersIds=1,2")
    assert down_res.status_code == 200
    assert down_res.json()["success"] is True

    # 3. P1-11: GET /license/state returns valid, entitlements, expirationDate, planName
    lic_res = admin_client.get("/api/license/state")
    assert lic_res.status_code == 200
    lic_body = lic_res.json()
    assert lic_body["valid"] is True
    assert lic_body["planName"] == "ENTERPRISE"
    assert "expirationDate" in lic_body
    assert isinstance(lic_body["entitlements"], list)
    assert "WORKFLOW" in lic_body["entitlements"]
    assert "RESOURCE_PLANNING" in lic_body["entitlements"]
    assert len(lic_body["entitlements"]) == 34

    # 4. P1-06: In-App Notification creation and strict per-user scoping
    # Admin creates a WorkOrder assigned to Tech One
    wo = admin_client.post(
        "/api/work-orders",
        json={
            "title": "Pump Bearing Replacement",
            "primaryUser": {"id": tech_user_id},
        },
    ).json()

    with TestClient(
        app,
        headers={
            "X-authentik-email": "tech@tenant-a.local",
            "X-authentik-name": "Tech One",
        },
    ) as tech_client:
        # Tech sees the in-app notification in POST /notifications/search and GET /notifications
        tech_search = tech_client.post(
            "/api/notifications/search",
            json={"pageNum": 0, "pageSize": 20},
        )
        assert tech_search.status_code == 200
        tech_notifs = tech_search.json()["content"]
        matching = [
            n
            for n in tech_notifs
            if n["resourceId"] == wo["id"] and n["notificationType"] == "WORK_ORDER"
        ]
        assert len(matching) == 1
        notif_id = matching[0]["id"]
        assert matching[0]["seen"] is False

        # Admin does NOT see Tech's notification in Admin's search or list, and cannot PATCH it (403)
        admin_search = admin_client.post(
            "/api/notifications/search",
            json={"pageNum": 0, "pageSize": 50},
        ).json()["content"]
        assert all(n["id"] != notif_id for n in admin_search)
        assert admin_client.patch(f"/api/notifications/{notif_id}", json={"seen": True}).status_code == 403

        # Tech can mark their own notification as seen
        mark_res = tech_client.patch(f"/api/notifications/{notif_id}", json={"seen": True})
        assert mark_res.status_code == 200
        assert mark_res.json()["seen"] is True

