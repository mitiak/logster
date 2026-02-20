# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows Semantic
Versioning.

## [Unreleased]

### Added
- Added `theme` as a preset selector in `logster.toml` (alias for
  `color_scheme`).
- Added `[fields].main_line_fields` so projects can choose which fields are
  rendered on the main line.

### Changed
- Updated example `logster.toml` and README configuration docs to include
  `theme`.
- Verbose metadata line now outputs raw JSON only (without `metadata:` prefix).
- Verbose metadata keys and values now use different configurable colors.
- Added `--verbose` option to `logster-manage demo --list-color-schemes`.
- Added fine-grained color configuration for all rendered parts: `time_color`,
  `level_color`, `file_color`, `origin_color`, `message_color`,
  `verbose_metadata_key_color`, `verbose_metadata_value_color`,
  `verbose_metadata_punctuation_color`.
- Added `monokai-github-meta` preset (Monokai main line + GitHub-dark verbose
  metadata line).
- Verbose metadata now always includes every JSON key that was not rendered on
  the main line.

## [0.2.0] - 2026-02-19

### Added
- `logster-manage demo` command to print sample JSON input and its formatted
  one-line output.
- Added `CHANGELOG.md` with Keep a Changelog structure for tracking updates.
- External config loading via `logster.toml`, `pyproject.toml` (`[tool.logster]`),
  `LOGSTER_CONFIG`, or `--config`.
- Configurable output style (`compact` or `verbose`) and field mapping via
  `[fields]` including `message_fields`.
- `logster-manage demo --config ...` support for trying different configurations.
- Configurable metadata/message colors via config (`metadata_color`,
  `message_color`) and preset `color_scheme` selection.
- Added 10 popular color-scheme presets: `dracula`, `nord`, `gruvbox`,
  `solarized-dark`, `solarized-light`, `monokai`, `one-dark`, `tokyo-night`,
  `catppuccin-mocha`, and `github-dark`.
- `logster-manage demo --list-color-schemes` to preview all preset schemes in
  terminal output.

### Changed
- Expanded `README.md` with usage, output format, development commands, and
  documentation maintenance rules.
- `--no-color` is now consistently applied during formatting, and can be set
  via config (`no_color = true`).
- Compact output style now emits `[time][level][file][function:line] message`.
- Verbose output now emits 2 lines: main compact-style mandatory fields + a
  JSON line containing all non-mandatory keys.

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
