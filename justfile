list-tasks:
  @just --list

alias f := format
alias t := test
alias l := lint
alias q := quick-tools


### run once after init/clone ###

# Initialize a new project
init: && prepare
  git init
  git commit --allow-empty -m "Initial commit"
  git add --all
  git commit -m "🚀 Initialized project using https://github.com/tsvikas/python-template"
  just deps-update
  git add --all
  [ -z "$(git status --porcelain)" ] || git commit -m "⬆️ Updated project dependencies"

# Setup the project after cloning
prepare:
  uv run pre-commit install --install-hooks


### dependencies ###

# List outdated python dependencies
deps-list-outdated:
  uv tree --outdated --depth 1 --color always -q  | { grep latest --color=never || exit 0; }

# Update all dependencies
deps-update: && deps-list-outdated
  uv sync --upgrade
  uv run -- \
    pre-commit autoupdate -j \
    "$( (uname -s | grep -q Linux && nproc) || (uname -s | grep -q Darwin && sysctl -n hw.ncpu) || echo 1 )" \
    | grep -v 'appears to be a mutable reference'
  uvx sync-with-uv
  uvx sync-pre-commit-deps --yaml-mapping 2 --yaml-sequence 4 --yaml-offset 2 .pre-commit-config.yaml || { \
    echo "Note: '.pre-commit-config.yaml' changed, and might lost its formatting." \
    && exit 1; \
  }

# Audit dependencies
deps-audit:
  uv run --exact --all-extras --all-groups --with pip-audit -- \
    pip-audit \
    --skip-editable
  uv run --exact true


### code quality ###
_assert_clean_repo:
  [ -z "$(git status --porcelain)" ]

# Tests to run before push, tag, or release
_check: _assert_clean_repo test lint

# Check the code, and push if it pass
check-and-push: _check
  git push --follow-tags

# Run fast formatting and linting tools
quick-tools:
  uv run ruff check --select I001 --fix -q
  uv run black -q .
  uv run ruff check

# Format code and files
format:
  uv run ruff check --select I001 --fix
  uv run black .
  uv run pre-commit run --all-files blacken-docs
  uv run pre-commit run --all-files mdformat

# Run linters
lint:
  uv run ruff check
  uv run --exact --all-extras --no-default-groups --group typing --group test -- dmypy run
  uv run --exact --all-extras --all-groups --with deptry -- deptry src/
  uv run --exact pre-commit run --all-files

# Run Pylint (slow, not used in other tasks)
pylint:
  uv run --exact --with pylint -- pylint src
  uv run --exact true

# Run tests with pytest
test:
  uv run --exact --all-extras --no-default-groups --group test \
    --reinstall-package sync_with_uv -- pytest
  uv run --exact true

# Run tests with pytest, using resolution lowest-direct
test-lowest python:
  mv uv.lock uv.lock.1
  uv sync --exact --all-extras --no-default-groups --group test \
    --upgrade --resolution lowest-direct --python {{python}} \
    --reinstall-package sync_with_uv
  mv uv.lock.1 uv.lock
  uv run --no-sync pytest
  uv run --exact true


### Release, tags, previous commits ###

# Create a release commit
release version: (_assert-legal-version version) _check
  sed -i "s/## Unreleased/## Unreleased\n\n## v{{version}}/" CHANGELOG.md
  git add CHANGELOG.md
  git commit -m "🔖 Release v{{version}}"
  just _tag-skip-check {{version}} HEAD

# Add a new version tag at a specific commit
tag-version-at-commit version commit: (_assert-legal-version version)
  just check-at-commit {{commit}}
  just _tag-skip-check {{version}} {{commit}}

version_regex := '^([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?$'

_assert-legal-version version:
  @echo "{{version}}" | grep -qE '{{version_regex}}' || ( echo "Error: not a legal version" && false )

tmp_rc_dir := '/tmp/rc/' + file_name(justfile_directory()) + '/' + datetime('%s')

# Run code checks at a specific commit
check-at-commit commit:
  git worktree add {{tmp_rc_dir}} --detach {{commit}}
  just -f {{tmp_rc_dir}}/justfile _check || ( git worktree remove -f {{tmp_rc_dir}} && false )
  git worktree remove {{tmp_rc_dir}}

_tag-skip-check version commit: (_assert-legal-version version)
  git tag -a v{{version}} -m "Release v{{version}}" {{commit}}


### Documentation ###

# Generate reference pages from docstrings
build-docs-ref:
  rm -rf docs/reference
  uv run --exact --python 3.14 --only-group docs -- \
    scripts/gen_ref_pages.py
  uv run --exact true

# Build the documentation
build-docs: build-docs-ref
  uv run --exact --python 3.14 --only-group docs -- \
    mkdocs build
  uv run --exact true

# Serve the documentation locally
serve-docs: build-docs-ref
  uv run --exact --python 3.14 --only-group docs -- \
    mkdocs serve
  uv run --exact true

# Print the help of the CLI command
print-cli-help:
  uv run sync-with-uv --help
