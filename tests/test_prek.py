import textwrap
from pathlib import Path

import pytest

from sync_with_uv.sync_with_uv import (
    load_uv_lock,
    process_prek_toml_text,
)


@pytest.fixture
def sample_uv_lock(tmp_path: Path) -> Path:
    """Create a sample uv.lock file for testing."""
    uv_lock_content = textwrap.dedent("""\
        [project]
        name = "test-project"
        version = "0.1.0"

        [tool.uv]
        required-version = "~=0.6.0"

        [[package]]
        name = "ruff"
        version = "0.15.0"
        requires-python = ">=3.7"

        [[package]]
        name = "gitleaks"
        version = "8.31.0"
        requires-python = ">=3.7"

        [[package]]
        name = "typos"
        version = "1.44.0"
        requires-python = ">=3.7"
        """)
    uv_lock_file = tmp_path / "uv.lock"
    uv_lock_file.write_text(uv_lock_content)
    return uv_lock_file


@pytest.fixture
def sample_prek_config(tmp_path: Path) -> Path:
    """Create a sample prek.toml file for testing."""
    prek_content = textwrap.dedent("""\
        minimum_prek_version = "0.3.2"

        [[repos]]
        repo = "builtin"
        hooks = [
          { id = "trailing-whitespace" },
        ]

        [[repos]]
        repo = "https://github.com/astral-sh/ruff-pre-commit"
        rev = "v0.14.0"
        hooks = [{ id = "ruff", args = ["--fix"] }]

        [[repos]]
        repo = "https://github.com/gitleaks/gitleaks"
        rev = "v8.30.0"
        hooks = [{ id = "gitleaks" }]

        [[repos]]
        repo = "https://github.com/crate-ci/typos"
        rev = "v1.43.3"
        hooks = [{ id = "typos" }]

        [[repos]]
        repo = "https://github.com/example/unknown-tool"
        rev = "v1.0.0"
        hooks = [{ id = "unknown" }]

        [[repos]]
        repo = "local"

        [[repos.hooks]]
        id = "my-local-hook"
        entry = "echo hello"
        language = "system"
        """)
    prek_file = tmp_path / "prek.toml"
    prek_file.write_text(prek_content)
    return prek_file


FIXED_PREK_CONTENT = textwrap.dedent("""\
    minimum_prek_version = "0.3.2"

    [[repos]]
    repo = "builtin"
    hooks = [
      { id = "trailing-whitespace" },
    ]

    [[repos]]
    repo = "https://github.com/astral-sh/ruff-pre-commit"
    rev = "v0.15.0"
    hooks = [{ id = "ruff", args = ["--fix"] }]

    [[repos]]
    repo = "https://github.com/gitleaks/gitleaks"
    rev = "v8.31.0"
    hooks = [{ id = "gitleaks" }]

    [[repos]]
    repo = "https://github.com/crate-ci/typos"
    rev = "v1.44.0"
    hooks = [{ id = "typos" }]

    [[repos]]
    repo = "https://github.com/example/unknown-tool"
    rev = "v1.0.0"
    hooks = [{ id = "unknown" }]

    [[repos]]
    repo = "local"

    [[repos.hooks]]
    id = "my-local-hook"
    entry = "echo hello"
    language = "system"
    """)


def test_process_prek_toml_text(sample_prek_config: Path, sample_uv_lock: Path) -> None:
    prek_text = sample_prek_config.read_text()
    uv_data = load_uv_lock(sample_uv_lock)
    result, changes = process_prek_toml_text(prek_text, uv_data)
    assert result == FIXED_PREK_CONTENT
    assert changes == {
        "ruff": ("v0.14.0", "v0.15.0"),
        "gitleaks": ("v8.30.0", "v8.31.0"),
        "typos": ("v1.43.3", "v1.44.0"),
        "unknown-tool": False,
    }


def test_process_prek_toml_text_empty() -> None:
    """Test processing an empty prek.toml."""
    result, changes = process_prek_toml_text("", {"ruff": "0.15.0"})
    assert result == ""
    assert changes == {}


def test_process_prek_toml_text_no_changes_needed() -> None:
    """Test processing a prek.toml that doesn't need changes."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = "https://github.com/astral-sh/ruff-pre-commit"
        rev = "v0.15.0"
        hooks = [{ id = "ruff" }]
        """)
    uv_data = {"ruff": "0.15.0"}
    result, changes = process_prek_toml_text(prek_text, uv_data)
    assert result == prek_text
    assert changes == {"ruff": True}


def test_process_prek_toml_text_single_quotes() -> None:
    """Test that single-quoted TOML values are handled correctly."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = 'https://github.com/astral-sh/ruff-pre-commit'
        rev = 'v0.14.0'
        hooks = [{ id = 'ruff' }]
        """)
    uv_data = {"ruff": "0.15.0"}
    result, changes = process_prek_toml_text(prek_text, uv_data)
    assert "rev = 'v0.15.0'" in result
    assert changes == {"ruff": ("v0.14.0", "v0.15.0")}


def test_process_prek_toml_text_builtin_and_local_skipped() -> None:
    """Test that builtin and local repos are skipped without errors."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = "builtin"
        hooks = [{ id = "trailing-whitespace" }]

        [[repos]]
        repo = "local"

        [[repos.hooks]]
        id = "my-hook"
        entry = "echo hello"
        language = "system"
        """)
    uv_data = {"ruff": "0.15.0"}
    result, changes = process_prek_toml_text(prek_text, uv_data)
    assert result == prek_text
    assert changes == {}


def test_process_prek_toml_text_with_user_mappings() -> None:
    """Test processing prek.toml with user-defined mappings."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = "https://github.com/example/custom-tool"
        rev = "v1.0.0"
        hooks = [{ id = "custom" }]

        [[repos]]
        repo = "https://github.com/astral-sh/ruff-pre-commit"
        rev = "v0.14.0"
        hooks = [{ id = "ruff" }]
        """)
    uv_data = {"custom-tool": "2.1.0", "ruff": "0.15.0"}
    user_repo_mappings = {"https://github.com/example/custom-tool": "custom-tool"}
    user_version_mappings = {"https://github.com/example/custom-tool": "v${version}"}

    result, changes = process_prek_toml_text(
        prek_text, uv_data, user_repo_mappings, user_version_mappings
    )
    assert 'rev = "v2.1.0"' in result
    assert 'rev = "v0.15.0"' in result
    assert changes == {
        "custom-tool": ("v1.0.0", "v2.1.0"),
        "ruff": ("v0.14.0", "v0.15.0"),
    }


@pytest.mark.parametrize(
    "line_ending",
    ["\n", "\r\n", "\r"],
    ids=["LF", "CRLF", "CR"],
)
def test_process_prek_toml_text_preserves_line_endings(line_ending: str) -> None:
    """Test that line endings are preserved in prek.toml processing."""
    prek_text = line_ending.join(
        [
            "[[repos]]",
            'repo = "https://github.com/astral-sh/ruff-pre-commit"',
            'rev = "v0.14.0"',
            'hooks = [{ id = "ruff" }]',
        ]
    )
    uv_data = {"ruff": "0.15.0"}
    result, _changes = process_prek_toml_text(prek_text, uv_data)
    assert result == prek_text.replace("v0.14.0", "v0.15.0")
