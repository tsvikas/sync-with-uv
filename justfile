list-tasks:
  @just --list

alias t := test
alias c := check
alias cp := check-and-push
alias fc := format-and-check
alias f := format

# Initialize a new project
init:
  git init
  git commit --allow-empty -m "Initial commit"
  git add --all
  git commit -m "🚀 Initialized project using https://github.com/tsvikas/python-template"
  just update-deps
  git add --all
  [ -z "$(git status --porcelain)" ] || git commit -m "⬆️ Updated project dependencies"
  just prepare

# Update all dependencies
update-deps:
  uv sync --upgrade
  uv run pre-commit autoupdate -j "$( (uname -s | grep -q Linux && nproc) || (uname -s | grep -q Darwin && sysctl -n hw.ncpu) || echo 1 )"
  uvx sync-with-uv
  uv run pre-commit run -a sync-pre-commit-deps

# Setup the project. Needed after cloning
prepare:
  uv run pre-commit install

check-and-push:
  [ -z "$(git status --porcelain)" ]
  just check
  git push --follow-tags

format-and-check:
  just format
  just check

# Run all code quality checks and tests, except pylint
check:
  just test
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

# add a new version tag
tag version commit="HEAD": (_assert-legal-version version)
  just check-at-commit {{ commit }}
  just tag-skip-check {{ version }} {{ commit }}

_assert-legal-version version:
  @echo "{{ version }}" | grep -q '^[0-9]' || ( echo "Error: version name should start with a digit" && false )

tmp_rc_dir := '/tmp/rc/' + file_name(justfile_directory()) + '/' + datetime('%s')

check-at-commit commit:
  git worktree add {{ tmp_rc_dir }} --detach {{ commit }}
  just -f {{ tmp_rc_dir }}/justfile check || ( git worktree remove -f {{ tmp_rc_dir }} && false )
  git worktree remove {{ tmp_rc_dir }}

tag-skip-check version commit: (_assert-legal-version version)
  git tag -a v{{ version }} -m "Release v{{ version }}" {{ commit }}
