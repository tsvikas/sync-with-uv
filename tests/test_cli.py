from pathlib import Path

from typer.testing import CliRunner

from sync_with_uv import __version__
from sync_with_uv.cli import app

from .test_sync import sample_precommit_config, sample_uv_lock  # noqa: F401

runner = CliRunner()


def test_app_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_process_precommit_cli_no_write(
    sample_uv_lock: Path, sample_precommit_config: Path  # noqa: F811
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

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_with_write(
    sample_uv_lock: Path, sample_precommit_config: Path  # noqa: F811
) -> None:
    """Test the CLI with writing changes."""
    result = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "-w",
        ],
    )
    assert result.exit_code == 0

    # Verify file was modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.11.0" in content
    assert "ruff-pre-commit\n  rev: v0.1.5" in content


def test_process_precommit_cli_verbose(
    sample_uv_lock: Path,  # noqa: F811
    sample_precommit_config: Path,  # noqa: F811
) -> None:
    """Test the CLI with different verbosity levels."""
    # Test verbose = 0 (no verbose flag)
    result_v0 = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            # No -w to avoid modifying the file, focus on logs
        ],
    )
    assert result_v0.exit_code == 0

    # Test verbose = 1 (-v)
    result_v1 = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "-v",
        ],
    )
    assert result_v1.exit_code == 0

    # Test verbose = 2 (-vv)
    result_v2 = runner.invoke(
        app,
        [
            "-p",
            str(sample_precommit_config),
            "-u",
            str(sample_uv_lock),
            "-v",
            "-v",
        ],
    )
    assert result_v2.exit_code == 0
