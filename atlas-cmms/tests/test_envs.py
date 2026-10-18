"""Secrets, as the platform injects them (src/envs.py): read when asked, so the app imports without
them — its tests, and a pair's `canvas validate` and `canvas api pull`, which import it (#110)."""

import pytest

from src import envs


def test_a_secret_the_user_has_set_is_read_one_not_set_says_how_to_set_it(monkeypatch):
    monkeypatch.setenv("PARTNER_API_KEY", "k3y")
    assert envs.secret("PARTNER_API_KEY") == "k3y"
    monkeypatch.delenv("OTHER_KEY", raising=False)
    with pytest.raises(RuntimeError, match="canvas secret set OTHER_KEY"):
        envs.secret("OTHER_KEY")


def test_a_secret_file_is_read_from_where_the_platform_mounted_it(monkeypatch, tmp_path):
    (tmp_path / "AZURE").write_text('{"tenant": "t"}')
    monkeypatch.setenv("AZURE_FILE", str(tmp_path / "AZURE"))
    assert envs.secret_file("AZURE") == '{"tenant": "t"}'
