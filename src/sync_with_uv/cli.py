"""CLI for sync_with_uv."""

import re
import tomllib
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from . import __version__

app = typer.Typer()


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


def load_uv_lock(filename: Path) -> dict[str, str]:
    """Read 'uv.lock' and return a dict of package, version."""
    with filename.open("rb") as f:
        toml_data = tomllib.load(f)
    return {
        package["name"]: package["version"]
        for package in toml_data["package"]
        if "version" in package
    }


def process_precommit_text(precommit_text: str, uv_data: dict[str, str]) -> str:
    """Read a pre-commit config file and return a fixed pre-commit config string."""
    # NOTE: this only works if the 'repo' is the first key of the element
    repo_header_re = re.compile(r"\s*-\s*repo\s*:\s*(\S*)\s*")
    repo_rev_re = re.compile(r"\s*rev\s*:\s*(\S*)\s*")
    lines = precommit_text.splitlines()
    new_lines = []
    repo_url: str | None = None
    package = None
    for line in lines:
        if repo_header := repo_header_re.fullmatch(line):
            repo_url = repo_header.group(1)
            package = repo_to_package(repo_url)
            logger.debug(
                "Processing {package} ({repo_url})", package=package, repo_url=repo_url
            )
            if not (package and package in uv_data):
                logger.debug("{}: NOT MANAGED", package)
        elif (
            package and package in uv_data and (repo_rev := repo_rev_re.fullmatch(line))
        ):
            assert repo_url is not None  # noqa: S101
            current_version = repo_rev.group(1)
            version_template = repo_to_version_template(repo_url)
            if version_template is None:
                version_template = "v${rev}" if current_version[0] == "v" else "${rev}"
            target_version = version_template.replace("${rev}", uv_data[package])
            line_fixed = line.replace(current_version, target_version)
            new_lines.append(line_fixed)
            if line == line_fixed:
                logger.debug("{}: NO CHANGE", package)
            else:
                logger.info(
                    "{package}: {current_version} -> {target_version}",
                    current_version=current_version,
                    target_version=target_version,
                    package=package,
                )
            continue
        new_lines.append(line)

    return "\n".join(new_lines)


ExistingFile = Annotated[
    Path,
    typer.Option(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
]


def _version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        print(f"sync-with-uv {__version__}")
        raise typer.Exit(0)


@app.command()
def process_precommit(
    precommit_filename: Annotated[
        Path,
        typer.Option(
            "-p",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = Path(".pre-commit-config.yaml"),
    uv_lock_filename: Annotated[
        Path,
        typer.Option(
            "-u",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = Path("uv.lock"),
    *,
    write_output: Annotated[bool, typer.Option("-w")] = False,
    version: Annotated[  # noqa: ARG001
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Print version",
        ),
    ] = None,
) -> str:
    """Sync the versions of a pre-commit-config file to a uv.lock file."""
    uv_data = load_uv_lock(uv_lock_filename)
    precommit_text = precommit_filename.read_text()
    fixed_text = process_precommit_text(precommit_text, uv_data)
    if write_output:
        precommit_filename.write_text(fixed_text)
    return fixed_text
