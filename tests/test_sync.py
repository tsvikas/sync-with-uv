import textwrap
from pathlib import Path

import pytest
import tomli

from sync_with_uv.sync_with_uv import (
    load_uv_lock,
    process_config_text,
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
        name = "black"
        version = "23.11.0"
        requires-python = ">=3.8"

        [[package]]
        name = "ruff"
        version = "0.1.5"
        requires-python = ">=3.7"

        [[package]]
        name = "unchanged-package"
        version = "1.2.3"
        requires-python = ">=3.7"
        """)
    uv_lock_file = tmp_path / "uv.lock"
    uv_lock_file.write_text(uv_lock_content)
    return uv_lock_file


def test_load_uv_lock(sample_uv_lock: Path) -> None:
    """Test loading a uv.lock file."""
    result = load_uv_lock(sample_uv_lock)
    assert result == {
        "black": "23.11.0",
        "ruff": "0.1.5",
        "unchanged-package": "1.2.3",
    }


def test_load_uv_lock_malformed(tmp_path: Path) -> None:
    """Test loading a malformed uv.lock file."""
    uv_lock_file = tmp_path / "malformed.lock"
    uv_lock_file.write_text("This is not valid TOML")

    with pytest.raises(tomli.TOMLDecodeError):
        load_uv_lock(uv_lock_file)


def test_load_uv_lock_empty(tmp_path: Path) -> None:
    """Test loading an empty uv.lock file."""
    uv_lock_file = tmp_path / "empty.lock"
    uv_lock_file.write_text("")

    result = load_uv_lock(uv_lock_file)
    assert result == {}


def test_load_uv_lock_no_packages(tmp_path: Path) -> None:
    """Test loading a uv.lock file with no packages."""
    uv_lock_content = textwrap.dedent("""\
        [project]
        name = "test-project"
        version = "0.1.0"

        [tool.uv]
        required-version = "~=0.6.0"
        """)
    uv_lock_file = tmp_path / "no_packages.lock"
    uv_lock_file.write_text(uv_lock_content)

    result = load_uv_lock(uv_lock_file)
    assert result == {}


@pytest.fixture
def sample_precommit_config(tmp_path: Path) -> Path:
    """Create a sample pre-commit config file for testing."""
    precommit_content = textwrap.dedent("""\
        repos:
        - repo: https://github.com/psf/black-pre-commit-mirror
          rev: 23.9.1  # a comment
          hooks:
            - id: black
        - repo: https://github.com/astral-sh/ruff-pre-commit
          rev: v0.0.292
          hooks:
            - id: ruff
        - repo: https://github.com/example/unchanged-package
          rev: v1.2.3
          hooks:
            - id: something
        - repo: https://github.com/example/another-package
          rev: v2.3
          hooks:
            - id: something-else
        - repo: local
          hooks:
            - id: local-hook
        """)
    precommit_file = tmp_path / ".pre-commit-config.yaml"
    precommit_file.write_text(precommit_content)
    return precommit_file


FIXED_PRECOMMIT_CONTENT = textwrap.dedent("""\
    repos:
    - repo: https://github.com/psf/black-pre-commit-mirror
      rev: 23.11.0  # a comment
      hooks:
        - id: black
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.1.5
      hooks:
        - id: ruff
    - repo: https://github.com/example/unchanged-package
      rev: v1.2.3
      hooks:
        - id: something
    - repo: https://github.com/example/another-package
      rev: v2.3
      hooks:
        - id: something-else
    - repo: local
      hooks:
        - id: local-hook
    """)


def test_process_precommit_text(
    sample_precommit_config: Path, sample_uv_lock: Path
) -> None:
    precommit_text = sample_precommit_config.read_text()
    uv_data = load_uv_lock(sample_uv_lock)
    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")
    assert result == FIXED_PRECOMMIT_CONTENT
    assert changes.repos == {
        "black": ("23.9.1", "23.11.0"),
        "ruff": ("v0.0.292", "v0.1.5"),
        "unchanged-package": True,
        "another-package": False,
    }
    assert changes.lines == {}


def test_process_precommit_text_empty() -> None:
    """Test processing an empty pre-commit config."""
    precommit_text = ""
    uv_data = {"black": "23.11.0"}

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")
    assert result == ""
    assert changes.repos == {}
    assert changes.lines == {}


def test_process_precommit_text_no_changes_needed() -> None:
    """Test processing a pre-commit config that doesn't need changes."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: https://github.com/psf/black-pre-commit-mirror
          rev: 23.11.0
          hooks:
            - id: black
        """)
    uv_data = {"black": "23.11.0"}

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")
    # Should be identical
    assert result == precommit_text
    assert changes.repos == {"black": True}
    assert changes.lines == {}


def test_process_precommit_text_complex() -> None:
    """Test processing a more complex pre-commit config."""
    precommit_text = textwrap.dedent("""\
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
        """)
    uv_data = {
        "black": "23.11.0",
        "ruff": "0.1.5",
        "mypy": "1.6.0",
        "pytest": "8.0.0",  # Should be ignored
        "repo": "3.2.1",
    }

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")

    # Check that versions were updated
    assert "black-pre-commit-mirror\n  rev: 23.11.0" in result
    assert "ruff-pre-commit\n  rev: v0.1.5" in result
    assert "mirrors-mypy/\n  rev: v1.6.0" in result
    assert "unknown/repo\n  rev: v3.2.1" in result

    # Check that non-matched repos weren't changed
    assert "pre-commit-hooks\n  rev: v4.4.0" in result
    assert "/non/url/repo\n  rev: v3" in result

    assert changes.repos == {
        "pre-commit-hooks": False,
        "black": ("23.9.1", "23.11.0"),
        "ruff": ("v0.0.292", "v0.1.5"),
        "mypy": ("v1.5.1", "v1.6.0"),
        "repo": ("v2", "v3.2.1"),
        "/non/url/repo": False,
    }
    # the `- types-PyYAML` line has no pragma, so it is not synced
    assert changes.lines == {}


def test_process_precommit_text_with_user_mappings() -> None:
    """Test processing pre-commit config with user-defined mappings."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: https://github.com/example/custom-tool
          rev: v1.0.0
          hooks:
            - id: custom
        - repo: https://github.com/psf/black-pre-commit-mirror
          rev: 23.9.1
          hooks:
            - id: black
        """)

    uv_data = {
        "custom-tool": "2.1.0",
        "black": "23.11.0",
    }

    user_repo_mappings = {"https://github.com/example/custom-tool": "custom-tool"}

    user_version_mappings = {"https://github.com/example/custom-tool": "v${version}"}

    result, changes = process_config_text(
        precommit_text,
        uv_data,
        config_format="yaml",
        user_repo_mappings=user_repo_mappings,
        user_version_mappings=user_version_mappings,
    )

    # Check that user mappings were applied
    assert "custom-tool\n  rev: v2.1.0" in result
    assert "black-pre-commit-mirror\n  rev: 23.11.0" in result

    assert changes.repos == {
        "custom-tool": ("v1.0.0", "v2.1.0"),
        "black": ("23.9.1", "23.11.0"),
    }
    assert changes.lines == {}


@pytest.mark.parametrize(
    "line_ending",
    ["\n", "\r\n", "\r"],
    ids=["LF", "CRLF", "CR"],
)
def test_process_precommit_text_preserves_line_endings_no_version_change(
    line_ending: str,
) -> None:
    """Test that line endings are preserved when version is already correct."""
    precommit_text = line_ending.join(
        [
            "repos:",
            "- repo: https://github.com/psf/black-pre-commit-mirror",
            "  rev: 23.11.0",
            "  hooks:",
            "    - id: black",
            "- repo: https://github.com/unchanged/unchanged",
            "  rev: 1.2.3",
            "  hooks:",
            "    - id: unchanged",
        ]
    )
    # Package exists in uv.lock but version is already correct
    uv_data = {"black": "23.11.0"}

    result, _changes = process_config_text(
        precommit_text, uv_data, config_format="yaml"
    )

    # Result should be identical to input when version is already correct
    assert result == precommit_text


@pytest.mark.parametrize(
    "line_ending",
    ["\n", "\r\n", "\r"],
    ids=["LF", "CRLF", "CR"],
)
def test_process_precommit_text_preserves_line_endings(
    line_ending: str,
) -> None:
    """Test that line endings are preserved and the version is updated in the output."""
    precommit_text = line_ending.join(
        [
            "repos:",
            "- repo: https://github.com/psf/black-pre-commit-mirror",
            "  rev: 23.11.0",
            "  hooks:",
            "    - id: black",
            "- repo: https://github.com/unchanged/unchanged",
            "  rev: 1.2.3",
            "  hooks:",
            "    - id: unchanged",
        ]
    )
    # Package exists in uv.lock but version is already correct
    uv_data = {"black": "24.0.0"}

    result, _changes = process_config_text(
        precommit_text, uv_data, config_format="yaml"
    )

    # Result should be identical to input when version is already correct
    assert result == precommit_text.replace("23.11.0", "24.0.0")


def test_sync_additional_dependencies_pragma() -> None:
    """Pragma-annotated additional_dependencies are pinned to the uv.lock version."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: https://github.com/pre-commit/mirrors-mypy
          rev: v1.5.1
          hooks:
            - id: mypy
              additional_dependencies:
                - pydantic==2.0.0  # sync-with-uv
                - types-PyYAML>=6.0  # sync-with-uv
                - rich>=10  # not synced, no pragma
        """)
    uv_data = {
        "mypy": "1.5.1",
        "pydantic": "2.5.0",
        "types-pyyaml": "6.0.1",
        "rich": "13.0.0",
    }

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")

    assert "- pydantic==2.5.0  # sync-with-uv" in result
    # operator is normalized to == and original name casing is preserved
    assert "- types-PyYAML==6.0.1  # sync-with-uv" in result
    # lines without a pragma are never touched
    assert "- rich>=10  # not synced, no pragma" in result
    # the rev is a per-package repo change; the deps are per-line changes
    assert changes.repos == {"mypy": True}
    assert changes.lines == {
        7: ("pydantic", "==2.0.0", "==2.5.0"),
        8: ("types-pyyaml", ">=6.0", "==6.0.1"),
    }


def test_sync_additional_dependencies_bare_adds_specifier() -> None:
    """A pragma dependency without a specifier gets an exact pin added."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: local
          hooks:
            - id: mypy
              additional_dependencies:
                - pydantic  # sync-with-uv
                - attrs[speedups]  # sync-with-uv
                - types-PyYAML ; python_version < "3.11"  # sync-with-uv
        """)
    uv_data = {"pydantic": "2.5.0", "attrs": "23.2.0", "types-pyyaml": "6.0.1"}

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")

    assert "- pydantic==2.5.0  # sync-with-uv" in result
    # extras are preserved when the pin is inserted
    assert "- attrs[speedups]==23.2.0  # sync-with-uv" in result
    # the pin is inserted before an environment marker
    assert '- types-PyYAML==6.0.1 ; python_version < "3.11"  # sync-with-uv' in result
    # a bare dependency reports an empty old specifier
    assert changes.repos == {}
    assert changes.lines == {
        6: ("pydantic", "", "==2.5.0"),
        7: ("attrs", "", "==23.2.0"),
        8: ("types-pyyaml", "", "==6.0.1"),
    }


def test_sync_additional_dependencies_no_dependency_errors() -> None:
    """A pragma on a line with no dependency to sync is an error."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: local
          hooks:
            - id: mypy  # sync-with-uv
              additional_dependencies:
                # sync-with-uv
                - pydantic==2.0.0  # sync-with-uv
        """)
    uv_data = {"pydantic": "2.5.0"}

    with pytest.raises(ValueError, match="no dependency to sync") as exc_info:
        process_config_text(precommit_text, uv_data, config_format="yaml")
    message = str(exc_info.value)
    # both the hook id line and the stray comment line are reported
    assert "line 4: no dependency to sync" in message
    assert "line 6: no dependency to sync" in message


@pytest.mark.parametrize(
    "dep_line",
    [
        "- pydantic==2.0.0, attrs==1.0  # sync-with-uv",  # comma-separated
        "- pydantic==2.0.0 attrs==1.0  # sync-with-uv",  # space-separated
    ],
    ids=["comma", "space"],
)
def test_sync_additional_dependencies_multiple_on_line_errors(dep_line: str) -> None:
    """More than one dependency on a pragma line is an error, not a partial sync."""
    precommit_text = textwrap.dedent(f"""\
        repos:
        - repo: local
          hooks:
            - id: mypy
              additional_dependencies:
                {dep_line}
        """)
    uv_data = {"pydantic": "2.5.0", "attrs": "23.2.0"}

    with pytest.raises(ValueError, match="more than one dependency") as exc_info:
        process_config_text(precommit_text, uv_data, config_format="yaml")
    assert "line 6" in str(exc_info.value)


def test_sync_additional_dependencies_marker_comma_not_confused_for_second_dep() -> (
    None
):
    """A comma inside an environment marker is not mistaken for a second dependency."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: local
          hooks:
            - id: mypy
              additional_dependencies:
                - pydantic>=1.0; extra == "a,b"  # sync-with-uv
        """)
    uv_data = {"pydantic": "2.5.0"}

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")

    assert '- pydantic==2.5.0; extra == "a,b"  # sync-with-uv' in result
    assert changes.lines == {6: ("pydantic", ">=1.0", "==2.5.0")}


@pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"], ids=["LF", "CRLF", "CR"])
def test_sync_additional_dependencies_preserves_line_endings(line_ending: str) -> None:
    """Dependency syncing preserves the original line endings (issue #24 area)."""
    precommit_text = line_ending.join(
        [
            "      additional_dependencies:",
            "        - pydantic>=2.0  # sync-with-uv",
            "        - attrs  # sync-with-uv",
        ]
    )
    uv_data = {"pydantic": "2.5.0", "attrs": "23.2.0"}

    result, _changes = process_config_text(
        precommit_text, uv_data, config_format="yaml"
    )

    assert result == precommit_text.replace("pydantic>=2.0", "pydantic==2.5.0").replace(
        "- attrs  ", "- attrs==23.2.0  "
    )


def test_sync_additional_dependencies_extras_and_marker() -> None:
    """Extras and environment markers are preserved when pinning."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: https://github.com/pre-commit/mirrors-mypy
          rev: v1.5.1
          hooks:
            - id: mypy
              additional_dependencies:
                - pydantic[email]>=1.0,<3.0  # sync-with-uv
                - attrs==22.0.0; python_version < "3.11"  # sync-with-uv
        """)
    uv_data = {"mypy": "1.5.1", "pydantic": "2.5.0", "attrs": "23.2.0"}

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")

    assert "- pydantic[email]==2.5.0  # sync-with-uv" in result
    assert '- attrs==23.2.0; python_version < "3.11"  # sync-with-uv' in result
    assert changes.repos == {"mypy": True}
    assert changes.lines == {
        7: ("pydantic", ">=1.0,<3.0", "==2.5.0"),
        8: ("attrs", "==22.0.0", "==23.2.0"),
    }


def test_sync_additional_dependencies_not_in_lock_errors() -> None:
    """A pragma dependency missing from uv.lock is an error (explicit opt-in)."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: local
          hooks:
            - id: something
              additional_dependencies:
                - some-tool==1.0.0  # sync-with-uv
        """)
    uv_data = {"pydantic": "2.5.0"}

    with pytest.raises(ValueError, match=r"'some-tool' is not in uv\.lock") as exc_info:
        process_config_text(precommit_text, uv_data, config_format="yaml")
    # the error points at the offending line
    assert "line 6" in str(exc_info.value)


