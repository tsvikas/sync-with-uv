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


def _fix_rev_line(
    line: str,
    repo_rev: re.Match[str],
    *,
    uv_version: str,
    config_format: Literal["yaml", "toml"],
    version_template: str | None,
) -> tuple[str, str, str]:
    """Extract version from a rev match and build the fixed line.

    Returns:
        Tuple of (fixed_line, current_version, target_version).
    """
    if config_format == "toml":
        quote_char = repo_rev.group(1)
        current_version = repo_rev.group(2)
    else:
        current_version = repo_rev.group(1)
    if version_template is None:
        version_template = "v${version}" if current_version[0] == "v" else "${version}"
    target_version = version_template.replace("${version}", uv_version)
    if config_format == "toml":
        line_fixed = line.replace(
            f"{quote_char}{current_version}{quote_char}",
            f"{quote_char}{target_version}{quote_char}",
        )
    else:
        line_fixed = line.replace(current_version, target_version)
    return line_fixed, current_version, target_version


def _process_config_text(
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
    if config_format == "yaml":
        # NOTE: this only works if the 'repo' is the first key of the element
        repo_header_re = re.compile(r"^\s*-\s*repo\s*:\s*(\S*).*$")
        repo_rev_re = re.compile(r"^\s*rev\s*:\s*(\S*).*$")
        skip_repos = {"local", "meta"}
    else:
        repo_header_re = re.compile(r"""^\s*repo\s*=\s*(['"])([^'"]*)\1.*$""")
        repo_rev_re = re.compile(r"""^\s*rev\s*=\s*(['"])([^'"]*)\1.*$""")
        skip_repos = {"local", "meta", "builtin"}

    lines = config_text.splitlines(keepends=True)
    new_lines: list[str] = []
    repo_url: str | None = None
    package: str | None = None
    changes: dict[str, bool | tuple[str, str]] = {}
    for line in lines:
        if repo_header := repo_header_re.match(line):
            repo_url = repo_header.group(2 if config_format == "toml" else 1)
            package = repo_to_package(repo_url, user_repo_mappings)
            if not package:
                if repo_url not in skip_repos:
                    changes[repo_url] = False
            elif package not in uv_data:
                changes[package] = False
        elif package and package in uv_data and (repo_rev := repo_rev_re.match(line)):
            assert repo_url is not None  # noqa: S101
            version_template = repo_to_version_template(repo_url, user_version_mappings)
            line_fixed, current_version, target_version = _fix_rev_line(
                line,
                repo_rev,
                uv_version=uv_data[package],
                config_format=config_format,
                version_template=version_template,
            )
            new_lines.append(line_fixed)
            changes[package] = current_version == target_version or (
                current_version,
                target_version,
            )
            continue  # don't add the line twice
        new_lines.append(line)

    return "".join(new_lines), changes


def process_precommit_text(
    precommit_text: str,
    uv_data: dict[str, str],
    user_repo_mappings: dict[str, str] | None = None,
    user_version_mappings: dict[str, str] | None = None,
) -> tuple[str, dict[str, bool | tuple[str, str]]]:
    """Process pre-commit config text and sync versions with uv.lock.

    Parses pre-commit config YAML text and updates repository revision
    tags to match versions from uv.lock file.

    Args:
        precommit_text: Raw pre-commit config file content.
        uv_data: Package name to version mapping from uv.lock.
        user_repo_mappings: Optional user repo-to-package mappings.
        user_version_mappings: Optional user repo-to-version-template mappings.

    Returns:
        Tuple of (updated_config_text, changes_dict) where changes_dict maps:
        - package names to True (unchanged), False (not in uv.lock), or
          tuple of (old_version, new_version) when changed
        - repo URLs to False when no package mapping exists
    """
    return _process_config_text(
        precommit_text,
        uv_data,
        config_format="yaml",
        user_repo_mappings=user_repo_mappings,
        user_version_mappings=user_version_mappings,
    )


def process_prek_toml_text(
    prek_text: str,
    uv_data: dict[str, str],
    user_repo_mappings: dict[str, str] | None = None,
    user_version_mappings: dict[str, str] | None = None,
) -> tuple[str, dict[str, bool | tuple[str, str]]]:
    """Process prek.toml config text and sync versions with uv.lock.

    Parses prek.toml text and updates repository revision values to match
    versions from uv.lock file. Uses regex-based line-by-line processing
    to preserve formatting and comments, consistent with the YAML approach.

    Args:
        prek_text: Raw prek.toml file content.
        uv_data: Package name to version mapping from uv.lock.
        user_repo_mappings: Optional user repo-to-package mappings.
        user_version_mappings: Optional user repo-to-version-template mappings.

    Returns:
        Tuple of (updated_config_text, changes_dict) where changes_dict maps:
        - package names to True (unchanged), False (not in uv.lock), or
          tuple of (old_version, new_version) when changed
        - repo URLs to False when no package mapping exists
    """
    return _process_config_text(
        prek_text,
        uv_data,
        config_format="toml",
        user_repo_mappings=user_repo_mappings,
        user_version_mappings=user_version_mappings,
    )
