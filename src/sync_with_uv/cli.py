"""CLI for sync_with_uv."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from . import __version__
from .sync_with_uv import load_uv_lock, process_precommit_text

app = typer.Typer()


def _version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        print(f"sync-with-uv {__version__}")
        raise typer.Exit(0)


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
    *,
    write_output: Annotated[bool, typer.Option("-w")] = False,
    check: bool = False,
    verbose: Annotated[int, typer.Option("-v", count=True)] = 0,
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
    logger.remove()
    if verbose == 1:
        logger.add(sys.stderr, level="INFO", format="{level}: <level>{message}</level>")
    elif verbose >= 2:
        logger.add(
            sys.stderr, level="DEBUG", format="{level}: <level>{message}</level>"
        )

    uv_data = load_uv_lock(uv_lock_filename)
    precommit_text = precommit_filename.read_text(encoding="utf-8")
    fixed_text = process_precommit_text(precommit_text, uv_data)
    if write_output:
        precommit_filename.write_text(fixed_text, encoding="utf-8")
    else:
        print(fixed_text)
    if check and fixed_text != precommit_text:
        raise typer.Exit(1)
