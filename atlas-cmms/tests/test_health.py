"""The readiness contract: the app answers where score.yaml's route probes it — the platform's test,
replaced with it by `canvas app update`."""

from pathlib import Path

import yaml  # with uvicorn[standard], which every app has
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def probe_path() -> str:
    """The route's own `path` in score.yaml, "/" when it sets none — read as YAML, so a variable or
    anything else named `path` is never taken for it."""
    score = yaml.safe_load((Path(__file__).resolve().parents[1] / "score.yaml").read_text())
    route = next(r for r in score["resources"].values() if r.get("type") == "route")
    return (route.get("params") or {}).get("path", "/")


def test_healthz_matches_score_yaml():
    """If this fails, score.yaml and views.py disagree — that is `probe.path`."""
    path = probe_path()
    assert client.get(path).status_code == 200, f"score.yaml probes {path}, which the app does not serve"
