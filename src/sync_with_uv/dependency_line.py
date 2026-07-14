"""Sync a single ``# sync-with-uv`` dependency line with uv.lock."""

import re
from typing import NamedTuple

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
# A PEP 508 name, shared by the dependency matchers below.
_DEP_NAME = r"[A-Za-z0-9][A-Za-z0-9._-]*"
# A dependency item (YAML ``- `` dash or a quote) followed by a PEP 508 name and
# optional extras, with a required version specifier. Matches ``- pydantic==2.0``.
_DEP_LINE_RE = re.compile(
    rf"""^
    \s*(?:-\s+['"]?|['"])
    (?P<name>{_DEP_NAME})
    (?:\[[^\]]*\])?
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
    rf"""^
    \s*(?:-\s+['"]?|['"])
    (?P<name>{_DEP_NAME})
    (?:\[[^\]]*\])?
    (?=\s*(?:['"]|,|;|\#|$))
    """,
    re.VERBOSE,
)
# The only text allowed between the first dependency's specifier and its pragma
# comment: whitespace, quotes and commas, then an optional ``;`` environment
# marker (which may itself contain anything). Anything else -- another name or a
# second quoted string -- means the line carries more than one dependency, of
# which only the first would be synced.
_DEP_TAIL_RE = re.compile(r"""[\s'",]*(?:;.*)?""")


class DepLineChange(NamedTuple):
    """A synced ``# sync-with-uv`` dependency line.

    ``old_spec`` is the original version specifier (``""`` when the dependency
    had none and a pin was added); ``new_spec`` is the applied ``==`` pin.
    """

    package: str
    old_spec: str
    new_spec: str

    @property
    def changed(self) -> bool:
        """Whether the applied pin differs from the original specifier."""
        return self.old_spec != self.new_spec


def _normalize_package_name(name: str) -> str:
    """Normalize a package name to its PEP 503 form (as used in uv.lock)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def sync_dependency_line(
    line: str, uv_data: dict[str, str]
) -> tuple[str, DepLineChange] | str | None:
    """Sync a dependency on a ``# sync-with-uv`` line.

    The pragma is a strict, per-line opt-in: an annotated line must be a
    dependency whose package is present in uv.lock. A dependency with a version
    specifier has it replaced with an exact ``==`` pin
    (``pydantic>=2.0`` -> ``pydantic==<locked>``); a bare dependency has a pin
    added (``pydantic`` -> ``pydantic==<locked>``). The package name, extras,
    quoting, environment markers and the comment itself are preserved.

    Only one dependency per pragma line is supported; a line with more than one
    is rejected rather than silently syncing only the first.

    Args:
        line: A single config line (with its line ending, if any).
        uv_data: Package name to version mapping from uv.lock.

    Returns:
        ``None`` if the line does not carry the pragma. A tuple of (updated line,
        :class:`DepLineChange`) when the dependency was processed. A ``str``
        describing the problem when the annotated line is invalid (its package is
        not in uv.lock, it has no dependency to sync, or it has more than one);
        the caller collects these and raises.
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
    if not _DEP_TAIL_RE.fullmatch(line, spec_end, pragma.start()):
        return "more than one dependency on the line; use one per line"
    package = _normalize_package_name(name)
    if package not in uv_data:
        return f"{package!r} is not in uv.lock"
    target_spec = f"=={uv_data[package]}"
    line_fixed = line[:spec_start] + target_spec + line[spec_end:]
    return line_fixed, DepLineChange(package, old_spec, target_spec)
