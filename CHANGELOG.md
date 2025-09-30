# Changelog

## Unreleased

- **BREAKING CHANGE**:
  Replace `${rev}` with `${version}` in version templates for improved clarity.
  Users with custom version templates in `pyproject.toml` must update their configuration.
- Improve docstrings and CLI help text
- Update README with clearer setup instructions and examples
- Skip repos marked as 'meta' for better compatibility with pre-commit configs
- Support repo URLs from any Git provider (not just GitHub) by using URL parsing instead of regex
- Trigger the hook also on changes of the pyproject.toml file

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
