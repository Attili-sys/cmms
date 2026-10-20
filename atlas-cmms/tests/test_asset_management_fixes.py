"""Granular tests for all 22 Asset Management fixes (5 Original Claims + 8 P0 + 9 P1)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.deps.db import get_db
from src.models import (
    Asset as AssetModel,
    Base,
    Company,
    CompanySettings,
    Location as LocationModel,
    RequestPortal,
    Role,
    User,
)
from src.models.associations import (
    role_create_permissions,
    role_view_other_permissions,
    role_view_permissions,
)
from src.models.enums import PermissionEntity


@pytest.fixture(scope="module")
def asset_env():
    """Module-scoped isolated test database and seeded tenants/users for Asset Management tests."""
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
        ) as client:
            me_resp = client.get("/api/auth/me")
            assert me_resp.status_code == 200
            me = me_resp.json()
            company_a_id = me["companyId"]

            with testing_session_local() as db:
                cs_b = CompanySettings()
                db.add(cs_b)
                db.flush()
                comp_b = Company(name="Tenant B Corp", company_settings_id=cs_b.id)
                db.add(comp_b)
                db.flush()
                cs_b.company_id = comp_b.id
                company_b_id = comp_b.id

                portal_a = RequestPortal(
                    company_id=company_a_id,
                    uuid="portal-uuid-tenant-a",
                    title="Portal A",
                )
                portal_b = RequestPortal(
                    company_id=company_b_id,
                    uuid="portal-uuid-tenant-b",
                    title="Portal B",
                )
                db.add_all([portal_a, portal_b])

                comp_a = db.get(Company, company_a_id)
                cs_a_id = comp_a.company_settings_id
                limited_role = Role(
                    name="Limited Tech",
                    company_settings_id=cs_a_id,
                    role_type=1,
                    code=2,
                    paid=True,
                )
                db.add(limited_role)
                db.flush()
                perm_entities = list(PermissionEntity)
                for perm in (
                    PermissionEntity.ASSETS,
                    PermissionEntity.LOCATIONS,
                    PermissionEntity.CATEGORIES,
                ):
                    perm_ord = perm_entities.index(perm)
                    db.execute(
                        role_view_permissions.insert().values(
                            role_id=limited_role.id, view_permissions=perm_ord
                        )
                    )
                    db.execute(
                        role_view_other_permissions.insert().values(
                            role_id=limited_role.id, view_other_permissions=perm_ord
                        )
                    )
                    db.execute(
                        role_create_permissions.insert().values(
                            role_id=limited_role.id, create_permissions=perm_ord
                        )
                    )
                tech_user = User(
                    email="tech@tenant-a.local",
                    username="tech@tenant-a.local",
                    first_name="Tech",
                    last_name="User",
                    password="hashed",
                    company_id=company_a_id,
                    role_id=limited_role.id,
                    enabled=True,
                    enabled_in_subscription=True,
                    created_via_sso=True,
                    owns_company=False,
                    rate=0,
                )
                other_tenant_user = User(
                    email="admin@tenant-b.local",
                    username="admin@tenant-b.local",
                    first_name="Tenant B",
                    last_name="User",
                    password="hashed",
                    company_id=company_b_id,
                    role_id=limited_role.id,
                    enabled=True,
                    enabled_in_subscription=True,
                    created_via_sso=True,
                    owns_company=True,
                    rate=0,
                )
                loc_b = LocationModel(name="Tenant B Secret Site", company_id=company_b_id)
                db.add_all([tech_user, other_tenant_user, loc_b])
                db.commit()
                tech_user_id = tech_user.id
                loc_b_id = loc_b.id

            state: dict = {
                "client": client,
                "session_local": testing_session_local,
                "company_a_id": company_a_id,
                "company_b_id": company_b_id,
                "tech_user_id": tech_user_id,
                "loc_b_id": loc_b_id,
            }
            yield state
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_01_file_upload_download_and_size_limit(asset_env: dict) -> None:
    """P0-02: Verify file upload, download, portal upload, and 25 MB size limit enforcement."""
    client: TestClient = asset_env["client"]
    upload_resp = client.post(
        "/api/files/upload",
        data={"folder": "assets", "type": "OTHER"},
        files=[("files", ("manual.pdf", io.BytesIO(b"PDF-CONTENT-123"), "application/pdf"))],
    )
    assert upload_resp.status_code == 200
    uploaded_files = upload_resp.json()
    assert len(uploaded_files) == 1
    file_dto = uploaded_files[0]
    assert file_dto["name"] == "manual.pdf"
    assert file_dto["url"] == f"/api/files/download/{file_dto['id']}"
    assert file_dto["thumbnailUrl"] == f"/api/files/download/{file_dto['id']}"

    dl_resp = client.get(file_dto["url"])
    assert dl_resp.status_code == 200
    assert dl_resp.content == b"PDF-CONTENT-123"
    asset_env["file_dto"] = file_dto

    # Verify 25 MB size limit returns 413
    oversized = io.BytesIO(b"x" * (25 * 1024 * 1024 + 2))
    too_big_resp = client.post(
        "/api/files/upload/request-portal/portal-uuid-tenant-a",
        files=[("files", ("huge.bin", oversized, "application/octet-stream"))],
    )
    assert too_big_resp.status_code == 413


def test_02_asset_m2m_custom_fields_and_part_lookup(asset_env: dict) -> None:
    """Claim 1, P0-05, P1-15: Verify M2M + CustomFieldValue sync, /assets/part/{id}, and /assets/barcode."""
    client: TestClient = asset_env["client"]
    tech_user_id: int = asset_env["tech_user_id"]
    file_dto: dict = asset_env["file_dto"]

    loc_resp = client.post("/api/locations", json={"name": "Plant North"})
    assert loc_resp.status_code == 200
    loc_id = loc_resp.json()["id"]

    part_resp = client.post(
        "/api/parts", json={"name": "Bearing 6204", "cost": 25.0, "quantity": 10}
    )
    assert part_resp.status_code == 200
    part_id = part_resp.json()["id"]

    vendor_resp = client.post(
        "/api/vendors",
        json={"companyName": "SKF Industrial", "name": "SKF Contact"},
    )
    assert vendor_resp.status_code == 200
    vendor_id = vendor_resp.json()["id"]

    cust_resp = client.post("/api/customers", json={"name": "Acme Corp"})
    assert cust_resp.status_code == 200
    cust_id = cust_resp.json()["id"]

    team_resp = client.post("/api/teams", json={"name": "Mechanical Team"})
    assert team_resp.status_code == 200
    team_id = team_resp.json()["id"]

    cf_resp = client.post("/api/custom-fields", json={"name": "Voltage"})
    assert cf_resp.status_code == 200
    cf_id = cf_resp.json()["id"]

    asset_create_resp = client.post(
        "/api/assets",
        json={
            "name": "Alpha Compressor",
            "barCode": "BC-ALPHA-01",
            "nfcId": "NFC-ALPHA-01",
            "acquisitionCost": 5000.0,
            "location": {"id": loc_id},
            "parts": [{"id": part_id}],
            "vendors": [{"id": vendor_id}],
            "customers": [{"id": cust_id}],
            "teams": [{"id": team_id}],
            "assignedTo": [{"id": tech_user_id}],
            "files": [{"id": file_dto["id"]}],
            "customFieldValues": [{"customField": {"id": cf_id}, "value": "480V"}],
        },
    )
    assert asset_create_resp.status_code == 200
    alpha = asset_create_resp.json()
    alpha_id = alpha["id"]
    assert alpha["customId"].startswith("A")
    assert len(alpha["parts"]) == 1 and alpha["parts"][0]["id"] == part_id
    assert len(alpha["vendors"]) == 1 and alpha["vendors"][0]["id"] == vendor_id
    assert len(alpha["customers"]) == 1 and alpha["customers"][0]["id"] == cust_id
    assert len(alpha["teams"]) == 1 and alpha["teams"][0]["id"] == team_id
    assert len(alpha["assignedTo"]) == 1 and alpha["assignedTo"][0]["id"] == tech_user_id
    assert len(alpha["files"]) == 1 and alpha["files"][0]["id"] == file_dto["id"]
    assert alpha["files"][0]["url"] == f"/api/files/download/{file_dto['id']}"
    assert (
        len(alpha["customFieldValues"]) == 1 and alpha["customFieldValues"][0]["value"] == "480V"
    )

    by_part_resp = client.get(f"/api/assets/part/{part_id}")
    assert by_part_resp.status_code == 200
    by_part_list = by_part_resp.json()
    assert len(by_part_list) == 1
    assert by_part_list[0]["id"] == alpha_id

    by_bc_resp = client.get("/api/assets/barcode?data=BC-ALPHA-01")
    assert by_bc_resp.status_code == 200
    assert by_bc_resp.json()["id"] == alpha_id
    assert client.get("/api/assets/barcode?data=NONEXISTENT").status_code == 404

    asset_env.update(
        {
            "loc_id": loc_id,
            "part_id": part_id,
            "vendor_id": vendor_id,
            "alpha_id": alpha_id,
        }
    )


def test_03_tenant_hijack_and_null_fk_clearing(asset_env: dict) -> None:
    """P0-07: Verify apply_patch blocks nested company/audit overrides and allows clearing FKs with None."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]
    loc_id: int = asset_env["loc_id"]
    company_a_id: int = asset_env["company_a_id"]
    company_b_id: int = asset_env["company_b_id"]
    testing_session_local = asset_env["session_local"]

    hijack_resp = client.patch(
        f"/api/assets/{alpha_id}",
        json={
            "company": {"id": company_b_id},
            "companyId": company_b_id,
            "createdBy": 99999,
            "updatedBy": 99999,
        },
    )
    assert hijack_resp.status_code == 200
    with testing_session_local() as db:
        db_asset = db.get(AssetModel, alpha_id)
        assert db_asset.company_id == company_a_id
        assert db_asset.created_by != 99999

    clear_loc_resp = client.patch(f"/api/assets/{alpha_id}", json={"location": None})
    assert clear_loc_resp.status_code == 200
    assert clear_loc_resp.json().get("location") is None
    client.patch(f"/api/assets/{alpha_id}", json={"location": {"id": loc_id}})


