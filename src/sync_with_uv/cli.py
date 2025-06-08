"""CLI for sync_with_uv."""

import difflib
import sys
from pathlib import Path
from typing import Annotated

import typer

from . import __version__
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
    check: Annotated[bool, typer.Option("--check")] = False,
    diff: Annotated[bool, typer.Option("--diff")] = False,
    color: bool = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet")] = False,
    verbose: Annotated[bool, typer.Option("-v", "--verbose")] = False,
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
) -> None:
    """Sync the versions of a pre-commit-config file to a uv.lock file."""
    try:
        uv_data = load_uv_lock(uv_lock_filename)
        precommit_text = precommit_filename.read_text(encoding="utf-8")
        fixed_text, changes = process_precommit_text(precommit_text, uv_data)
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
