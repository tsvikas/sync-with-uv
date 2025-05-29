"""sync-with-uv: Sync '.pre-commit-config.yaml' from 'uv.lock'."""

import re
import sys
from pathlib import Path

from loguru import logger

from sync_with_uv.repo_data import repo_to_package, repo_to_version_template

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_uv_lock(filename: Path) -> dict[str, str]:
    """Read 'uv.lock' and return a dict of package, version."""
    with filename.open("rb") as f:
        toml_data = tomllib.load(f)
    return (
        {
            package["name"]: package["version"]
            for package in toml_data["package"]
            if "version" in package
        }
        if "package" in toml_data
        else {}
    )


def process_precommit_text(precommit_text: str, uv_data: dict[str, str]) -> str:
    """Read a pre-commit config file and return a fixed pre-commit config string."""
    # NOTE: this only works if the 'repo' is the first key of the element
    repo_header_re = re.compile(r"\s*-\s*repo\s*:\s*(\S*).*")
    repo_rev_re = re.compile(r"\s*rev\s*:\s*(\S*).*")
    lines = precommit_text.split("\n")
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
            continue  # don't add the line twice
        new_lines.append(line)

    return "\n".join(new_lines)
