"""CLI for sync_with_uv."""

import difflib
import sys
from pathlib import Path
from typing import Annotated

import cyclopts.types
from colorama import Fore, Style
from cyclopts import App, Parameter

from .repo_data import load_user_mappings
from .sync_with_uv import load_uv_lock, process_precommit_text, process_prek_toml_text

app = App(name="sync-with-uv")
app.register_install_completion_command()


def get_colored_diff(diff_lines: list[str]) -> list[str]:
    """Apply ANSI color codes to diff lines.

    Args:
        diff_lines: List of unified diff lines.

    Returns:
        List of diff lines with ANSI color codes applied.
    """
    output_lines = []
    for line in diff_lines:
        if line.startswith(("+++", "---")):
            output_lines.append(Style.BRIGHT + line + Fore.RESET)
        elif line.startswith("+"):
            output_lines.append(Fore.GREEN + line + Fore.RESET)
        elif line.startswith("-"):
            output_lines.append(Fore.RED + line + Fore.RESET)
        elif line.startswith("@@"):
            output_lines.append(Fore.CYAN + line + Fore.RESET)
        else:
            output_lines.append(line)
    return output_lines


_DEFAULT_CONFIGS = (".pre-commit-config.yaml", "prek.toml")
"""Config filenames tried in order when no explicit path is given."""


def _resolve_config(explicit: Path | None) -> Path:
    """Return the config file path to use.

    When *explicit* is ``None``, try each name in :data:`_DEFAULT_CONFIGS`
    in order, returning the first that exists.

    Raises:
        FileNotFoundError: If no config file can be found.
    """
    if explicit is not None:
        resolved = explicit.resolve()
        if not resolved.is_file():
            msg = f'"{explicit}" does not exist.'
            raise FileNotFoundError(msg)
        return resolved
    for name in _DEFAULT_CONFIGS:
        candidate = Path(name)
        if candidate.is_file():
            return candidate.resolve()
    tried = " or ".join(f'"{n}"' for n in _DEFAULT_CONFIGS)
    msg = f"{tried} does not exist."
    raise FileNotFoundError(msg)


@app.default()
def process_precommit(  # noqa: PLR0913
    *,
    precommit_filename: Annotated[
        Path | None, Parameter(["-p", "--pre-commit-config"])
    ] = None,
    uv_lock_filename: Annotated[
        cyclopts.types.ResolvedExistingFile, Parameter(["-u", "--uv-lock"])
    ] = Path("uv.lock"),
    check: Annotated[bool, Parameter(negative="")] = False,
    diff: Annotated[bool, Parameter(negative="")] = False,
    color: bool = False,
    quiet: Annotated[bool, Parameter(alias="-q")] = False,
    verbose: Annotated[bool, Parameter(alias="-v")] = False,
) -> int:
    """Sync pre-commit hook versions with uv.lock.

    Updates the 'rev' fields in .pre-commit-config.yaml or prek.toml to match
    the package versions found in uv.lock, ensuring consistent versions for
    development tools.

    When no config file is specified, tries .pre-commit-config.yaml first,
    then prek.toml.

    Parameters
    ----------
    precommit_filename:
        Path to .pre-commit-config.yaml or prek.toml file to update.
        Auto-detected if not specified.
    uv_lock_filename
        Path to uv.lock file containing package versions
    check
        Don't write the file back, just return the status.
        Return code 0 means nothing would change.
        Return code 1 means some package versions would be updated.
        Return code 123 means there was an internal error.
    diff
        Don't write the file back,
        just output a diff to indicate what changes would be made.
    color
        Enable colored diff output. Only applies when --diff is given.
    quiet
        Stop emitting all non-critical output.
        Error messages will still be emitted.
    verbose
        Show detailed information about all packages,
        including those that were not changed.
    """
    try:
        config_path = _resolve_config(precommit_filename)
        user_repo_mappings, user_version_mappings = load_user_mappings()
        uv_data = load_uv_lock(uv_lock_filename)
        # note that the next line can be simplified in Python>=3.13 using
        # read_text with newline=""
        config_text = config_path.read_bytes().decode(encoding="utf-8")
        process_fn = (
            process_prek_toml_text
            if config_path.suffix == ".toml"
            else process_precommit_text
        )
        fixed_text, changes = process_fn(
            config_text, uv_data, user_repo_mappings, user_version_mappings
        )
        # report the results / change files
        if verbose:
            _print_packages(changes)
        # output a diff to to stdout
        if diff:
            _print_diff(config_text, fixed_text, config_path, color=color)
        # update the file
        if not diff and not check:
            config_path.write_text(fixed_text, encoding="utf-8", newline="")
        # print summary
        if verbose or not quiet:
            _print_summary(changes, dry_mode=diff or check)
        # return 1 if check and changed
        return int(check and fixed_text != config_text)
    except Exception as e:  # noqa: BLE001
        print("Error:", e, file=sys.stderr)
        return 123


def _print_packages(changes: dict[str, bool | tuple[str, str]]) -> None:
    for package, change in changes.items():
        if isinstance(change, tuple):
            print(f"{package}: {change[0]} -> {change[1]}", file=sys.stderr)
        elif change:
            print(f"{package}: unchanged", file=sys.stderr)
        else:
            print(f"{package}: not managed in uv", file=sys.stderr)
    print(file=sys.stderr)


def _print_diff(
    precommit_text: str, fixed_text: str, precommit_filename: Path, *, color: bool
) -> None:
    diff_lines = list(
        difflib.unified_diff(
            precommit_text.splitlines(keepends=True),
            fixed_text.splitlines(keepends=True),
            fromfile=str(precommit_filename),
            tofile=str(precommit_filename),
        )
    )
    if color:
        diff_lines = get_colored_diff(diff_lines)
    print("\n".join(diff_lines))


def _print_summary(
    changes: dict[str, bool | tuple[str, str]], *, dry_mode: bool
) -> None:
    print("All done!", file=sys.stderr)
    n_changed = n_unchanged = 0
    for change in changes.values():
        if isinstance(change, tuple):
            n_changed += 1
        else:
            n_unchanged += 1
    would_be = "would be " if dry_mode else ""
    print(
        f"{n_changed} package {would_be}changed, "
        f"{n_unchanged} packages {would_be}left unchanged.",
        file=sys.stderr,
    )
