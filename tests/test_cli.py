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


def test_process_precommit_cli_check_no_changes_needed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI check mode when files are already synchronized (returns code 0)."""
    # Create uv.lock with package versions
    uv_lock_file = tmp_path / "uv.lock"
    uv_lock_file.write_text(
        """
[[package]]
name = "black"
version = "23.11.0"

[[package]]
name = "ruff"
version = "0.1.5"
"""
    )

    # Create pre-commit config that matches uv.lock versions
    precommit_file = tmp_path / ".pre-commit-config.yaml"
    precommit_file.write_text(
        """repos:
- repo: https://github.com/psf/black-pre-commit-mirror
  rev: 23.11.0
  hooks:
    - id: black
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.5
  hooks:
    - id: ruff
"""
    )

    with pytest.raises(SystemExit) as exc_info:
        app(["-p", str(precommit_file), "-u", str(uv_lock_file), "--check"])

    # Should return exit code 0 when no changes needed
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "All done!" in captured.err
    assert (
        "0 package would be changed, 2 packages would be left unchanged" in captured.err
    )
    assert captured.out == ""


def test_cli_exception_handling_quiet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test that error messages are shown even in quiet mode."""
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
                "-q",
            ]
        )
    assert exc_info.value.code == 123
    captured = capsys.readouterr()
    # Error messages should still be shown in quiet mode
    assert "Error:" in captured.err
    assert captured.out == ""


def test_cli_write_permission_error(tmp_path: Path) -> None:
    """Test CLI handles file write permission errors."""
    # Create valid files
    uv_lock_file = tmp_path / "uv.lock"
    uv_lock_file.write_text(
        """
[[package]]
name = "black"
version = "23.11.0"
"""
    )

    precommit_file = tmp_path / ".pre-commit-config.yaml"
    precommit_file.write_text(
        """repos:
- repo: https://github.com/psf/black-pre-commit-mirror
  rev: 23.9.1
  hooks:
    - id: black
"""
    )

    # Make the pre-commit file read-only
    precommit_file.chmod(0o444)

    try:
        # The write operation is not wrapped in exception handler,
        # so PermissionError is raised directly
        with pytest.raises(PermissionError):
            app(["-p", str(precommit_file), "-u", str(uv_lock_file)])
    finally:
        # Restore write permissions for cleanup
        precommit_file.chmod(0o644)


def test_cli_missing_uv_lock(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI handles missing uv.lock file."""
    nonexistent_uv_lock = tmp_path / "nonexistent.lock"

    precommit_file = tmp_path / ".pre-commit-config.yaml"
    precommit_file.write_text("repos: []")

    with pytest.raises(SystemExit) as exc_info:
        app(["-p", str(precommit_file), "-u", str(nonexistent_uv_lock)])

    # cyclopts validates file existence at CLI level, returning exit code 1
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_cli_missing_precommit_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI handles missing pre-commit config file."""
    uv_lock_file = tmp_path / "uv.lock"
    uv_lock_file.write_text(
        """
[[package]]
name = "black"
version = "23.11.0"
"""
    )

    nonexistent_precommit = tmp_path / "nonexistent.yaml"

    with pytest.raises(SystemExit) as exc_info:
        app(["-p", str(nonexistent_precommit), "-u", str(uv_lock_file)])

    # cyclopts validates file existence at CLI level, returning exit code 1
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err
