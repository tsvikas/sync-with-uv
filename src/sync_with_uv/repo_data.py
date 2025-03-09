"""Maps repo urls to package names and version templates."""

import re

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


def repo_to_package(repo_url: str) -> str | None:
    """Convert a repo url to a python package name."""
    if repo_url == "local":
        return None
    if repo_url in REPO_TO_PACKAGE:
        return REPO_TO_PACKAGE[repo_url]
    for repo, package in REPO_TO_PACKAGE.items():
        if repo_url.startswith(repo + "/"):
            return package
    # find from regex
    repo_url_re = re.compile(
        r"https?://(www\.)?github.com/(?P<user_name>[^/]*)/(?P<repo_name>[^/]*)/?"
    )
    repo_url_match = repo_url_re.fullmatch(repo_url)
    if repo_url_match is None:
        return None
    repo_name: str = repo_url_match.group("repo_name")
    return repo_name


def repo_to_version_template(repo_url: str) -> str | None:
    """Convert a repo url to a evrsion template."""
    if repo_url in REPO_TO_VERSION_TEMPLATE:
        return REPO_TO_VERSION_TEMPLATE[repo_url]
    for repo, version_template in REPO_TO_VERSION_TEMPLATE.items():
        if repo_url.startswith(repo + "/"):
            return version_template
    return None
