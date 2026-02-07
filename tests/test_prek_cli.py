import textwrap
from pathlib import Path

import pytest

from sync_with_uv.cli import app

from .test_prek import sample_prek_config, sample_uv_lock  # noqa: F401


def test_cli_autodetect_prek_toml(
    sample_uv_lock: Path,
    sample_prek_config: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that CLI auto-detects prek.toml when .pre-commit-config.yaml is absent."""
    monkeypatch.chdir(sample_prek_config.parent)
    with pytest.raises(SystemExit) as exc_info:
        app(["-u", str(sample_uv_lock), "--check"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "All done!" in captured.err


def test_cli_explicit_prek_toml(
    sample_uv_lock: Path,
    sample_prek_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that CLI accepts prek.toml via -p flag."""
    with pytest.raises(SystemExit) as exc_info:
        app(["-p", str(sample_prek_config), "-u", str(sample_uv_lock), "--check"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "All done!" in captured.err


def test_cli_prek_toml_write(
    sample_uv_lock: Path,
    sample_prek_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that CLI writes updated prek.toml."""
    with pytest.raises(SystemExit) as exc_info:
        app(["-p", str(sample_prek_config), "-u", str(sample_uv_lock)])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "3 package changed" in captured.err

    content = sample_prek_config.read_text()
    assert 'rev = "v0.15.0"' in content  # ruff updated
    assert 'rev = "v8.31.0"' in content  # gitleaks updated
    assert 'rev = "v1.44.0"' in content  # typos updated


def test_cli_prek_toml_diff(
    sample_uv_lock: Path,
    sample_prek_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that CLI shows diff for prek.toml."""
    with pytest.raises(SystemExit) as exc_info:
        app(["-p", str(sample_prek_config), "-u", str(sample_uv_lock), "--diff"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert '-rev = "v0.14.0"' in captured.out
    assert '+rev = "v0.15.0"' in captured.out


def test_cli_prefers_yaml_over_prek(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that .pre-commit-config.yaml is preferred over prek.toml."""
    monkeypatch.chdir(tmp_path)
    uv_lock = tmp_path / "uv.lock"
    uv_lock.write_text(textwrap.dedent("""\
        [[package]]
        name = "ruff"
        version = "0.15.0"
        """))

    yaml_config = tmp_path / ".pre-commit-config.yaml"
    yaml_config.write_text(textwrap.dedent("""\
        repos:
        - repo: https://github.com/astral-sh/ruff-pre-commit
          rev: v0.14.0
          hooks:
            - id: ruff
        """))

    prek_config = tmp_path / "prek.toml"
    prek_config.write_text(textwrap.dedent("""\
        [[repos]]
        repo = "https://github.com/astral-sh/ruff-pre-commit"
        rev = "v0.14.0"
        hooks = [{ id = "ruff" }]
        """))

    with pytest.raises(SystemExit) as exc_info:
        app(["-u", str(uv_lock)])
    assert exc_info.value.code == 0

    # YAML should be updated, prek.toml should NOT
    assert "v0.15.0" in yaml_config.read_text()
    assert "v0.14.0" in prek_config.read_text()


def test_cli_no_config_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test CLI error when neither config file exists."""
    monkeypatch.chdir(tmp_path)
    uv_lock = tmp_path / "uv.lock"
    uv_lock.write_text(textwrap.dedent("""\
        [[package]]
        name = "ruff"
        version = "0.15.0"
        """))

    with pytest.raises(SystemExit) as exc_info:
        app(["-u", str(uv_lock)])
    assert exc_info.value.code == 123
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
