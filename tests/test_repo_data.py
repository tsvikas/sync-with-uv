from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from sync_with_uv.repo_data import (
    load_user_mappings,
    repo_to_package,
    repo_to_version_template,
)


@pytest.mark.parametrize(
    ("url", "package"),
    [
        ("https://github.com/psf/black-pre-commit-mirror", "black"),
        ("https://github.com/psf/black", "black"),
        ("https://github.com/astral-sh/ruff-pre-commit", "ruff"),
        ("https://github.com/unknown/repo", "repo"),
    ],
)
def test_repo_to_package(url: str, package: str) -> None:
    assert repo_to_package(url) == package


def test_local_repo_to_package() -> None:
    assert repo_to_package("local") is None


@pytest.mark.parametrize(
    ("url", "version_template"),
    [
        ("https://github.com/psf/black-pre-commit-mirror", "${rev}"),
        ("https://github.com/psf/black", "${rev}"),
        ("https://github.com/astral-sh/ruff-pre-commit", "v${rev}"),
    ],
)
def test_repo_to_version_template(url: str, version_template: str) -> None:
    # Test known repos
    assert repo_to_version_template(url) == version_template


def test_unknown_repo_to_version_template() -> None:
    assert repo_to_version_template("https://github.com/unknown/repo") is None


def test_load_user_mappings_nonexistent_file() -> None:
    """Test loading user mappings when pyproject.toml doesn't exist."""
    nonexistent_path = Path("/nonexistent/pyproject.toml")
    repo_mappings, version_mappings = load_user_mappings(nonexistent_path)
    assert repo_mappings == {}
    assert version_mappings == {}


def test_load_user_mappings_empty_config() -> None:
    """Test loading user mappings with empty pyproject.toml."""
    with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[build-system]\nrequires = ["hatchling"]')
        f.flush()
        path = Path(f.name)

    try:
        repo_mappings, version_mappings = load_user_mappings(path)
        assert repo_mappings == {}
        assert version_mappings == {}
    finally:
        path.unlink()


def test_load_user_mappings_with_config() -> None:
    """Test loading user mappings with valid configuration."""
    config_content = """
[tool.sync-with-uv]
repo-to-package = {"https://github.com/example/test" = "test-pkg"}
repo-to-version-template = {"https://github.com/example/test" = "v${rev}"}
"""

    with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(config_content)
        f.flush()
        path = Path(f.name)

    try:
        repo_mappings, version_mappings = load_user_mappings(path)
        assert repo_mappings == {"https://github.com/example/test": "test-pkg"}
        assert version_mappings == {"https://github.com/example/test": "v${rev}"}
    finally:
        path.unlink()


def test_repo_to_package_with_user_mappings() -> None:
    """Test repo_to_package with user-defined mappings."""
    user_mappings = {
        "https://github.com/example/custom": "custom-pkg",
        "https://github.com/example/override": "override-pkg",
    }

    # Test custom mapping
    assert (
        repo_to_package("https://github.com/example/custom", user_mappings)
        == "custom-pkg"
    )

    # Test user mapping overrides built-in
    assert (
        repo_to_package("https://github.com/example/override", user_mappings)
        == "override-pkg"
    )

    # Test fallback to built-in
    assert (
        repo_to_package("https://github.com/psf/black-pre-commit-mirror", user_mappings)
        == "black"
    )

    # Test unknown repo with user mappings
    assert repo_to_package("https://github.com/unknown/repo", user_mappings) == "repo"


def test_repo_to_version_template_with_user_mappings() -> None:
    """Test repo_to_version_template with user-defined mappings."""
    user_mappings = {
        "https://github.com/example/custom": "custom-${rev}",
        "https://github.com/example/override": "user-${rev}",
    }

    # Test custom mapping
    assert (
        repo_to_version_template("https://github.com/example/custom", user_mappings)
        == "custom-${rev}"
    )

    # Test user mapping overrides built-in
    assert (
        repo_to_version_template("https://github.com/example/override", user_mappings)
        == "user-${rev}"
    )

    # Test fallback to built-in
    assert (
        repo_to_version_template(
            "https://github.com/psf/black-pre-commit-mirror", user_mappings
        )
        == "${rev}"
    )

    # Test unknown repo with user mappings
    assert (
        repo_to_version_template("https://github.com/unknown/repo", user_mappings)
        is None
    )


def test_repo_functions_with_empty_user_mappings() -> None:
    """Test repo functions work correctly with empty user mappings."""
    empty_mappings: dict[str, str] = {}

    # Should behave exactly like no user mappings
    assert (
        repo_to_package(
            "https://github.com/psf/black-pre-commit-mirror", empty_mappings
        )
        == "black"
    )
    assert (
        repo_to_version_template(
            "https://github.com/psf/black-pre-commit-mirror", empty_mappings
        )
        == "${rev}"
    )

    # Test with None (default parameter)
    assert repo_to_package("https://github.com/psf/black-pre-commit-mirror") == "black"
    assert (
        repo_to_version_template("https://github.com/psf/black-pre-commit-mirror")
        == "${rev}"
    )