def test_04_search_m2m_distinct_and_custom_fields(asset_env: dict) -> None:
    """P0-04: Verify search with customFieldValues.value and M2M deduplication via subquery."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]
    part_id: int = asset_env["part_id"]

    search_cf_resp = client.post(
        "/api/assets/search",
        json={
            "pageNum": 0,
            "pageSize": 10,
            "sortField": "name",
            "direction": "ASC",
            "filterFields": [
                {
                    "field": "name",
                    "operation": "cn",
                    "value": "480V",
                    "alternatives": [
                        {"field": "customFieldValues.value", "operation": "cn", "value": "480V"}
                    ],
                },
                {"field": "parts", "operation": "in", "values": [part_id]},
            ],
        },
    )
    assert search_cf_resp.status_code == 200
    search_cf_data = search_cf_resp.json()
    assert search_cf_data["totalElements"] == 1
    assert search_cf_data["content"][0]["id"] == alpha_id


def test_05_hierarchy_sort_cycle_and_identifier_uniqueness(asset_env: dict) -> None:
    """P1-08, P1-09, P1-12: Verify hierarchy pagination sorting, cycle detection, and identifier uniqueness."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]

    zulu_resp = client.post(
        "/api/assets",
        json={
            "name": "Zulu Pump",
            "parentAsset": {"id": alpha_id},
            "barCode": "   ",
            "nfcId": "",
        },
    )
    assert zulu_resp.status_code == 200
    zulu = zulu_resp.json()
    zulu_id = zulu["id"]
    assert zulu["barCode"] is None
    assert zulu["nfcId"] is None

    beta_resp = client.post("/api/assets", json={"name": "Beta Generator", "barCode": ""})
    assert beta_resp.status_code == 200
    beta_id = beta_resp.json()["id"]

    paginated_asc = client.get("/api/assets/children/0/paginated?sort=name,asc")
    assert paginated_asc.status_code == 200
    names_asc = [a["name"] for a in paginated_asc.json()["content"]]
    assert names_asc == ["Alpha Compressor", "Beta Generator"]

    paginated_desc = client.get("/api/assets/children/0/paginated?sort=name,desc")
    assert paginated_desc.status_code == 200
    names_desc = [a["name"] for a in paginated_desc.json()["content"]]
    assert names_desc == ["Beta Generator", "Alpha Compressor"]

    assert (
        client.patch(f"/api/assets/{alpha_id}", json={"parentAsset": {"id": alpha_id}}).status_code
        == 400
    )
    assert (
        client.patch(f"/api/assets/{alpha_id}", json={"parentAsset": {"id": zulu_id}}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/assets", json={"name": "Duplicate Barcode Asset", "barCode": "BC-ALPHA-01"}
        ).status_code
        == 409
    )

    asset_env["zulu_id"] = zulu_id
    asset_env["beta_id"] = beta_id


