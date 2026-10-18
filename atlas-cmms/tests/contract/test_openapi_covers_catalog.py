"""Phase 10 contract verification: OpenAPI route coverage against endpoints.yaml catalog."""

from __future__ import annotations

from pathlib import Path
import yaml

from src.app import app

CATALOG_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "contract" / "endpoints.yaml"


def test_openapi_schema_generates_cleanly() -> None:
    schema = app.openapi()
    assert schema["info"]["title"]
    paths = schema.get("paths", {})
    assert len(paths) >= 100


def test_openapi_covers_core_domain_route_groups() -> None:
    assert CATALOG_PATH.exists()
    catalog = yaml.safe_load(CATALOG_PATH.read_text())
    assert len(catalog["endpoints"]) >= 350

    openapi_paths = set(app.openapi().get("paths", {}).keys())
    required_prefixes = [
        "/api/auth/signin",
        "/api/auth/me",
        "/api/license/validity",
        "/api/subscription-plans",
        "/api/users",
        "/api/roles",
        "/api/teams",
        "/api/locations",
        "/api/assets",
        "/api/asset-downtimes",
        "/api/parts",
        "/api/multi-parts",
        "/api/purchase-orders",
        "/api/vendors",
        "/api/customers",
        "/api/tasks",
        "/api/checklists",
        "/api/work-orders",
        "/api/labors",
        "/api/preventive-maintenances",
        "/api/schedules",
        "/api/meters",
        "/api/readings",
        "/api/requests",
        "/api/workflows",
        "/api/files",
        "/api/custom-fields",
        "/api/notifications",
        "/api/analytics/work-orders/complete/overview",
        "/api/export/{entity_name}",
        "/api/import/{entity_name}",
        "/api/api-keys",
        "/api/webhooks",
    ]
    for prefix in required_prefixes:
        assert prefix in openapi_paths, f"Missing required route in OpenAPI schema: {prefix}"
