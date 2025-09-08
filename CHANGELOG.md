# Changelog

## Unreleased

## v0.4.0

- Redirect non-diff output to stderr for better CLI experience
- Improve diff color output to match black's color scheme

## v0.3.1

- Add keywords to pyproject.toml for better package discoverability
- Improve README clarity and add CONTRIBUTING.md

## v0.3.0

- Add user-configurable repository mappings via pyproject.toml

## v0.2.1

- Remove Python version constraint from pre-commit hook, and use system Python

## v0.2.0

- Add support for Python 3.10 (previously required Python 3.11+)
- Change CLI flags to mimic Black's interface: `--quiet`, `--verbose`, `--diff`, `--color`, and `--check`
- Add CLI help text
- Add hooks without corresponding package to the "unchanged" report

## v0.1.2

- Fix pre-commit hook not running at all
- Reduce output verbosity by hiding debug messages and timestamps

## v0.1.1

- Fix hook failing on systems with default Python version below 3.11

## v0.1.0

- Initial release with core functionality to sync pre-commit hook versions with uv.lock
