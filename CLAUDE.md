# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run CLI: `uv run sync-with-uv` or `uv run python -m sync_with_uv`
- Run with options: `uv run sync-with-uv -p custom-precommit.yaml -u custom-lock.toml --diff`
- Format code: `just format` (runs black and ruff-isort)
- Lint: `just lint` (runs ruff-check and mypy)
- Run tests: `just test` or `uv run pytest`
- Run single test: `uv run pytest tests/test_cli.py::test_function_name -v`
- Type check: `uv run mypy`
- Full check: `just check` (runs tests, mypy, and all pre-commit hooks)

## Code Style Guidelines

- **Imports**: Standard library first, then third-party, then local (enforced by ruff)
- **Type Hints**: Strict mypy typing with complete type coverage (e.g., `dict[str, str]`, `str | None`)
- **Formatting**: Black formatting style with ruff for additional formatting
- **Naming**: Snake case for variables/functions, PascalCase for classes/types
- **Error Handling**: Use standard exceptions; CLI module uses typer.Exit for error codes
- **CLI**: Use typer for command-line interfaces with type annotations
- **Docstrings**: Google-style conventions (enforced by ruff)

## Architecture

This tool synchronizes pre-commit hook versions with those in uv.lock to ensure consistent dependency versions.

### Core Components

- **cli.py**: Typer-based CLI interface with diff/check/write modes
- **sync_with_uv.py**: Core logic for parsing uv.lock and updating pre-commit configs
- **repo_data.py**: Mapping tables for GitHub repo URLs to package names and version templates

### Key Functions

- `load_uv_lock()`: Parses uv.lock TOML and extracts package versions
- `process_precommit_text()`: Regex-based parsing and updating of .pre-commit-config.yaml
- `repo_to_package()`: Maps GitHub URLs to Python package names
- `repo_to_version_template()`: Handles version prefix patterns (v-prefixed vs plain versions)
