"""End-to-end CRUD and DTO contract verification tests matching React frontend slices."""

from __future__ import annotations

from collections.abc import Iterator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import app
from src.deps.db import get_db
from src.models import Base


def test_full_frontend_crud_contracts() -> None:
    """Verify Location, Asset, WorkOrder, PM, Checklist, and Meter DTO contracts."""
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
                "X-authentik-email": "admin@canvas.local",
                "X-authentik-name": "Canvas Admin",
            },
        ) as client:
            # 1. Authenticate / get current user
            me_resp = client.get("/api/auth/me")
            assert me_resp.status_code == 200
            me = me_resp.json()
            assert me["companyId"] is not None

            # 2. Location CRUD + /children/0/paginated hierarchy contract
            loc_resp = client.post(
                "/api/locations",
                json={"name": "Smoke Test Location", "address": "100 Main St"},
            )
            assert loc_resp.status_code == 200
            loc = loc_resp.json()
            assert loc["name"] == "Smoke Test Location"
            assert isinstance(loc["workers"], list)
            assert isinstance(loc["teams"], list)
            assert isinstance(loc["vendors"], list)
            assert isinstance(loc["customers"], list)

            loc_page_resp = client.get(
                "/api/locations/children/0/paginated",
                params={"pageNum": 0, "pageSize": 10, "sortField": "createdAt", "direction": "DESC"},
            )
            assert loc_page_resp.status_code == 200
            loc_page = loc_page_resp.json()
            assert loc_page["totalElements"] >= 1
            assert any(item["id"] == loc["id"] for item in loc_page["content"])

            # 3. Asset CRUD + /children/0/paginated + /mini?locationId= + FK hydration
            asset_resp = client.post(
                "/api/assets",
                json={"name": "Smoke Test Asset", "location": {"id": loc["id"]}},
            )
            assert asset_resp.status_code == 200
            asset = asset_resp.json()
            assert asset["name"] == "Smoke Test Asset"
            assert asset["location"]["id"] == loc["id"]
            assert asset["location"]["name"] == "Smoke Test Location"
            assert asset["status"] == "OPERATIONAL"

            asset_page_resp = client.get(
                "/api/assets/children/0/paginated",
                params={"pageNum": 0, "pageSize": 10, "sortField": "createdAt", "direction": "DESC"},
            )
            assert asset_page_resp.status_code == 200
            asset_page = asset_page_resp.json()
            assert asset_page["totalElements"] >= 1
            assert any(item["id"] == asset["id"] for item in asset_page["content"])

            mini_empty_resp = client.get("/api/assets/mini?locationId=")
            assert mini_empty_resp.status_code == 200
            assert any(item["id"] == asset["id"] for item in mini_empty_resp.json())

            # 4. WorkOrder CRUD + FK hydration
            wo_resp = client.post(
                "/api/work-orders",
                json={
                    "title": "Smoke Test Work Order",
                    "location": {"id": loc["id"]},
                    "asset": {"id": asset["id"]},
                },
            )
            assert wo_resp.status_code == 200
            wo = wo_resp.json()
            assert wo["title"] == "Smoke Test Work Order"
            assert wo["customId"].startswith("WO")
            assert wo["location"]["name"] == "Smoke Test Location"
            assert wo["asset"]["name"] == "Smoke Test Asset"

            # 5. PreventiveMaintenance CRUD + Schedule hydration + search sorting
            pm_resp = client.post(
                "/api/preventive-maintenances",
                json={
                    "name": "Smoke Test PM",
                    "title": "PM WO Title",
                    "location": {"id": loc["id"]},
                    "asset": {"id": asset["id"]},
                    "schedule": {"frequency": 14, "recurrenceType": "DAILY"},
                },
            )
            assert pm_resp.status_code == 200
            pm = pm_resp.json()
            assert pm["schedule"] is not None
            assert pm["schedule"]["frequency"] == 14
            assert isinstance(pm["schedule"]["daysOfWeek"], list)
            assert pm["location"]["name"] == "Smoke Test Location"
            assert pm["asset"]["name"] == "Smoke Test Asset"

            pm_search_resp = client.post(
                "/api/preventive-maintenances/search",
                json={"pageNum": 0, "pageSize": 10, "sortField": "schedule.startsOn", "direction": "DESC"},
            )
            assert pm_search_resp.status_code == 200
            assert pm_search_resp.json()["totalElements"] >= 1

            # 6. Checklist CRUD with taskBases and options
            cl_resp = client.post(
                "/api/checklists",
                json={
                    "name": "Smoke Test Checklist",
                    "description": "Verify checklist tasks",
                    "taskBases": [
                        {
                            "label": "Inspect pressure gauge",
                            "taskType": "MULTIPLE",
                            "options": ["Pass", "Fail"],
                        }
                    ],
                },
            )
            assert cl_resp.status_code == 200
            cl = cl_resp.json()
            assert cl["name"] == "Smoke Test Checklist"
            assert len(cl["taskBases"]) == 1
            assert cl["taskBases"][0]["label"] == "Inspect pressure gauge"
            assert [o["label"] for o in cl["taskBases"][0]["options"]] == ["Pass", "Fail"]

            # 7. Meter CRUD + FK hydration
            meter_resp = client.post(
                "/api/meters",
                json={
                    "name": "Smoke Test Meter",
                    "unit": "psi",
                    "updateFrequency": 5,
                    "location": {"id": loc["id"]},
                    "asset": {"id": asset["id"]},
                },
            )
            assert meter_resp.status_code == 200
            meter = meter_resp.json()
            assert meter["name"] == "Smoke Test Meter"
            assert meter["location"]["name"] == "Smoke Test Location"
            assert meter["asset"]["name"] == "Smoke Test Asset"
    finally:
        app.dependency_overrides.pop(get_db, None)