def test_sync_additional_dependencies_reports_all_errors() -> None:
    """All invalid pragma dependencies are collected before raising."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: local
          hooks:
            - id: something
              additional_dependencies:
                - typo-pkg>=1.0  # sync-with-uv
                # sync-with-uv
                - pydantic==2.5.0  # sync-with-uv
        """)
    uv_data = {"pydantic": "2.5.0"}

    with pytest.raises(
        ValueError, match="invalid '# sync-with-uv' dependencies"
    ) as exc_info:
        process_config_text(precommit_text, uv_data, config_format="yaml")
    message = str(exc_info.value)
    assert "line 6: 'typo-pkg' is not in uv.lock" in message
    assert "line 7: no dependency to sync" in message


def test_sync_additional_dependencies_already_pinned() -> None:
    """A dependency already at the locked version is reported as unchanged."""
    precommit_text = textwrap.dedent("""\
        repos:
        - repo: local
          hooks:
            - id: something
              additional_dependencies:
                - pydantic==2.5.0  # sync-with-uv
        """)
    uv_data = {"pydantic": "2.5.0"}

    result, changes = process_config_text(precommit_text, uv_data, config_format="yaml")

    assert result == precommit_text
    # an already-correct line is recorded with matching old/new specifiers
    assert changes.repos == {}
    assert changes.lines == {6: ("pydantic", "==2.5.0", "==2.5.0")}
