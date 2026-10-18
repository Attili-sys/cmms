"""Tests verifying the Spring REST controller endpoint catalog."""

from pathlib import Path
import yaml

ENDPOINTS_YAML = Path(__file__).resolve().parents[1] / "fixtures" / "contract" / "endpoints.yaml"


def test_endpoints_yaml_exists_and_is_complete() -> None:
    assert ENDPOINTS_YAML.exists(), "fixtures/contract/endpoints.yaml must exist"
    data = yaml.safe_load(ENDPOINTS_YAML.read_text(encoding="utf-8"))
    assert data["total_controllers"] >= 55
    assert data["total_endpoints"] >= 250
    endpoints = data["endpoints"]
    paths = {(e["method"], e["path"]) for e in endpoints}
    assert ("POST", "/work-orders/search") in paths
    assert ("POST", "/auth/signin") in paths
    assert ("GET", "/auth/me") in paths
    assert ("POST", "/assets/search") in paths
    assert ("POST", "/parts/search") in paths
    assert ("POST", "/requests/search") in paths
