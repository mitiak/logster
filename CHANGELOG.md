# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic
Versioning.

## [Unreleased]

### Added
- `logster-manage demo` command to print sample JSON input and its formatted
  one-line output.
- Added `CHANGELOG.md` with Keep a Changelog structure for tracking updates.
- External config loading via `logster.toml`, `pyproject.toml` (`[tool.logster]`),
  `LOGSTER_CONFIG`, or `--config`.

### Changed
- Expanded `README.md` with usage, output format, development commands, and
  documentation maintenance rules.
- `--no-color` is now consistently applied during formatting, and can be set
  via config (`no_color = true`).

## [0.1.0] - 2026-02-19

### Added
- Initial publishable Python package with `pyproject.toml`.
- `logster` pipe-mode CLI for formatting JSON-per-line logs.
- Pass-through behavior for non-JSON lines.
- Formatting engine in `logster/format.py` with timestamp normalization and
  compact segment rendering.
- `--no-color` CLI flag (MVP-compatible).
- `logster-manage` CLI for project tasks (`info`, `test`, `install`, `clean`).
- Test suite for formatter, CLI behavior, and manager commands.
- Basic project documentation in `README.md`.
