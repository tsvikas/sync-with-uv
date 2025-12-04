# Changelog

## [Unreleased]

## [0.5.0] - 2025-11-18

### Breaking Changes

- **Version template variable renamed**:
  Custom version templates in `pyproject.toml` must use `${version}` instead of `${rev}`.

### New Features

- **Auto-sync on config changes**:
  The pre-commit hook now also runs when you modify `pyproject.toml`.
- **Support syncing for more tools**:
  Sync hooks from any Git provider, not just GitHub

### Improvements

- Better CLI help
- README now includes step-by-step setup and practical examples

### Bug Fixes

- Handle permission errors gracefully
- Preserve original line endings on Windows (#24)
- Skip `repo: meta` entries in pre-commit configs

## [0.4.0] - 2025-09-08

- Redirect non-diff output to stderr for better CLI experience
- Improve diff color output to match black's color scheme

## [0.3.1] - 2025-08-31

- Add keywords to pyproject.toml for better package discoverability
- Improve README clarity and add CONTRIBUTING.md

## [0.3.0] - 2025-08-28

- Add user-configurable repository mappings via pyproject.toml

## [0.2.1] - 2025-08-07

- Remove Python version constraint from pre-commit hook, and use system Python

## [0.2.0] - 2025-06-17

- Add support for Python 3.10 (previously required Python 3.11+)
- Change CLI flags to mimic Black's interface: `--quiet`, `--verbose`, `--diff`, `--color`, and `--check`
- Add CLI help text
- Add hooks without corresponding package to the "unchanged" report

## [0.1.2] - 2025-05-26

- Fix pre-commit hook not running at all
- Reduce output verbosity by hiding debug messages and timestamps

## [0.1.1] - 2025-05-26

- Fix hook failing on systems with default Python version below 3.11

## [0.1.0] - 2025-03-12

- Initial release with core functionality to sync pre-commit hook versions with uv.lock

[0.1.0]: https://github.com/tsvikas/sync-with-uv/releases/tag/v0.1.0
[0.1.1]: https://github.com/tsvikas/sync-with-uv/compare/v0.1.0...v0.1.1
[0.1.2]: https://github.com/tsvikas/sync-with-uv/compare/v0.1.1...v0.1.2
[0.2.0]: https://github.com/tsvikas/sync-with-uv/compare/v0.1.2...v0.2.0
[0.2.1]: https://github.com/tsvikas/sync-with-uv/compare/v0.2.0...v0.2.1
[0.3.0]: https://github.com/tsvikas/sync-with-uv/compare/v0.2.1...v0.3.0
[0.3.1]: https://github.com/tsvikas/sync-with-uv/compare/v0.3.0...v0.3.1
[0.4.0]: https://github.com/tsvikas/sync-with-uv/compare/v0.3.1...v0.4.0
[0.5.0]: https://github.com/tsvikas/sync-with-uv/compare/v0.4.0...v0.5.0
[unreleased]: https://github.com/tsvikas/sync-with-uv/compare/v0.5.0...HEAD
