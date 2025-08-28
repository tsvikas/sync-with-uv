"""Maps repo urls to package names and version templates."""

import re
from collections import ChainMap
from pathlib import Path

import tomli

REPO_TO_PACKAGE = {
    "https://github.com/adamchainz/djade-pre-commit": "djade",
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/charliermarsh/ruff-pre-commit": "ruff",
    "https://github.com/pre-commit/mirrors-autopep8": "autopep8",
    "https://github.com/pre-commit/mirrors-clang-format": "clang-format",
    "https://github.com/pre-commit/mirrors-isort": "isort",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
    "https://github.com/pre-commit/mirrors-pylint": "pylint",
    "https://github.com/pre-commit/mirrors-yapf": "yapf",
    "https://github.com/psf/black-pre-commit-mirror": "black",
}
REPO_TO_VERSION_TEMPLATE = {
    "https://github.com/adamchainz/djade-pre-commit": "${rev}",
    "https://github.com/adrienverge/yamllint": "v${rev}",
    "https://github.com/asottile/pyupgrade": "v${rev}",
    "https://github.com/astral-sh/ruff-pre-commit": "v${rev}",
    "https://github.com/charliermarsh/ruff-pre-commit": "v${rev}",
    "https://github.com/codespell-project/codespell": "v${rev}",
    "https://github.com/commitizen-tools/commitizen": "v${rev}",
    "https://github.com/flakeheaven/flakeheaven": "${rev}",
    "https://github.com/hadialqattan/pycln": "v${rev}",
    "https://github.com/hhatto/autopep8": "v${rev}",
    "https://github.com/pdm-project/pdm": "${rev}",
    "https://github.com/pre-commit/mirrors-autopep8": "v${rev}",
    "https://github.com/pre-commit/mirrors-clang-format": "v${rev}",
    "https://github.com/pre-commit/mirrors-isort": "v${rev}",
    "https://github.com/pre-commit/mirrors-mypy": "v${rev}",
    "https://github.com/pre-commit/mirrors-pylint": "v${rev}",
    "https://github.com/pre-commit/mirrors-yapf": "v${rev}",
    "https://github.com/psf/black": "${rev}",
    "https://github.com/psf/black-pre-commit-mirror": "${rev}",
    "https://github.com/PyCQA/bandit": "${rev}",
    "https://github.com/PyCQA/docformatter": "${rev}",
    "https://github.com/PyCQA/flake8": "${rev}",
    "https://github.com/PyCQA/isort": "${rev}",
    "https://github.com/python-jsonschema/check-jsonschema": "${rev}",
    "https://github.com/python-poetry/poetry": "${rev}",
    "https://github.com/regebro/pyroma": "${rev}",
    "https://github.com/rstcheck/rstcheck": "v${rev}",
    "https://github.com/rtts/djhtml": "${rev}",
}


def load_user_mappings(
    pyproject_path: Path | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Load user-defined mappings from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml file. If None, looks for it in cwd.

    Returns:
        Tuple of (repo_to_package, repo_to_version_template) user mappings.
    """
    if pyproject_path is None:
        pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        return {}, {}

    with pyproject_path.open("rb") as f:
        toml_data = tomli.load(f)

    tool_config = toml_data.get("tool", {}).get("sync-with-uv", {})
    user_repo_to_package = tool_config.get("repo-to-package", {})
    user_repo_to_version_template = tool_config.get("repo-to-version-template", {})

    return user_repo_to_package, user_repo_to_version_template


def repo_to_package(
    repo_url: str, user_mappings: dict[str, str] | None = None
) -> str | None:
    """Convert a repo url to a python package name.

    Args:
        repo_url: The repository URL to lookup.
        user_mappings: Optional user-defined repo-to-package mappings.

    Returns:
        The package name, or None if no mapping is found.
    """
    if repo_url == "local":
        return None

    # Use ChainMap to prioritize user mappings over built-in ones
    combined_mappings = ChainMap(user_mappings or {}, REPO_TO_PACKAGE)

    # Check exact match first
    if repo_url in combined_mappings:
        return combined_mappings[repo_url]

    # Check prefix matches (for repos with sub-paths)
    for repo, package in combined_mappings.items():
        if repo_url.startswith(repo + "/"):
            return package

    # Extract from regex as fallback
    repo_url_re = re.compile(
        r"https?://(www\.)?github.com/(?P<user_name>[^/]*)/(?P<repo_name>[^/]*)/?"
    )
    repo_url_match = repo_url_re.fullmatch(repo_url)
    return repo_url_match.group("repo_name") if repo_url_match else None


def repo_to_version_template(
    repo_url: str, user_mappings: dict[str, str] | None = None
) -> str | None:
    """Convert a repo url to a version template.

    Args:
        repo_url: The repository URL to lookup.
        user_mappings: Optional user-defined repo-to-version-template mappings.

    Returns:
        The version template, or None if no mapping is found.
    """
    # Use ChainMap to prioritize user mappings over built-in ones
    combined_mappings = ChainMap(user_mappings or {}, REPO_TO_VERSION_TEMPLATE)

    # Check exact match first
    if repo_url in combined_mappings:
        return combined_mappings[repo_url]

    # Check prefix matches (for repos with sub-paths)
    for repo, version_template in combined_mappings.items():
        if repo_url.startswith(repo + "/"):
            return version_template

    return None
