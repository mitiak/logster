"""Project management CLI for logster."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

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


def _demo() -> int:
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
    print("Input JSON:")
    print(json.dumps(sample, separators=(",", ":")))
    print("Output:")
    print(format_record(sample))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logster-manage")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("info", help="Show project information")
    sub.add_parser("test", help="Run test suite")
    sub.add_parser("install", help="Install project in editable mode")
    sub.add_parser("demo", help="Print sample input and formatted output")

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
        code = _demo()
    else:
        code = _clean(dry_run=args.dry_run)

    raise SystemExit(code)


if __name__ == "__main__":
    main()
