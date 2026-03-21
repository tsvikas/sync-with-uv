"""sync-with-uv: Sync '.pre-commit-config.yaml' or 'prek.toml' from 'uv.lock'."""

import re
from pathlib import Path
from typing import Literal

import tomli

from sync_with_uv.repo_data import repo_to_package, repo_to_version_template


def load_uv_lock(filename: Path) -> dict[str, str]:
    """Load package versions from uv.lock file.

    Args:
        filename: Path to uv.lock file.

    Returns:
        Mapping of package names to their versions.
    """
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


def process_config_text(
    config_text: str,
    uv_data: dict[str, str],
    *,
    config_format: Literal["yaml", "toml"],
    user_repo_mappings: dict[str, str] | None = None,
    user_version_mappings: dict[str, str] | None = None,
) -> tuple[str, dict[str, bool | tuple[str, str]]]:
    """Process config text and sync versions with uv.lock.

    Shared implementation for both .pre-commit-config.yaml and prek.toml.

    Args:
        config_text: Raw config file content.
        uv_data: Package name to version mapping from uv.lock.
        config_format: Either "yaml" for .pre-commit-config.yaml
            or "toml" for prek.toml.
        user_repo_mappings: Optional user repo-to-package mappings.
        user_version_mappings: Optional user repo-to-version-template mappings.

    Returns:
        Tuple of (updated_config_text, changes_dict) where changes_dict maps:
        - package names to True (unchanged), False (not in uv.lock), or
          tuple of (old_version, new_version) when changed
        - repo URLs to False when no package mapping exists
    """
    repo_header_re = {
        "yaml": re.compile(r"^\s*-\s*repo\s*:\s*(?P<repo_url>\S*).*$"),
        "toml": re.compile(r"""^\s*repo\s*=\s*(['"])(?P<repo_url>[^'"]*)\1.*$"""),
    }[config_format]
    repo_rev_re = {
        "yaml": re.compile(r"^\s*rev\s*:\s*(?P<repo_rev>\S*).*$"),
        "toml": re.compile(r"""^\s*rev\s*=\s*(['"])(?P<repo_rev>[^'"]*)\1.*$"""),
    }[config_format]
    skip_repos = {
        "yaml": {"local", "meta"},
        "toml": {"local", "meta", "builtin"},
    }[config_format]
    lines = config_text.splitlines(keepends=True)
    new_lines: list[str] = []
    repo_url: str | None = None
    package: str | None = None
    changes: dict[str, bool | tuple[str, str]] = {}
    for line in lines:
        if repo_header := repo_header_re.match(line):
            repo_url = repo_header.group("repo_url")
            package = repo_to_package(repo_url, user_repo_mappings)
            if not package:
                if repo_url not in skip_repos:
                    changes[repo_url] = False
            elif package not in uv_data:
                changes[package] = False
        elif package and package in uv_data and (repo_rev := repo_rev_re.match(line)):
            assert repo_url is not None  # noqa: S101
            version_template = repo_to_version_template(repo_url, user_version_mappings)
            current_version = repo_rev.group("repo_rev")
            if version_template is None:
                version_template = (
                    "v${version}"
                    if current_version and current_version[0] == "v"
                    else "${version}"
                )
            target_version = version_template.replace("${version}", uv_data[package])
            line_fixed = (
                line[: repo_rev.start("repo_rev")]
                + target_version
                + line[repo_rev.end("repo_rev") :]
            )
            new_lines.append(line_fixed)
            changes[package] = current_version == target_version or (
                current_version,
                target_version,
            )
            continue  # don't add the line twice
        new_lines.append(line)

    return "".join(new_lines), changes
