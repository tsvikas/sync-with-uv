"""sync-with-uv: Sync '.pre-commit-config.yaml' or 'prek.toml' from 'uv.lock'."""

import re
from pathlib import Path
from typing import Literal, NamedTuple

import tomli

from sync_with_uv.repo_data import repo_to_package, repo_to_version_template

# A dependency line is only synced when it carries this pragma comment,
# e.g. ``- pydantic==2.0.0  # sync-with-uv``. The pragma is an explicit,
# per-line opt-in, so the sync is safe regardless of where the line lives.
_DEP_PRAGMA_RE = re.compile(r"#\s*sync-with-uv(?![\w-])")
# A PEP 440 version specifier: one or more comma-separated ``<operator><version>``
# clauses, e.g. ``==2.0.0`` or ``>=1.0,<2.0``.
_DEP_OP = r"(?:===|==|~=|!=|<=|>=|<|>)"
_DEP_VERSION = r"[0-9A-Za-z._*+!-]+"
_DEP_CLAUSE = rf"{_DEP_OP}\s*{_DEP_VERSION}"
_DEP_SPEC = rf"{_DEP_CLAUSE}(?:\s*,\s*{_DEP_CLAUSE})*"
# A dependency item (YAML ``- `` dash or a quote) followed by a PEP 508 name and
# optional extras, with a required version specifier. Matches ``- pydantic==2.0``.
_DEP_LINE_RE = re.compile(
    rf"""^
    (?P<prefix>\s*(?:-\s+['"]?|['"]))
    (?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)
    (?P<extras>\[[^\]]*\])?
    \s*
    (?P<spec>{_DEP_SPEC})
    """,
    re.VERBOSE,
)
# A dependency item with a name but no version specifier, e.g. ``- pydantic`` or
# ``"pydantic",``. The name must be followed (via a zero-width lookahead, so the
# match ends right after the name/extras and marks the insertion point) by a
# bare-dependency terminator (closing quote, comma, marker, comment or end of
# line) and never a ``:``, so structural lines such as ``rev:`` or ``- id: mypy``
# are not matched.
_DEP_BARE_RE = re.compile(
    r"""^
    \s*(?:-\s+['"]?|['"])
    (?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)
    (?P<extras>\[[^\]]*\])?
    (?=\s*(?:['"]|,|;|\#|$))
    """,
    re.VERBOSE,
)
# A second dependency after the first one on the same line: a comma (the first
# dependency's own specifier and extras are already consumed) followed by another
# package name, optionally quoted. Used to reject lines with more than one
# dependency, since only the first would be synced.
_DEP_EXTRA_RE = re.compile(r""",\s*['"]?[A-Za-z0-9]""")


class DepLineChange(NamedTuple):
    """A synced ``# sync-with-uv`` dependency line.

    ``old_spec`` is the original version specifier (``""`` when the dependency
    had none and a pin was added); ``new_spec`` is the applied ``==`` pin. The
    line is unchanged when ``old_spec == new_spec``.
    """

    package: str
    old_spec: str
    new_spec: str


class Changes(NamedTuple):
    """The changes made to a config, split by code path.

    ``repos`` maps a package name to True (rev already correct), False (repo not
    linked to a uv.lock package) or a (old_rev, new_rev) tuple, and a repo URL
    to False when it has no package mapping. ``lines`` maps a 1-based line
    number to the :class:`DepLineChange` applied to that dependency line.
    """

    repos: dict[str, bool | tuple[str, str]]
    lines: dict[int, DepLineChange]


class _DepSyncResult(NamedTuple):
    """A successfully processed pragma dependency line."""

    line: str
    package: str
    old_spec: str
    new_spec: str