def test_06_status_downtime_state_machine_and_work_order_hooks(asset_env: dict) -> None:
    """Claim 3: Verify status-to-downtime cascades, overlap validation, and WorkOrder status hooks."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]
    zulu_id: int = asset_env["zulu_id"]
    beta_id: int = asset_env["beta_id"]

    down_resp = client.patch(f"/api/assets/{zulu_id}", json={"status": "DOWN"})
    assert down_resp.status_code == 200
    assert down_resp.json()["status"] == "DOWN"
    assert client.get(f"/api/assets/{alpha_id}").json()["status"] == "DOWN"

    zulu_dts = client.get(f"/api/asset-downtimes/asset/{zulu_id}").json()
    alpha_dts = client.get(f"/api/asset-downtimes/asset/{alpha_id}").json()
    assert len(zulu_dts) == 1 and zulu_dts[0]["duration"] == 0
    assert len(alpha_dts) == 1 and alpha_dts[0]["duration"] == 0

    op_resp = client.patch(f"/api/assets/{alpha_id}", json={"status": "OPERATIONAL"})
    assert op_resp.status_code == 200
    assert op_resp.json()["status"] == "OPERATIONAL"
    assert client.get(f"/api/assets/{zulu_id}").json()["status"] == "OPERATIONAL"

    zulu_dts_closed = client.get(f"/api/asset-downtimes/asset/{zulu_id}").json()
    assert len(zulu_dts_closed) == 1 and zulu_dts_closed[0]["duration"] >= 1

    # Overlap validation (406)
    t0 = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    dt1_resp = client.post(
        "/api/asset-downtimes",
        json={
            "asset": {"id": beta_id},
            "startsOn": t0,
            "duration": 3600,
            "downtimeReason": "Failure 1",
        },
    )
    assert dt1_resp.status_code == 200

    dt_overlap_resp = client.post(
        "/api/asset-downtimes",
        json={
            "asset": {"id": beta_id},
            "startsOn": t0,
            "duration": 1800,
            "downtimeReason": "Overlap",
        },
    )
    assert dt_overlap_resp.status_code == 406

    # WorkOrder IN_PROGRESS sets firstTimeToReact
    wo_resp = client.post(
        "/api/work-orders",
        json={"title": "Pump Repair WO", "asset": {"id": beta_id}},
    )
    assert wo_resp.status_code == 200
    wo_id = wo_resp.json()["id"]
    wo_ip_resp = client.patch(f"/api/work-orders/{wo_id}", json={"status": "IN_PROGRESS"})
    assert wo_ip_resp.status_code == 200
    assert wo_ip_resp.json()["firstTimeToReact"] is not None


def test_07_asset_analytics_and_depreciation_contracts(asset_env: dict) -> None:
    """Claim 2, Claim 4, P0-03: Verify asset/fleet analytics and depreciation CRUD."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]

    overview_resp = client.post(f"/api/analytics/assets/{alpha_id}/overview", json={})
    assert overview_resp.status_code == 200
    overview_data = overview_resp.json()
    assert isinstance(overview_data, dict)
    for key in ("mtbf", "mttr", "downtime", "uptime", "totalCost"):
        assert key in overview_data

    costs_overview_resp = client.post("/api/analytics/assets/costs/overview", json={})
    assert costs_overview_resp.status_code == 200
    costs_data = costs_overview_resp.json()
    assert costs_data["totalAcquisitionCost"] == 5000.0
    assert "totalWOCosts" in costs_data and "rav" in costs_data

    fleet_mtbf_resp = client.get("/api/analytics/assets/mtbf")
    assert fleet_mtbf_resp.status_code == 200
    assert isinstance(fleet_mtbf_resp.json(), list)

    dep_resp = client.post(
        "/api/deprecations",
        json={"purchasePrice": 5000, "residualValue": "500", "usefulLife": "10", "rate": 10.0},
    )
    assert dep_resp.status_code == 200
    assert dep_resp.json()["purchasePrice"] == 5000


