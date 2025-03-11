list-tasks:
  @just --list

# Initialize a new project
init:
  git init
  git commit --allow-empty -m "Initial commit"
  git add --all
  git commit -m "🚀 Initialized project using https://github.com/tsvikas/python-template"
  @just update-deps
  git add --all
  git commit -m "⬆️ Updated project dependencies"
  @just prepare

# Update all dependencies
update-deps:
  uv sync --upgrade
  uv run pre-commit autoupdate -j "$(nproc)"

# Setup the project. Needed after cloning
prepare:
  uv run pre-commit install

check-and-push:
  @just check
  git push

format-and-check:
  @just format
  @just check

# Run all code quality checks and tests, except pylint
check:
  uv run pytest
  uv run mypy
  uv run pre-commit run --all-files --show-diff-on-failure

# Format code and files
format:
  just isort
  uv run black .
  uv run pre-commit run --all-files blacken-docs
  uv run pre-commit run --all-files mdformat

# Sort imports (using ruff)
isort:
  uv run ruff check --select I001 --fix

# Run linters: ruff and mypy
lint:
  uv run ruff check
  uv run mypy

# Run Pylint, might be slow
pylint:
  uv run --with pylint pylint src

# Run tests with pytest
test:
  uv run --exact pytest

# add a new version tag and push it
tag version commit="HEAD": check
  # TODO: check the commit and not the current state.
  git tag -a v{{ version }} -m "Release v{{ version }}" {{ commit }}
  git push --tags
