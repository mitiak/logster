from __future__ import annotations

from pathlib import Path

import pytest

from logster import manage
from logster.config import COLOR_SCHEME_PRESETS


def test_manage_info_outputs_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    code = manage._info()
    out = capsys.readouterr().out
    assert code == 0
    assert "Project root:" in out
    assert "Commands: logster, logster-manage" in out


def test_manage_clean_removes_known_artifacts(tmp_path: Path) -> None:
    egg = tmp_path / "logster.egg-info"
    pycache = tmp_path / "logster" / "__pycache__"
    egg.mkdir()
    pycache.mkdir(parents=True)
    (pycache / "x.pyc").write_text("x", encoding="utf-8")

    old_root = manage.PROJECT_ROOT
    manage.PROJECT_ROOT = tmp_path
    try:
        code = manage._clean(dry_run=False)
    finally:
        manage.PROJECT_ROOT = old_root

    assert code == 0
    assert not egg.exists()
    assert not pycache.exists()


def test_manage_test_uses_pytest_when_uv_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage.shutil, "which", lambda _: None)
    called: list[list[str]] = []

    def fake_run(cmd: list[str]) -> int:
        called.append(cmd)
        return 0

    monkeypatch.setattr(manage, "_run", fake_run)
    code = manage._test()

    assert code == 0
    assert called == [[manage.sys.executable, "-m", "pytest", "-q"]]


def test_manage_demo_prints_expected_output(capsys: pytest.CaptureFixture[str]) -> None:
    code = manage._demo()
    out = capsys.readouterr().out
    assert code == 0
    assert "Input JSON:" in out
    assert "Output:" in out
    assert "[10:12:05][INFO][query.py][query:17]" in out
    assert "query_endpoint_started" in out


def test_manage_demo_applies_external_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "demo.toml"
    config_path.write_text(
        "no_color = true\noutput_style = \"verbose\"\n",
        encoding="utf-8",
    )

    code = manage._demo(config_path=str(config_path))
    out = capsys.readouterr().out
    assert code == 0
    assert "[10:12:05][INFO][query.py][query:17] query_endpoint_started" in out
    assert (
        '{"path":"/query","query":"timing","request_id":"5342fb6b-8ff0-4d9d-84a5-1f6b0e098528","top_k":5}'
        in out
    )


def test_manage_demo_lists_all_color_schemes(capsys: pytest.CaptureFixture[str]) -> None:
    code = manage._demo_color_schemes()
    out = capsys.readouterr().out
    assert code == 0
    assert "Available color schemes:" in out
    for scheme_name in COLOR_SCHEME_PRESETS:
        assert f"{scheme_name}:\n" in out
    assert "\033[" in out
    assert "\n\n" in out


def test_manage_demo_lists_all_color_schemes_in_verbose_mode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = manage._demo_color_schemes(verbose=True)
    out = capsys.readouterr().out
    assert code == 0
    assert "Available color schemes:" in out
    assert "\n{" in out
    assert "\n\n" in out
