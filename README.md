# sync-with-uv

[![Tests][tests-badge]][tests-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![uv][uv-badge]][uv-link]
[![Ruff][ruff-badge]][ruff-link]
[![Black][black-badge]][black-link]
\
[![PyPI version][pypi-version-badge]][pypi-link]
[![PyPI platforms][pypi-platforms-badge]][pypi-link]
[![Total downloads][pepy-badge]][pepy-link]
\
[![Made Using tsvikas/python-template][template-badge]][template-link]
[![GitHub Discussion][github-discussions-badge]][github-discussions-link]
[![PRs Welcome][prs-welcome-badge]][prs-welcome-link]

## Overview

Sync '.pre-commit-config.yaml' from 'uv.lock'.

## Usage

### As a pre-commit hook

Add to your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/tsvikas/sync-with-uv
  rev: v0.1.0  # Use the version you want
  hooks:
    - id: sync-with-uv
```

### Command Line

Install the tool using pipx or uv:

```bash
pipx install sync-with-uv
```

And run the tool directly from the command line:

```bash
# Print updated file to stdout
sync-with-uv

# Write changes back to the .pre-commit-config.yaml file
sync-with-uv -w

# Use custom file paths
sync-with-uv -p path/to/.pre-commit-config.yaml -u path/to/uv.lock
```

## Development

### Getting started

- install [git][install-git], [uv][install-uv].
- git clone this repo: `git clone tsvikas/sync-with-uv.git`
- run `uv run just prepare`

### Tests and code quality

- use `uv run just format` to format the code.
- use `uv run just lint` to see linting errors.
- use `uv run just test` to run tests.
- use `uv run just check` to run all the checks (format, lint, test, and pre-commit).
- Run a specific tool directly, with `uv run pytest`/`ruff`/`mypy`/`black`/...

[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/psf/black
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]: https://github.com/tsvikas/sync-with-uv/discussions
[install-git]: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
[install-uv]: https://docs.astral.sh/uv/getting-started/installation/
[pepy-badge]: https://img.shields.io/pepy/dt/sync-with-uv
[pepy-link]: https://pepy.tech/project/sync-with-uv
[prs-welcome-badge]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[prs-welcome-link]: http://makeapullrequest.com
[pypi-link]: https://pypi.org/project/sync-with-uv/
[pypi-platforms-badge]: https://img.shields.io/pypi/pyversions/sync-with-uv
[pypi-version-badge]: https://img.shields.io/pypi/v/sync-with-uv
[rtd-badge]: https://readthedocs.org/projects/sync-with-uv/badge/?version=latest
[rtd-link]: https://sync-with-uv.readthedocs.io/en/latest/?badge=latest
[ruff-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[ruff-link]: https://github.com/astral-sh/ruff
[template-badge]: https://img.shields.io/badge/%F0%9F%9A%80_Made_Using-tsvikas%2Fpython--template-gold
[template-link]: https://github.com/tsvikas/python-template
[tests-badge]: https://github.com/tsvikas/sync-with-uv/actions/workflows/ci.yml/badge.svg
[tests-link]: https://github.com/tsvikas/sync-with-uv/actions/workflows/ci.yml
[uv-badge]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
[uv-link]: https://github.com/astral-sh/uv