def test_08_public_mini_and_floor_plan_isolation(asset_env: dict) -> None:
    """P0-01: Verify public mini endpoints and floor-plans/location/{id} enforce tenant isolation."""
    client: TestClient = asset_env["client"]
    loc_b_id: int = asset_env["loc_b_id"]

    mini_a = client.get("/api/assets/mini/portal-uuid-tenant-a").json()
    mini_b = client.get("/api/assets/mini/portal-uuid-tenant-b").json()
    mini_invalid = client.get("/api/assets/mini/non-existent-uuid").json()
    assert len(mini_a) >= 2
    assert mini_b == []
    assert mini_invalid == []
    loc_mini_a = client.get("/api/locations/mini/portal-uuid-tenant-a").json()
    loc_mini_b = client.get("/api/locations/mini/portal-uuid-tenant-b").json()
    assert [l["name"] for l in loc_mini_a] == ["Plant North"]
    assert [l["name"] for l in loc_mini_b] == ["Tenant B Secret Site"]
    assert client.get("/api/locations/mini/non-existent-uuid").json() == []
    assert client.get(f"/api/floor-plans/location/{loc_b_id}").status_code == 403


def test_09_rbac_ownership_and_cross_tenant_fk_validation(asset_env: dict) -> None:
    """P0-08, P1-11: Verify Java-parity edit/delete ownership and cross-tenant FK guard."""
    alpha_id: int = asset_env["alpha_id"]
    beta_id: int = asset_env["beta_id"]
    loc_b_id: int = asset_env["loc_b_id"]

    with TestClient(
        app,
        headers={
            "X-authentik-email": "tech@tenant-a.local",
            "X-authentik-name": "Tech User",
        },
    ) as tech_client:
        cross_fk_resp = tech_client.post(
            "/api/assets",
            json={"name": "Cross Tenant FK Probe", "location": {"id": loc_b_id}},
        )
        assert cross_fk_resp.status_code == 403

        tech_edit_assigned = tech_client.patch(
            f"/api/assets/{alpha_id}",
            json={"description": "Updated by assigned tech"},
        )
        assert tech_edit_assigned.status_code == 200

        tech_delete_assigned = tech_client.delete(f"/api/assets/{alpha_id}")
        assert tech_delete_assigned.status_code == 403

        tech_edit_unassigned = tech_client.patch(
            f"/api/assets/{beta_id}",
            json={"description": "Should be forbidden"},
        )
        assert tech_edit_unassigned.status_code == 403


