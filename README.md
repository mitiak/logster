# logster

`logster` is a Python CLI that reads logs from `stdin` and writes formatted
lines to `stdout`.

It focuses on JSON-per-line logs and keeps non-JSON lines unchanged.

## Install

```bash
uv tool install .
```

## Usage

```bash
your_app 2>&1 | uv run logster
```

Example with uvicorn:

```bash
uv run uvicorn app:app --reload 2>&1 | uv run logster
```

Disable colors (MVP-safe flag):

```bash
your_app 2>&1 | uv run logster --no-color
```

## Configuration

`logster` can load TOML configuration from:

1. `--config /path/to/file.toml`
2. `LOGSTER_CONFIG=/path/to/file.toml`
3. `./logster.toml`
4. `./pyproject.toml` under `[tool.logster]`

Supported settings:

```toml
no_color = false
output_style = "compact" # compact | verbose

[fields]
timestamp = "timestamp"
level = "level"
path = "path"
query = "query"
top_k = "top_k"
file = "file"
function = "function"
line = "line"
message_fields = ["event", "message", "msg"]
```

Example in `pyproject.toml`:

```toml
[tool.logster]
no_color = true
```

Example standalone file (`logster.toml`):

```toml
no_color = true
```

Try a config quickly with the demo command:

```bash
uv run logster-manage demo --config ./logster.toml
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
uv run logster-manage info
uv run logster-manage test
uv run logster-manage install
uv run logster-manage demo
uv run logster-manage clean
uv run logster-manage clean --dry-run
```

Demo output:

```bash
uv run logster-manage demo
```

## Development

Create/sync the local environment:

```bash
uv sync
```

Run tests:

```bash
uv run --with pytest pytest -q
```

## Publish workflow

Use this when you want to release new changes:

1. Update `CHANGELOG.md` under `Unreleased`.
2. Bump `version` in `pyproject.toml`.
3. Run tests:

```bash
uv run --with pytest pytest -q
```

4. Build distribution artifacts:

```bash
uv build
```

5. Publish to PyPI (or another index):

```bash
uv publish
# or for TestPyPI:
uv publish --publish-url https://test.pypi.org/legacy/
```

6. Move `Unreleased` notes into a new version section in `CHANGELOG.md`.
7. Commit, tag, and push:

```bash
git add CHANGELOG.md README.md pyproject.toml
git commit -m "release: vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

`uv publish` expects credentials (for example `UV_PUBLISH_TOKEN`) to be set in
your environment.

## Use in other projects (separate uv environments)

Every project can keep its own isolated `.venv` and still use `logster`.

Install as a dependency in another project:

```bash
cd /path/to/other-project
uv add logster
uv run logster --help
```

If `logster` is not published yet, install from git:

```bash
uv add "logster @ git+https://github.com/mitiak/logster.git"
```

Run your app logs through `logster` inside that project's environment:

```bash
uv run your_app 2>&1 | uv run logster
```

If you want one global tool install (separate from project envs):

```bash
uv tool install logster
logster --help
```

## Documentation maintenance

- Keep `README.md` aligned with current CLI behavior and examples.
- Record every user-visible change in `CHANGELOG.md`.
- Add new entries under `Unreleased`, then cut a versioned section at release.
