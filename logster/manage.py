"""Project management CLI for logster."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from logster.config import COLOR_SCHEME_PRESETS, COLOR_SCHEME_VERBOSE_PRESETS, load_config
from logster.format import format_record


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return proc.returncode


def _clean(dry_run: bool = False) -> int:
    static_dirs = ["build", "dist", ".pytest_cache", "logster.egg-info"]
    removed: list[Path] = []

    for name in static_dirs:
        path = PROJECT_ROOT / name
        if path.exists():
            removed.append(path)

    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        removed.append(cache_dir)

    if not removed:
        print("Nothing to clean.")
        return 0

    for path in removed:
        if dry_run:
            print(f"Would remove: {path}")
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
        print(f"Removed: {path}")
    return 0


def _info() -> int:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Python: {sys.executable}")
    print("Commands: logster, logster-manage")
    return 0


def _test() -> int:
    if shutil.which("uv"):
        return _run(["uv", "run", "--with", "pytest", "pytest", "-q"])
    return _run([sys.executable, "-m", "pytest", "-q"])


def _install() -> int:
    return _run([sys.executable, "-m", "pip", "install", "-e", "."])


def _demo(
    *,
    config_path: str | None = None,
    no_color: bool = False,
    output_style_override: str | None = None,
) -> int:
    sample = {
        "query": "timing",
        "top_k": 5,
        "event": "query_endpoint_started",
        "request_id": "5342fb6b-8ff0-4d9d-84a5-1f6b0e098528",
        "path": "/query",
        "timestamp": "2026-02-19T10:12:05.497600Z",
        "level": "info",
        "file": "query.py",
        "function": "query",
        "line": 17,
    }
    config = load_config(config_path=config_path, cwd=PROJECT_ROOT)
    output_style = output_style_override or config.output_style
    print("Input JSON:")
    print(json.dumps(sample, separators=(",", ":")))
    print("Output:")
    print(
        format_record(
            sample,
            use_color=not (config.no_color or no_color),
            output_style=output_style,
            time_color=config.time_color,
            level_color=config.level_color,
            file_color=config.file_color,
            origin_color=config.origin_color,
            metadata_color=config.metadata_color,
            message_color=config.message_color,
            verbose_metadata_key_color=config.verbose_metadata_key_color,
            verbose_metadata_value_color=config.verbose_metadata_value_color,
            verbose_metadata_punctuation_color=config.verbose_metadata_punctuation_color,
            fields=config.fields,
        )
    )
    return 0


def _demo_color_schemes(*, verbose: bool = False) -> int:
    sample = {
        "query": "timing",
        "top_k": 5,
        "event": "query_endpoint_started",
        "path": "/query",
        "timestamp": "2026-02-19T10:12:05.497600Z",
        "level": "info",
        "function": "query",
        "line": 17,
    }
    print("Available color schemes:")
    for scheme_name, (metadata_color, message_color) in sorted(COLOR_SCHEME_PRESETS.items()):
        (
            verbose_key_color,
            verbose_value_color,
            verbose_punctuation_color,
        ) = COLOR_SCHEME_VERBOSE_PRESETS.get(
            scheme_name,
            (metadata_color, message_color, metadata_color),
        )
        preview = format_record(
            sample,
            use_color=True,
            output_style="verbose" if verbose else "compact",
            time_color=metadata_color,
            level_color=metadata_color,
            file_color=metadata_color,
            origin_color=metadata_color,
            metadata_color=metadata_color,
            message_color=message_color,
            verbose_metadata_key_color=verbose_key_color,
            verbose_metadata_value_color=verbose_value_color,
            verbose_metadata_punctuation_color=verbose_punctuation_color,
        )
        preview_lines = preview.splitlines()
        print(f"{scheme_name}:")
        for line in preview_lines:
            print(line)
        print()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logster-manage")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Show project information")
    sub.add_parser("test", help="Run test suite")
    sub.add_parser("install", help="Install project in editable mode")
    demo_parser = sub.add_parser("demo", help="Print sample input and formatted output")
    demo_parser.add_argument(
        "--config",
        help="Path to TOML config file (logster.toml or pyproject.toml)",
    )
    demo_parser.add_argument("--no-color", action="store_true", help="Disable colors")
    demo_parser.add_argument(
        "--list-color-schemes",
        action="store_true",
        help="Show all preset color schemes with a preview",
    )
    demo_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Use verbose output style for demo and color-scheme previews",
    )

    clean_parser = sub.add_parser("clean", help="Remove caches and build artifacts")
    clean_parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "info":
        code = _info()
    elif args.command == "test":
        code = _test()
    elif args.command == "install":
        code = _install()
    elif args.command == "demo":
        try:
            if args.list_color_schemes:
                code = _demo_color_schemes(verbose=args.verbose)
            else:
                code = _demo(
                    config_path=args.config,
                    no_color=args.no_color,
                    output_style_override="verbose" if args.verbose else None,
                )
        except (FileNotFoundError, ValueError) as err:
            parser.error(str(err))
    else:
        code = _clean(dry_run=args.dry_run)

    raise SystemExit(code)


if __name__ == "__main__":
    main()