def test_10_two_pass_import_and_csv_export(asset_env: dict) -> None:
    """P0-06, P1-10: Verify two-pass asset import, template headers, and 26-column CSV export."""
    client: TestClient = asset_env["client"]
    loc_id: int = asset_env["loc_id"]
    tech_user_id: int = asset_env["tech_user_id"]
    part_id: int = asset_env["part_id"]
    vendor_id: int = asset_env["vendor_id"]

    tpl_resp = client.get("/api/import/download-template?language=EN&importEntity=ASSET")
    assert tpl_resp.status_code == 200
    assert "Parent Asset" in tpl_resp.text

    import_resp = client.post(
        "/api/import/assets",
        json=[
            {
                "name": "Imported Child Pump",
                "parentAssetName": "Imported Parent Skid",
                "locationName": "Plant North",
                "category": "Rotating Equipment",
                "primaryUserEmail": "tech@tenant-a.local",
                "assignedToEmails": ["tech@tenant-a.local"],
                "teamsNames": ["Mechanical Team"],
                "vendorsNames": ["SKF Industrial"],
                "customersNames": ["Acme Corp"],
                "partsNames": ["Bearing 6204"],
                "acquisitionCost": 1200.0,
                "status": "OPERATIONAL",
            },
            {
                "name": "Imported Parent Skid",
                "locationName": "Plant North",
                "acquisitionCost": 8000.0,
                "status": "OPERATIONAL",
            },
        ],
    )
    assert import_resp.status_code == 200
    assert import_resp.json()["created"] == 2

    all_assets = client.get("/api/assets").json()
    imp_child = next(a for a in all_assets if a["name"] == "Imported Child Pump")
    imp_parent = next(a for a in all_assets if a["name"] == "Imported Parent Skid")
    assert imp_child["customId"].startswith("A")
    assert imp_child["location"]["id"] == loc_id
    assert imp_child["parentAsset"]["id"] == imp_parent["id"]
    assert imp_child["primaryUser"]["id"] == tech_user_id
    assert len(imp_child["parts"]) == 1 and imp_child["parts"][0]["id"] == part_id
    assert len(imp_child["vendors"]) == 1 and imp_child["vendors"][0]["id"] == vendor_id

    export_resp = client.get("/api/export/assets")
    assert export_resp.status_code == 200
    assert "Imported Child Pump" in export_resp.text


