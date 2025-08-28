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

**Recommended: Use as a pre-commit hook**

Simply add these lines to your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/tsvikas/sync-with-uv
  rev: main  # replace with the latest version
  hooks:
    - id: sync-with-uv
```

That's it! The hook will automatically keep your pre-commit versions in sync with `uv.lock`.

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

Most users don't need this section - the tool works out of the box with popular tools like black, ruff, and mypy.

### Custom Repository Mappings

For tools not included in the built-in mapping, you can add custom mappings in your `pyproject.toml`:

```toml
# Map repository URLs to package names
[tool.sync-with-uv.repo-to-package]
"https://github.com/myorg/my-awesome-linter" = "awesome-linter"

# Define custom version templates (optional)
[tool.sync-with-uv.repo-to-version-template]
"https://github.com/myorg/my-awesome-linter" = "ver_${rev}"
```

**Example scenario:**

- Your `.pre-commit-config.yaml` has: `repo: https://github.com/myorg/my-awesome-linter` with `rev: 1.2.0`
- Your `uv.lock` contains: `awesome-linter = "1.5.0"`
- With the mapping above, sync-with-uv will update the pre-commit version to `ver_1.5.0`

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
