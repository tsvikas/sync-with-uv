"""Maps repo urls to package names and version templates."""

from collections import ChainMap
from pathlib import Path
from urllib.parse import urlparse

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
    "https://github.com/adamchainz/djade-pre-commit": "${version}",
    "https://github.com/adrienverge/yamllint": "v${version}",
    "https://github.com/asottile/pyupgrade": "v${version}",
    "https://github.com/astral-sh/ruff-pre-commit": "v${version}",
    "https://github.com/charliermarsh/ruff-pre-commit": "v${version}",
    "https://github.com/codespell-project/codespell": "v${version}",
    "https://github.com/commitizen-tools/commitizen": "v${version}",
    "https://github.com/flakeheaven/flakeheaven": "${version}",
    "https://github.com/hadialqattan/pycln": "v${version}",
    "https://github.com/hhatto/autopep8": "v${version}",
    "https://github.com/pdm-project/pdm": "${version}",
    "https://github.com/pre-commit/mirrors-autopep8": "v${version}",
    "https://github.com/pre-commit/mirrors-clang-format": "v${version}",
    "https://github.com/pre-commit/mirrors-isort": "v${version}",
    "https://github.com/pre-commit/mirrors-mypy": "v${version}",
    "https://github.com/pre-commit/mirrors-pylint": "v${version}",
    "https://github.com/pre-commit/mirrors-yapf": "v${version}",
    "https://github.com/psf/black": "${version}",
    "https://github.com/psf/black-pre-commit-mirror": "${version}",
    "https://github.com/PyCQA/bandit": "${version}",
    "https://github.com/PyCQA/docformatter": "${version}",
    "https://github.com/PyCQA/flake8": "${version}",
    "https://github.com/PyCQA/isort": "${version}",
    "https://github.com/python-jsonschema/check-jsonschema": "${version}",
    "https://github.com/python-poetry/poetry": "${version}",
    "https://github.com/regebro/pyroma": "${version}",
    "https://github.com/rstcheck/rstcheck": "v${version}",
    "https://github.com/rtts/djhtml": "${version}",
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
    if repo_url in {"local", "meta"}:
        return None
    repo_url = repo_url.removesuffix("/")

    # Use ChainMap to prioritize user mappings over built-in ones
    combined_mappings = ChainMap(user_mappings or {}, REPO_TO_PACKAGE)

    # Check the mapping
    try:
        return combined_mappings[repo_url]
    except KeyError:
        pass
    try:
        return combined_mappings[repo_url + "/"]
    except KeyError:
        pass

    # Extract from the url as fallback
    url_parsed = urlparse(repo_url)
    if not url_parsed.netloc:
        return None
    url_last_path = url_parsed.path.split("/")[-1]
    return url_last_path or None


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