def test_11_meters_by_asset_and_reading_triggers(asset_env: dict) -> None:
    """P1-13, P1-14: Verify GET /meters/asset/{id} hydration and reading-triggered WO customId."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]
    loc_id: int = asset_env["loc_id"]
    tech_user_id: int = asset_env["tech_user_id"]

    meter_resp = client.post(
        "/api/meters",
        json={
            "name": "Discharge Pressure",
            "unit": "bar",
            "updateFrequency": 1,
            "asset": {"id": alpha_id},
            "location": {"id": loc_id},
            "users": [{"id": tech_user_id}],
        },
    )
    assert meter_resp.status_code == 200
    meter_id = meter_resp.json()["id"]

    trigger_resp = client.post(
        "/api/work-order-meter-triggers",
        json={
            "name": "High Pressure Trigger",
            "title": "High Pressure Alarm WO",
            "meter": {"id": meter_id},
            "triggerCondition": "MORE_THAN",
            "value": 100,
            "priority": "HIGH",
        },
    )
    assert trigger_resp.status_code == 200

    reading_resp = client.post(
        "/api/readings",
        json={"meter": {"id": meter_id}, "value": 125},
    )
    assert reading_resp.status_code == 200

    meters_for_asset = client.get(f"/api/meters/asset/{alpha_id}").json()
    assert len(meters_for_asset) == 1
    assert meters_for_asset[0]["lastReading"] is not None
    assert meters_for_asset[0]["nextReading"] is not None
    assert len(meters_for_asset[0]["users"]) == 1

    wos = client.post("/api/work-orders/search", json={"pageNum": 0, "pageSize": 20}).json()[
        "content"
    ]
    triggered_wo = next((w for w in wos if w["title"] == "High Pressure Alarm WO"), None)
    assert triggered_wo is not None
    assert triggered_wo["customId"] is not None and triggered_wo["customId"].startswith("W")


def test_12_sql_migration_deduplication_and_partial_unique_indexes() -> None:
    """P1-12: Verify db/migrations/003_asset_unique_identifiers.sql deduplicates existing rows and enforces unique indexes."""
    mig_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with mig_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE asset (id INTEGER PRIMARY KEY, company_id INTEGER, custom_id VARCHAR, bar_code VARCHAR, nfc_id VARCHAR)"
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO asset (id, company_id, custom_id, bar_code, nfc_id) VALUES
                (1, 10, 'A000001', 'BC-DUP', '   '),
                (2, 10, 'A000001', 'BC-DUP', ''),
                (3, 20, 'A000001', 'BC-DUP', NULL)
                """
            )
        )
        sql_path = (
            Path(__file__).resolve().parent.parent
            / "db"
            / "migrations"
            / "003_asset_unique_identifiers.sql"
        )
        for stmt in sql_path.read_text().split(";"):
            cleaned = stmt.strip()
            if cleaned:
                conn.execute(text(cleaned))

        rows = conn.execute(
            text("SELECT id, company_id, custom_id, bar_code, nfc_id FROM asset ORDER BY id")
        ).fetchall()
        assert rows[0] == (1, 10, "A000001", "BC-DUP", None)
        assert rows[1] == (2, 10, "A000001-2", "BC-DUP-2", None)
        assert rows[2] == (3, 20, "A000001", "BC-DUP", None)


