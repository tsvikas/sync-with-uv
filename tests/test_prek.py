import functools
import textwrap
from pathlib import Path

import pytest

from sync_with_uv.sync_with_uv import (
    load_uv_lock,
    process_config_text,
)

process_prek_toml_text = functools.partial(process_config_text, config_format="toml")


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
    result, changes = process_config_text(prek_text, uv_data, config_format="toml")
    assert result == FIXED_PREK_CONTENT
    assert changes.repos == {
        "ruff": ("v0.14.0", "v0.15.0"),
        "gitleaks": ("v8.30.0", "v8.31.0"),
        "typos": ("v1.43.3", "v1.44.0"),
        "unknown-tool": False,
    }
    assert changes.lines == {}


def test_process_prek_toml_text_empty() -> None:
    """Test processing an empty prek.toml."""
    result, changes = process_config_text("", {"ruff": "0.15.0"}, config_format="toml")
    assert result == ""
    assert changes.repos == {}
    assert changes.lines == {}


def test_process_prek_toml_text_no_changes_needed() -> None:
    """Test processing a prek.toml that doesn't need changes."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = "https://github.com/astral-sh/ruff-pre-commit"
        rev = "v0.15.0"
        hooks = [{ id = "ruff" }]
        """)
    uv_data = {"ruff": "0.15.0"}
    result, changes = process_config_text(prek_text, uv_data, config_format="toml")
    assert result == prek_text
    assert changes.repos == {"ruff": True}
    assert changes.lines == {}


def test_process_prek_toml_text_single_quotes() -> None:
    """Test that single-quoted TOML values are handled correctly."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = 'https://github.com/astral-sh/ruff-pre-commit'
        rev = 'v0.14.0'
        hooks = [{ id = 'ruff' }]
        """)
    uv_data = {"ruff": "0.15.0"}
    result, changes = process_config_text(prek_text, uv_data, config_format="toml")
    assert "rev = 'v0.15.0'" in result
    assert changes.repos == {"ruff": ("v0.14.0", "v0.15.0")}
    assert changes.lines == {}


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
    result, changes = process_config_text(prek_text, uv_data, config_format="toml")
    assert result == prek_text
    assert changes.repos == {}
    assert changes.lines == {}


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
        prek_text,
        uv_data,
        user_repo_mappings=user_repo_mappings,
        user_version_mappings=user_version_mappings,
    )
    assert 'rev = "v2.1.0"' in result
    assert 'rev = "v0.15.0"' in result
    assert changes.repos == {
        "custom-tool": ("v1.0.0", "v2.1.0"),
        "ruff": ("v0.14.0", "v0.15.0"),
    }
    assert changes.lines == {}


def test_sync_additional_dependencies_pragma_toml() -> None:
    """Pragma-annotated dependencies in a multi-line TOML array are pinned."""
    prek_text = textwrap.dedent("""\
        [[repos]]
        repo = "https://github.com/pre-commit/mirrors-mypy"
        rev = "v1.5.1"

        [[repos.hooks]]
        id = "mypy"
        additional_dependencies = [
          "pydantic>=2.0",  # sync-with-uv
          'types-PyYAML==6.0.0',  # sync-with-uv
          "rich>=10",
        ]
        """)
    uv_data = {"mypy": "1.5.1", "pydantic": "2.5.0", "types-pyyaml": "6.0.1"}

    result, changes = process_config_text(prek_text, uv_data, config_format="toml")

    assert '  "pydantic==2.5.0",  # sync-with-uv' in result
    assert "  'types-PyYAML==6.0.1',  # sync-with-uv" in result
    # lines without a pragma are never touched
    assert '  "rich>=10",' in result
    assert changes.repos == {"mypy": True}
    assert changes.lines == {
        8: ("pydantic", ">=2.0", "==2.5.0"),
        9: ("types-pyyaml", "==6.0.0", "==6.0.1"),
    }


def test_sync_additional_dependencies_toml_bare_adds_specifier() -> None:
    """A bare pragma dependency in prek.toml gets an exact pin added."""
    prek_text = textwrap.dedent("""\
        [[repos.hooks]]
        id = "mypy"
        additional_dependencies = [
          "pydantic",  # sync-with-uv
          'attrs>=1',  # sync-with-uv
        ]
        """)
    uv_data = {"pydantic": "2.5.0", "attrs": "23.2.0"}

    result, changes = process_config_text(prek_text, uv_data, config_format="toml")

    assert '  "pydantic==2.5.0",  # sync-with-uv' in result
    assert "  'attrs==23.2.0',  # sync-with-uv" in result
    assert changes.repos == {}
    assert changes.lines == {
        4: ("pydantic", "", "==2.5.0"),
        5: ("attrs", ">=1", "==23.2.0"),
    }


def test_sync_additional_dependencies_toml_bare_adds_specifier_with_marker() -> None:
    """A bare pragma dependency with a marker in prek.toml pins before the marker."""
    prek_text = textwrap.dedent("""\
        [[repos.hooks]]
        id = "mypy"
        additional_dependencies = [
          'types-PyYAML ; python_version < "3.11"',  # sync-with-uv
        ]
        """)
    uv_data = {"types-pyyaml": "6.0.1"}

    result, changes = process_config_text(prek_text, uv_data, config_format="toml")

    assert (
        "  'types-PyYAML==6.0.1 ; python_version < \"3.11\"',  # sync-with-uv" in result
    )
    assert changes.repos == {}
    assert changes.lines == {
        4: ("types-pyyaml", "", "==6.0.1"),
    }


def test_sync_additional_dependencies_toml_errors() -> None:
    """Invalid pragma dependencies in prek.toml are reported as errors."""
    prek_text = textwrap.dedent("""\
        [[repos.hooks]]
        id = "mypy"
        additional_dependencies = [
          # sync-with-uv
          "not-locked==1.0.0",  # sync-with-uv
        ]
        """)
    uv_data = {"pydantic": "2.5.0"}

    with pytest.raises(
        ValueError, match="invalid '# sync-with-uv' dependencies"
    ) as exc_info:
        process_config_text(prek_text, uv_data, config_format="toml")
    message = str(exc_info.value)
    assert "line 4: no dependency to sync" in message
    assert "line 5: 'not-locked' is not in uv.lock" in message


def test_sync_additional_dependencies_toml_multiple_on_line_errors() -> None:
    """More than one dependency on a pragma line is rejected in prek.toml too."""
    prek_text = textwrap.dedent("""\
        [[repos.hooks]]
        id = "mypy"
        additional_dependencies = [
          "pydantic==2.0", "attrs>=1",  # sync-with-uv
        ]
        """)
    uv_data = {"pydantic": "2.5.0", "attrs": "23.2.0"}

    with pytest.raises(ValueError, match="more than one dependency") as exc_info:
        process_config_text(prek_text, uv_data, config_format="toml")
    assert "line 4" in str(exc_info.value)


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
    result, _changes = process_config_text(prek_text, uv_data, config_format="toml")
    assert result == prek_text.replace("v0.14.0", "v0.15.0")
