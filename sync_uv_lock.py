# /// script
# requires-python = ">=3.13"
# dependencies = ["typer", "loguru"]
# ///

import re
import tomllib
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

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
    if repo_url == "local":
        return None
    if repo_url in REPO_TO_PACKAGE:
        return REPO_TO_PACKAGE[repo_url]
    for repo in REPO_TO_PACKAGE:
        if repo_url.startswith(repo + "/"):
            return REPO_TO_PACKAGE[repo]
    # find from regex
    repo_url_re = re.compile(
        r"https?://(www\.)?github.com/(?P<user_name>[^/]*)/(?P<repo_name>[^/]*)/?"
    )
    repo_url = repo_url_re.fullmatch(repo_url)
    return repo_url and repo_url.group("repo_name")


def repo_to_version_template(repo_url: str) -> str:
    if repo_url in REPO_TO_VERSION_TEMPLATE:
        return REPO_TO_VERSION_TEMPLATE[repo_url]
    for repo in REPO_TO_VERSION_TEMPLATE:
        if repo_url.startswith(repo + "/"):
            return REPO_TO_VERSION_TEMPLATE[repo]
    return None


def load_uv_lock(filename: Path) -> dict[str, str]:
    with filename.open("rb") as f:
        toml_data = tomllib.load(f)
    return {
        package["name"]: package["version"]
        for package in toml_data["package"]
        if "version" in package
    }


def process_precommit_text(precommit_text: str, uv_data: dict[str, str]) -> str:
    # NOTE: this only works if the 'repo' is the first key of the element
    repo_header_re = re.compile(r"\s*-\s*repo\s*:\s*(\S*)\s*")
    repo_rev_re = re.compile(r"\s*rev\s*:\s*(\S*)\s*")
    lines = precommit_text.splitlines()
    new_lines = []
    repo_url = None
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
    write_output: Annotated[bool, typer.Option("-w")] = False,
) -> str:
    uv_data = load_uv_lock(uv_lock_filename)
    precommit_text = precommit_filename.read_text()
    fixed_text = process_precommit_text(precommit_text, uv_data)
    if write_output:
        precommit_filename.write_text(fixed_text)
    return fixed_text


if __name__ == "__main__":
    app()