def _normalize_package_name(name: str) -> str:
    """Normalize a package name to its PEP 503 form (as used in uv.lock)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _sync_dependency_line(
    line: str, uv_data: dict[str, str]
) -> _DepSyncResult | str | None:
    """Sync a dependency on a ``# sync-with-uv`` line.

    The pragma is a strict, per-line opt-in: an annotated line must be a
    dependency whose package is present in uv.lock. A dependency with a version
    specifier has it replaced with an exact ``==`` pin
    (``pydantic>=2.0`` -> ``pydantic==<locked>``); a bare dependency has a pin
    added (``pydantic`` -> ``pydantic==<locked>``). The package name, extras,
    quoting, environment markers and the comment itself are preserved.

    Args:
        line: A single config line (with its line ending, if any).
        uv_data: Package name to version mapping from uv.lock.

    Only one dependency per pragma line is supported; a line with more than one
    is rejected rather than silently syncing only the first.

    Returns:
        ``None`` if the line does not carry the pragma. A :class:`_DepSyncResult`
        (updated line, package, old specifier, new specifier) when the dependency
        was processed; the old specifier is ``""`` when a pin was added, and the
        line is unchanged when old and new specifiers match. A ``str`` describing
        the problem when the annotated line is invalid (its package is not in
        uv.lock, it has no dependency to sync, or it has more than one); the
        caller collects these and raises.
    """
    pragma = _DEP_PRAGMA_RE.search(line)
    if pragma is None:
        return None
    # Locate the dependency and the span of its version specifier. A specifier is
    # replaced in place; a bare dependency has a pin inserted after its name, so
    # its specifier span is the empty slice at the name's end.
    spec_match = _DEP_LINE_RE.match(line)
    if spec_match is not None:
        name = spec_match.group("name")
        old_spec = spec_match.group("spec")
        spec_start, spec_end = spec_match.start("spec"), spec_match.end("spec")
    else:
        bare_match = _DEP_BARE_RE.match(line)
        if bare_match is None:
            return "no dependency to sync"
        name = bare_match.group("name")
        old_spec = ""
        spec_start = spec_end = bare_match.end()
    if _DEP_EXTRA_RE.search(line, spec_end, pragma.start()):
        return "more than one dependency on the line; use one per line"
    package = _normalize_package_name(name)
    if package not in uv_data:
        return f"{package!r} is not in uv.lock"
    target_spec = f"=={uv_data[package]}"
    line_fixed = line[:spec_start] + target_spec + line[spec_end:]
    return _DepSyncResult(line_fixed, package, old_spec, target_spec)


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


def _repo_header_package(
    repo_url: str,
    uv_data: dict[str, str],
    skip_repos: set[str],
    user_repo_mappings: dict[str, str] | None,
    repo_changes: dict[str, bool | tuple[str, str]],
) -> str | None:
    """Resolve the package linked to a repo header.

    Records unmanaged repos and packages absent from uv.lock in *repo_changes*.

    Returns:
        The package name to sync the repo's ``rev`` against, or ``None`` when
        the repo has no linked package in uv.lock.
    """
    package = repo_to_package(repo_url, user_repo_mappings)
    if not package:
        if repo_url not in skip_repos:
            repo_changes[repo_url] = False
        return None
    if package not in uv_data:
        repo_changes[package] = False
    return package


def process_config_text(
    config_text: str,
    uv_data: dict[str, str],
    *,
    config_format: Literal["yaml", "toml"],
    user_repo_mappings: dict[str, str] | None = None,
    user_version_mappings: dict[str, str] | None = None,
) -> tuple[str, Changes]:
    """Process config text and sync versions with uv.lock.

    Shared implementation for both .pre-commit-config.yaml and prek.toml.

    The ``rev`` field of every repo linked to a uv.lock package is synced.
    In addition, any dependency line (such as an ``additional_dependencies``
    entry) that carries a ``# sync-with-uv`` pragma comment is pinned to the
    exact uv.lock version, adding an ``==`` specifier if the dependency has
    none. The pragma is a strict opt-in: an annotated line must be a dependency
    whose package is in uv.lock, otherwise a :class:`ValueError` is raised.

    Args:
        config_text: Raw config file content.
        uv_data: Package name to version mapping from uv.lock.
        config_format: Either "yaml" for .pre-commit-config.yaml
            or "toml" for prek.toml.
        user_repo_mappings: Optional user repo-to-package mappings.
        user_version_mappings: Optional user repo-to-version-template mappings.

    Returns:
        Tuple of (updated_config_text, changes), where ``changes`` is a
        :class:`Changes` with ``repos`` (per-package ``rev`` results) and
        ``lines`` (per-line-number dependency-pin results). The two code paths
        are kept separate so that a package synced on several dependency lines
        is reported once per line rather than collapsed to a single entry.

    Raises:
        ValueError: If a ``# sync-with-uv`` line has no dependency to sync, or
            its package is not present in uv.lock.
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
    repo_changes: dict[str, bool | tuple[str, str]] = {}
    dep_changes: dict[int, DepLineChange] = {}
    dep_errors: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if repo_header := repo_header_re.match(line):
            repo_url = repo_header.group("repo_url")
            package = _repo_header_package(
                repo_url, uv_data, skip_repos, user_repo_mappings, repo_changes
            )
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
            repo_changes[package] = current_version == target_version or (
                current_version,
                target_version,
            )
            continue  # don't add the line twice
        elif (dep_result := _sync_dependency_line(line, uv_data)) is not None:
            if isinstance(dep_result, str):
                dep_errors.append(f"line {line_number}: {dep_result}")
                new_lines.append(line)
            else:
                dep_changes[line_number] = DepLineChange(
                    dep_result.package, dep_result.old_spec, dep_result.new_spec
                )
                new_lines.append(dep_result.line)
            continue  # don't add the line twice
        new_lines.append(line)

    if dep_errors:
        msg = "invalid '# sync-with-uv' dependencies:\n  " + "\n  ".join(dep_errors)
        raise ValueError(msg)
    return "".join(new_lines), Changes(repo_changes, dep_changes)
