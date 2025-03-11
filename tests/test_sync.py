import textwrap
import tomllib
from pathlib import Path

import pytest

from sync_with_uv.sync_with_uv import (
    load_uv_lock,
    process_precommit_text,
)


@pytest.fixture
def sample_uv_lock(tmp_path: Path) -> Path:
    """Create a sample uv.lock file for testing."""
    uv_lock_content = textwrap.dedent(
        """\
        [project]
        name = "test-project"
        version = "0.1.0"

        [tool.uv]
        required-version = "~=0.6.0"

        [[package]]
        name = "black"
        version = "23.11.0"
        requires-python = ">=3.8"

        [[package]]
        name = "ruff"
        version = "0.1.5"
        requires-python = ">=3.7"
        """
    )
    uv_lock_file = tmp_path / "uv.lock"
    uv_lock_file.write_text(uv_lock_content)
    return uv_lock_file


def test_load_uv_lock(sample_uv_lock: Path) -> None:
    """Test loading a uv.lock file."""
    result = load_uv_lock(sample_uv_lock)
    assert result == {"black": "23.11.0", "ruff": "0.1.5"}


def test_load_uv_lock_malformed(tmp_path: Path) -> None:
    """Test loading a malformed uv.lock file."""
    uv_lock_file = tmp_path / "malformed.lock"
    uv_lock_file.write_text("This is not valid TOML")

    with pytest.raises(tomllib.TOMLDecodeError):
        load_uv_lock(uv_lock_file)


def test_load_uv_lock_empty(tmp_path: Path) -> None:
    """Test loading an empty uv.lock file."""
    uv_lock_file = tmp_path / "empty.lock"
    uv_lock_file.write_text("")

    result = load_uv_lock(uv_lock_file)
    assert result == {}


def test_load_uv_lock_no_packages(tmp_path: Path) -> None:
    """Test loading a uv.lock file with no packages."""
    uv_lock_content = textwrap.dedent(
        """\
        [project]
        name = "test-project"
        version = "0.1.0"

        [tool.uv]
        required-version = "~=0.6.0"
        """
    )
    uv_lock_file = tmp_path / "no_packages.lock"
    uv_lock_file.write_text(uv_lock_content)

    result = load_uv_lock(uv_lock_file)
    assert result == {}


@pytest.fixture
def sample_precommit_config(tmp_path: Path) -> Path:
    """Create a sample pre-commit config file for testing."""
    precommit_content = textwrap.dedent(
        """\
        repos:
        - repo: https://github.com/psf/black-pre-commit-mirror
          rev: 23.9.1  # a comment
          hooks:
            - id: black
        - repo: https://github.com/astral-sh/ruff-pre-commit
          rev: v0.0.292
          hooks:
            - id: ruff
        - repo: local
          hooks:
            - id: local-hook
        """
    )
    precommit_file = tmp_path / ".pre-commit-config.yaml"
    precommit_file.write_text(precommit_content)
    return precommit_file


FIXED_PRECOMMIT_CONTENT = textwrap.dedent(
    """\
    repos:
    - repo: https://github.com/psf/black-pre-commit-mirror
      rev: 23.11.0  # a comment
      hooks:
        - id: black
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.1.5
      hooks:
        - id: ruff
    - repo: local
      hooks:
        - id: local-hook
    """
)


def test_process_precommit_text(
    sample_precommit_config: Path, sample_uv_lock: Path
) -> None:
    precommit_text = sample_precommit_config.read_text()
    uv_data = load_uv_lock(sample_uv_lock)
    result = process_precommit_text(precommit_text, uv_data)
    assert result == FIXED_PRECOMMIT_CONTENT


def test_process_precommit_text_empty() -> None:
    """Test processing an empty pre-commit config."""
    precommit_text = ""
    uv_data = {"black": "23.11.0"}

    result = process_precommit_text(precommit_text, uv_data)
    assert result == ""


def test_process_precommit_text_no_changes_needed() -> None:
    """Test processing a pre-commit config that doesn't need changes."""
    precommit_text = textwrap.dedent(
        """\
        repos:
        - repo: https://github.com/psf/black-pre-commit-mirror
          rev: 23.11.0
          hooks:
            - id: black
        """
    )
    uv_data = {"black": "23.11.0"}

    result = process_precommit_text(precommit_text, uv_data)
    # Should be identical
    assert result == precommit_text


def test_process_precommit_text_complex() -> None:
    """Test processing a more complex pre-commit config."""
    precommit_text = textwrap.dedent(
        """\
        repos:
        - repo: https://github.com/pre-commit/pre-commit-hooks
          rev: v4.4.0
          hooks:
            - id: trailing-whitespace
            - id: end-of-file-fixer
            - id: check-yaml
            - id: check-toml

        - repo: https://github.com/psf/black-pre-commit-mirror
          rev: 23.9.1
          hooks:
            - id: black

        - repo: https://github.com/astral-sh/ruff-pre-commit
          rev: v0.0.292
          hooks:
            - id: ruff
              args: [--fix]

        - repo: https://github.com/pre-commit/mirrors-mypy/
          rev: v1.5.1
          hooks:
            - id: mypy
              additional_dependencies:
                - types-PyYAML

        - repo: https://github.com/unknown/repo
          rev: v2
          hooks:
            - id: some-hook

        - repo: /non/url/repo
          rev: v3
          hooks:
            - id: my-hook
        """
    )
    uv_data = {
        "black": "23.11.0",
        "ruff": "0.1.5",
        "mypy": "1.6.0",
        "pytest": "8.0.0",  # Should be ignored
        "repo": "3.2.1",
    }

    result = process_precommit_text(precommit_text, uv_data)

    # Check that versions were updated
    assert "black-pre-commit-mirror\n  rev: 23.11.0" in result
    assert "ruff-pre-commit\n  rev: v0.1.5" in result
    assert "mirrors-mypy/\n  rev: v1.6.0" in result
    assert "unknown/repo\n  rev: v3.2.1" in result

    # Check that non-matched repos weren't changed
    assert "pre-commit-hooks\n  rev: v4.4.0" in result
    assert "/non/url/repo\n  rev: v3" in result
