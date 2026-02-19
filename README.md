# logster

`logster` is a Python CLI that reads logs from `stdin` and writes formatted
lines to `stdout`.

It focuses on JSON-per-line logs and keeps non-JSON lines unchanged.

## Install

```bash
pip install .
```

## Usage

```bash
your_app 2>&1 | logster
```

Example with uvicorn:

```bash
uvicorn app:app --reload 2>&1 | logster
```

Disable colors (MVP-safe flag):

```bash
your_app 2>&1 | logster --no-color
```

## Output format

For JSON records, `logster` emits compact one-liners:

```text
[HH:MM:SS][LEVEL][/path][q="..."][top_k=...][function:line] message
```

Only available fields are rendered; missing segments are omitted.

## Project management CLI

This project includes `logster-manage` for local development tasks:

```bash
logster-manage info
logster-manage test
logster-manage install
logster-manage clean
logster-manage clean --dry-run
```

## Development

Run tests:

```bash
uv run --with pytest pytest -q
```

## Documentation maintenance

- Keep `README.md` aligned with current CLI behavior and examples.
- Record every user-visible change in `CHANGELOG.md`.
- Add new entries under `Unreleased`, then cut a versioned section at release.
