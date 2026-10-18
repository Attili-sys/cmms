"""Phase 1 schema parity gate: asserts SQLAlchemy Base.metadata matches Liquibase schema_dump.json."""

import json
from pathlib import Path

from src.models import Base, SubscriptionPlan
from src.models.enums import PlanFeatures


def test_schema_matches_liquibase_dump() -> None:
    dump_path = Path(__file__).resolve().parents[1] / "fixtures" / "schema_dump.json"
    dump = json.loads(dump_path.read_text())

    expected_tables = dump["tables"]
    actual_tables = Base.metadata.tables

    assert set(actual_tables.keys()) == set(expected_tables.keys())

    for tname, tinfo in expected_tables.items():
        sa_table = actual_tables[tname]
        sa_cols = {c.name.lower(): c for c in sa_table.columns}
        exp_cols = tinfo["columns"]
        assert set(sa_cols.keys()) == set(exp_cols.keys()), f"Column mismatch in {tname}"
        for cname, cinfo in exp_cols.items():
            if not cinfo.get("pk") and cname not in ("id", "rev"):
                assert sa_cols[cname].nullable == cinfo["nullable"], f"Nullability mismatch on {tname}.{cname}"


def test_subscription_plan_returns_all_features() -> None:
    plan = SubscriptionPlan(code="FREE", name="Free")
    assert plan.features == set(PlanFeatures)
    assert len(plan.features) == len(list(PlanFeatures))
