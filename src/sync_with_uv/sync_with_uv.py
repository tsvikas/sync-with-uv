"""sync-with-uv: Sync '.pre-commit-config.yaml' from 'uv.lock'."""

import re
from pathlib import Path

import tomli

from sync_with_uv.repo_data import repo_to_package, repo_to_version_template


def load_uv_lock(filename: Path) -> dict[str, str]:
    """Read 'uv.lock' and return a dict of package, version."""
    with filename.open("rb") as f:
        toml_data = tomli.load(f)
    return (
        {
            package["name"]: package["version"]
            for package in toml_data["package"]
            if "version" in package
        }
        if "package" in toml_data
        else {}
    )


def process_precommit_text(
    precommit_text: str,
    uv_data: dict[str, str],
    user_repo_mappings: dict[str, str] | None = None,
    user_version_mappings: dict[str, str] | None = None,
) -> tuple[str, dict[str, bool | tuple[str, str]]]:
    """Read a pre-commit config file and return a fixed pre-commit config string."""
    # NOTE: this only works if the 'repo' is the first key of the element
    repo_header_re = re.compile(r"\s*-\s*repo\s*:\s*(\S*).*")
    repo_rev_re = re.compile(r"\s*rev\s*:\s*(\S*).*")
    lines = precommit_text.split("\n")
    new_lines = []
    repo_url: str | None = None
    package = None
    changes: dict[str, bool | tuple[str, str]] = {}
    for line in lines:
        if repo_header := repo_header_re.fullmatch(line):
            repo_url = repo_header.group(1)
            package = repo_to_package(repo_url, user_repo_mappings)
            if not package:
                if repo_url != "local":
                    changes[repo_url] = False
            elif package not in uv_data:
                changes[package] = False
        elif (
            package and package in uv_data and (repo_rev := repo_rev_re.fullmatch(line))
        ):
            assert repo_url is not None  # noqa: S101
            current_version = repo_rev.group(1)
            version_template = repo_to_version_template(repo_url, user_version_mappings)
            if version_template is None:
                version_template = "v${rev}" if current_version[0] == "v" else "${rev}"
            target_version = version_template.replace("${rev}", uv_data[package])
            line_fixed = line.replace(current_version, target_version)
            new_lines.append(line_fixed)
            changes[package] = current_version == target_version or (
                current_version,
                target_version,
            )
            continue  # don't add the line twice
        new_lines.append(line)

    return "\n".join(new_lines), changes
