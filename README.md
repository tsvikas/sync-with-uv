# sync-with-uv

[![Tests][tests-badge]][tests-link]
[![uv][uv-badge]][uv-link]
[![Ruff][ruff-badge]][ruff-link]
[![Black][black-badge]][black-link]
[![codecov][codecov-badge]][codecov-link]
\
[![PyPI version][pypi-version-badge]][pypi-link]
[![PyPI platforms][pypi-platforms-badge]][pypi-link]
[![Total downloads][pepy-badge]][pepy-link]
\
[![Made Using tsvikas/python-template][template-badge]][template-link]
[![GitHub Discussion][github-discussions-badge]][github-discussions-link]
[![PRs Welcome][prs-welcome-badge]][prs-welcome-link]

## Overview

[PEP 735](https://peps.python.org/pep-0735/) introduces dependency groups in `pyproject.toml`,
allowing tools like black, ruff, and mypy to be managed centrally.
However, when these tools are also used in pre-commit hooks,
keeping versions in sync between `uv.lock` and `.pre-commit-config.yaml` can be tedious.

This package automatically updates the versions of dependencies in `.pre-commit-config.yaml` to match their versions in `uv.lock`,
ensuring everything stays aligned and is managed from a single source.
Any tool not specified in `uv.lock` remains managed by `.pre-commit-config.yaml`.

Simply add this pre-commit hook to your setup and enjoy consistent dependency management.

## Usage

### Recommended: Use as a pre-commit hook

Simply add these lines to your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/tsvikas/sync-with-uv
  rev: main  # replace with the latest version
  hooks:
    - id: sync-with-uv
```

**Note:** Place this hook **after** hooks that modify `uv.lock` (like `uv-lock`), and **before** hooks that read versions from `.pre-commit-config.yaml` (like `sync-pre-commit-deps`).

That's it! The hook will automatically sync versions for any tools present in both your pre-commit config and `uv.lock`.

To add a tool to your uv dependencies, use `uv add --group dev tool-name` (the tool must be available on PyPI).

### Alternative: Command Line Interface

For manual usage or CI/CD integration, install and run directly:

```bash
pipx install sync-with-uv

# Update .pre-commit-config.yaml
sync-with-uv

# Preview changes only
sync-with-uv --diff

# Custom file paths
sync-with-uv -p custom-precommit.yaml -u custom-lock.toml
```

## Advanced Configuration

Most users don't need this section -
the tool works out of the box with popular tools like black, ruff, and mypy,
as well as commonly used mirrors for those tools.

### Mapping from repo URL to package name

By default, the tool assumes the last part of a repo URL is the package name.
For example, if `repo: https://github.com/my-org/my-awesome-linter` is in `.pre-commit-config.yaml`,
the tool will sync with the version of `my-awesome-linter` in `uv.lock`.

The tool skips any repo without a corresponding package in `uv.lock`.

To link a repo to a different package name,
add an entry to the `[tool.sync-with-uv.repo-to-package]` section in `pyproject.toml`.

Use an empty value to disable syncing for a specific repo.

```toml
[tool.sync-with-uv.repo-to-package]
# sync this repo with the `awesome-linter` package
"https://github.com/my-org/my-awesome-linter" = "awesome-linter"
# do not sync this repo, even if `cool-tool` is in `uv.lock`
"https://github.com/my-org/cool-tool" = ""
```

### Mapping from repo URL to version tag format

For each repo in `.pre-commit-config.yaml` with a linked package,
the tool updates the `rev` field with the version from `uv.lock`, optionally preserving a leading `v`.
The tool preserves the original formatting and any comments on the `rev` line.
For example, if the `uv.lock` version is `1.2.3`,
it will update `rev: 1.0.0` to `rev: 1.2.3`,
and `rev: v1.0.0` to `rev: v1.2.3`.

To use a custom format for the `rev` field,
add an entry to the `[tool.sync-with-uv.repo-to-version-template]` section in `pyproject.toml`,
using `${version}` as a placeholder for the package version.

```toml
[tool.sync-with-uv.repo-to-version-template]
# for example, this project uses `version_1.2.3` format for tags
"https://github.com/my-org/my-awesome-linter" = "version_${version}"
```

## Contributing

Interested in contributing?
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guideline.

[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/psf/black
[codecov-badge]: https://codecov.io/gh/tsvikas/sync-with-uv/graph/badge.svg
[codecov-link]: https://codecov.io/gh/tsvikas/sync-with-uv
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]: https://github.com/tsvikas/sync-with-uv/discussions
[pepy-badge]: https://img.shields.io/pepy/dt/sync-with-uv
[pepy-link]: https://pepy.tech/project/sync-with-uv
[prs-welcome-badge]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[prs-welcome-link]: https://opensource.guide/how-to-contribute/
[pypi-link]: https://pypi.org/project/sync-with-uv/
[pypi-platforms-badge]: https://img.shields.io/pypi/pyversions/sync-with-uv
[pypi-version-badge]: https://img.shields.io/pypi/v/sync-with-uv
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff-link]: https://github.com/astral-sh/ruff
[template-badge]: https://img.shields.io/badge/%F0%9F%9A%80_Made_Using-tsvikas%2Fpython--template-gold
[template-link]: https://github.com/tsvikas/python-template
[tests-badge]: https://github.com/tsvikas/sync-with-uv/actions/workflows/ci.yml/badge.svg
[tests-link]: https://github.com/tsvikas/sync-with-uv/actions/workflows/ci.yml
[uv-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
[uv-link]: https://github.com/astral-sh/uv