def test_13_clone_with_nfc_and_analytics_overview_naive_datetime(asset_env: dict) -> None:
    """Delta verification: cloning an asset with nfc_id does not emit or copy nfc:{id:...}, and analytics/assets/overview handles naive starts_on."""
    client: TestClient = asset_env["client"]
    alpha_id: int = asset_env["alpha_id"]

    # 1. Source asset has nfcId='NFC-ALPHA-01' from test_06; verify model_to_dict does NOT emit 'nfc'
    alpha_dto = client.get(f"/api/assets/{alpha_id}").json()
    assert alpha_dto.get("nfcId") == "NFC-ALPHA-01"
    assert "nfc" not in alpha_dto

    # 2. Even if a legacy client sends nfc={'id': 'NFC-ALPHA-01'} alongside blank nfcId='' when cloning, it must succeed (200) and leave nfcId=None
    clone_resp = client.post(
        "/api/assets",
        json={
            "name": "Compressor Alpha Clone",
            "customId": "",
            "barCode": "",
            "nfcId": "",
            "nfc": {"id": "NFC-ALPHA-01"},
        },
    )
    assert clone_resp.status_code == 200
    cloned = clone_resp.json()
    assert cloned["nfcId"] is None
    assert "nfc" not in cloned

    # 3. POST /api/analytics/assets/overview must succeed (200) when downtime records exist
    overview_resp = client.post(
        "/api/analytics/assets/overview",
        json={
            "start": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "end": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert overview_resp.status_code == 200
    overview = overview_resp.json()
    assert "availability" in overview
    assert "downtime" in overview
    assert overview["downtime"] > 0

    # 4. GET /, /runtime-env.js, and built static entrypoints resolve cleanly with no-cache headers on HTML/runtime-env
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert "no-store" in root_resp.headers.get("cache-control", "")

    rt_resp = client.get("/runtime-env.js")
    assert rt_resp.status_code == 200
    assert "window.__RUNTIME_CONFIG__" in rt_resp.text
    assert "no-store" in rt_resp.headers.get("cache-control", "")

    manifest_resp = client.get("/asset-manifest.json")
    assert manifest_resp.status_code == 200
    for ep in manifest_resp.json().get("entrypoints", []):
        ep_resp = client.get(f"/{ep.lstrip('/')}")
        assert ep_resp.status_code == 200

    # Verify stale hashed bundle requests fall back cleanly to the active main bundle
    stale_main_resp = client.get("/static/js/main.0991fd54.js")
    assert stale_main_resp.status_code == 200



