from pathlib import Path

import pytest
from typer.testing import CliRunner

from sync_with_uv import __version__
from sync_with_uv.cli import app

from .test_sync import sample_precommit_config, sample_uv_lock  # noqa: F401

runner = CliRunner()


def test_app_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_process_precommit_cli_check(
    sample_uv_lock: Path, sample_precommit_config: Path
) -> None:
    """Test the CLI without writing changes."""
    result = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "--check",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout == (
        "All done!\n"
        "2 package would be changed, 2 packages would be left unchanged.\n"
    )
    assert result.stderr == ""

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_check_q(
    sample_uv_lock: Path, sample_precommit_config: Path
) -> None:
    """Test the CLI without writing changes."""
    result = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "--check",
            "-q",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == ""

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_check_v(
    sample_uv_lock: Path, sample_precommit_config: Path
) -> None:
    """Test the CLI without writing changes."""
    result = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "--check",
            "-v",
        ],
    )
    assert result.exit_code == 1
    assert result.stdout == (
        "black: 23.9.1 -> 23.11.0\n"
        "ruff: v0.0.292 -> v0.1.5\n"
        "unchanged-package: unchanged\n"
        "another-package: not managed in uv\n"
        "\n"
        "All done!\n"
        "2 package would be changed, 2 packages would be left unchanged.\n"
    )
    assert result.stderr == ""

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


@pytest.mark.parametrize("color", [False, True])
def test_process_precommit_cli_diff(
    sample_uv_lock: Path,
    sample_precommit_config: Path,
    color: bool,  # noqa: FBT001
) -> None:
    """Test the CLI with diff."""
    result = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "--diff",
            "--color" if color else "--no-color",
        ],
    )
    assert result.exit_code == 0
    assert "-  rev: 23.9.1  # a comment" in result.stdout
    assert "+  rev: 23.11.0  # a comment" in result.stdout
    assert (
        "All done!\n2 package would be changed, 2 packages would be left unchanged."
        in result.stdout
    )
    assert result.stderr == ""
    if color:
        assert "\033[0m" in result.stdout
    else:
        assert "\033[0m" not in result.stdout

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_with_write(
    sample_uv_lock: Path, sample_precommit_config: Path
) -> None:
    """Test the CLI with writing changes."""
    result = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
        ],
    )
    assert result.exit_code == 0
    assert result.stdout == (
        "All done!\n2 package changed, 2 packages left unchanged.\n"
    )
    assert result.stderr == ""

    # Verify file was modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.11.0" in content
    assert "ruff-pre-commit\n  rev: v0.1.5" in content
