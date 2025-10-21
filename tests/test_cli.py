from pathlib import Path

import pytest
from colorama import Fore

from sync_with_uv import __version__
from sync_with_uv.cli import app

from .test_sync import sample_precommit_config, sample_uv_lock  # noqa: F401


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        app("--version")
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_process_precommit_cli_check(
    sample_uv_lock: Path,
    sample_precommit_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the CLI without writing changes."""
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "-p",
                str(sample_precommit_config),
                "-u",
                str(sample_uv_lock),
                "--check",
            ]
        )
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == (
        "All done!\n"
        "2 package would be changed, 2 packages would be left unchanged.\n"
    )
    assert captured.out == ""

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_check_q(
    sample_uv_lock: Path,
    sample_precommit_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the CLI without writing changes."""
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "-p",
                str(sample_precommit_config),
                "-u",
                str(sample_uv_lock),
                "--check",
                "-q",
            ]
        )
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_check_v(
    sample_uv_lock: Path,
    sample_precommit_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the CLI without writing changes."""
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "-p",
                str(sample_precommit_config),
                "-u",
                str(sample_uv_lock),
                "--check",
                "-v",
            ]
        )
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == (
        "black: 23.9.1 -> 23.11.0\n"
        "ruff: v0.0.292 -> v0.1.5\n"
        "unchanged-package: unchanged\n"
        "another-package: not managed in uv\n"
        "\n"
        "All done!\n"
        "2 package would be changed, 2 packages would be left unchanged.\n"
    )
    assert captured.out == ""

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


@pytest.mark.parametrize("color", [False, True])
def test_process_precommit_cli_diff(
    sample_uv_lock: Path,
    sample_precommit_config: Path,
    color: bool,  # noqa: FBT001
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the CLI with diff."""
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "-p",
                str(sample_precommit_config),
                "-u",
                str(sample_uv_lock),
                "--diff",
                "--color" if color else "--no-color",
            ]
        )
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert (
        "All done!\n2 package would be changed, 2 packages would be left unchanged."
        in captured.err
    )
    assert "-  rev: 23.9.1  # a comment" in captured.out
    assert "+  rev: 23.11.0  # a comment" in captured.out
    if color:
        assert Fore.RESET in captured.out
    else:
        assert Fore.RESET not in captured.out

    # Verify file wasn't modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.9.1" in content
    assert "ruff-pre-commit\n  rev: v0.0.292" in content


def test_process_precommit_cli_with_write(
    sample_uv_lock: Path,
    sample_precommit_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test the CLI with writing changes."""
    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "-p",
                str(sample_precommit_config),
                "-u",
                str(sample_uv_lock),
            ]
        )
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == (
        "All done!\n2 package changed, 2 packages left unchanged.\n"
    )
    assert captured.out == ""

    # Verify file was modified
    content = sample_precommit_config.read_text()
    assert "black-pre-commit-mirror\n  rev: 23.11.0" in content
    assert "ruff-pre-commit\n  rev: v0.1.5" in content


def test_cli_exception_handling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI handles exceptions and exits with code 123."""
    # Create a malformed uv.lock file
    malformed_uv_lock = tmp_path / "uv.lock"
    malformed_uv_lock.write_text("invalid toml content: [[[")

    precommit_config = tmp_path / ".pre-commit-config.yaml"
    precommit_config.write_text("repos: []")

    with pytest.raises(SystemExit) as exc_info:
        app(
            [
                "-p",
                str(precommit_config),
                "-u",
                str(malformed_uv_lock),
            ]
        )
    assert exc_info.value.code == 123
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert captured.out == ""
