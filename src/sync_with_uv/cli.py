"""CLI for sync_with_uv."""

import difflib
import sys
from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from .repo_data import load_user_mappings
from .sync_with_uv import load_uv_lock, process_precommit_text

app = typer.Typer()


def get_colored_diff(diff_lines: list[str]) -> list[str]:
    """Apply ANSI color codes to a list of diff lines."""
    output_lines = []
    for line in diff_lines:
        if line.startswith("+"):
            output_lines.append("\033[92m" + line + "\033[0m")  # Green
        elif line.startswith("-"):
            output_lines.append("\033[91m" + line + "\033[0m")  # Red
        elif line.startswith("@@"):
            output_lines.append("\033[96m" + line + "\033[0m")  # Cyan
        else:
            output_lines.append(line)
    return output_lines


def _version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        print(f"sync-with-uv {__version__}")
        raise typer.Exit(0)


@app.command()
def process_precommit(  # noqa: C901, PLR0912, PLR0913
    precommit_filename: Annotated[
        Path,
        typer.Option(
            "-p",
            "--pre-commit-config",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="pre-commit file to update",
        ),
    ] = Path(".pre-commit-config.yaml"),
    uv_lock_filename: Annotated[
        Path,
        typer.Option(
            "-u",
            "--uv-lock",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
            help="lock file to use",
        ),
    ] = Path("uv.lock"),
    *,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Don't write the files back, just return the status. "
            "Return code 0 means nothing would change. "
            "Return code 1 means some files would be reformatted. "
            "Return code 123 means there was an internal error.",
        ),
    ] = False,
    diff: Annotated[
        bool,
        typer.Option(
            "--diff",
            help="Don't write the files back, "
            "just output a diff to indicate what changes would've made.",
        ),
    ] = False,
    color: Annotated[
        bool,
        typer.Option(
            help="Show (or do not show) colored diff. "
            "Only applies when --diff is given."
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "-q",
            "--quiet",
            help="Stop emitting all non-critical output. "
            "Error messages will still be emitted.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Emit messages about files that were not changed "
            "or were ignored due to exclusion patterns.",
        ),
    ] = False,
    version: Annotated[  # noqa: ARG001
        bool | None,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = None,
) -> None:
    """Sync the versions of a pre-commit-config file to a uv.lock file."""
    try:
        user_repo_mappings, user_version_mappings = load_user_mappings()
        uv_data = load_uv_lock(uv_lock_filename)
        precommit_text = precommit_filename.read_text(encoding="utf-8")
        fixed_text, changes = process_precommit_text(
            precommit_text, uv_data, user_repo_mappings, user_version_mappings
        )
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        raise typer.Exit(123) from e
    # report the results / change files
    if verbose:
        for package, change in changes.items():
            if isinstance(change, tuple):
                print(f"{package}: {change[0]} -> {change[1]}")
            elif change:
                print(f"{package}: unchanged")
            else:
                print(f"{package}: not managed in uv")
        print()
    # output a diff to to stdout
    if diff:
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
    # update the file
    if not diff and not check:
        precommit_filename.write_text(fixed_text, encoding="utf-8")
    # print summary
    if verbose or not quiet:
        print("All done!")
        n_changed = n_unchanged = 0
        for change in changes.values():
            if isinstance(change, tuple):
                n_changed += 1
            else:
                n_unchanged += 1
        would_be = "would be " if (diff or check) else ""
        print(
            f"{n_changed} package {would_be}changed, "
            f"{n_unchanged} packages {would_be}left unchanged."
        )
    # return 1 if check and changed
    raise typer.Exit(check and fixed_text != precommit_text)
