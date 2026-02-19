"""Formatting utilities for logster."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


_TIME_RE = re.compile(r"(\d{2}:\d{2}:\d{2})")
ANSI_RESET = "\033[0m"
ANSI_METADATA = "\033[36m"
ANSI_MESSAGE = "\033[97m"


def format_time(ts: str) -> str:
    """Format an ISO timestamp to HH:MM:SS (UTC when timezone is present)."""
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.strftime("%H:%M:%S")
    except ValueError:
        pass

    source = ts.split("T", 1)[1] if "T" in ts else ts
    match = _TIME_RE.search(source)
    if match:
        return match.group(1)
    return source[:8]


def _colorize(text: str, color_code: str, use_color: bool) -> str:
    if not use_color or not text:
        return text
    return f"{color_code}{text}{ANSI_RESET}"


def format_record(rec: dict[str, Any], *, use_color: bool = True) -> str:
    """Format a JSON log record into a compact one-line representation."""
    segments: list[str] = []

    timestamp = rec.get("timestamp")
    if isinstance(timestamp, str):
        segments.append(f"[{format_time(timestamp)}]")

    level = rec.get("level")
    if level is not None:
        segments.append(f"[{str(level).upper()}]")

    path = rec.get("path")
    if path is not None:
        segments.append(f"[{path}]")

    if "query" in rec and rec.get("query") is not None:
        query = str(rec["query"]).replace('"', '\\"')
        segments.append(f'[q="{query}"]')

    if "top_k" in rec and rec.get("top_k") is not None:
        segments.append(f"[top_k={rec['top_k']}]")

    line = rec.get("line")
    function = rec.get("function")
    file_name = rec.get("file")
    if line is not None and (function is not None or file_name is not None):
        origin = function if function is not None else file_name
        segments.append(f"[{origin}:{line}]")

    message = None
    for key in ("event", "message", "msg"):
        if rec.get(key) is not None:
            message = str(rec[key])
            break

    base = _colorize("".join(segments), ANSI_METADATA, use_color)
    if message:
        colored_message = _colorize(message, ANSI_MESSAGE, use_color)
        if base:
            return f"{base} {colored_message}"
        return colored_message
    return base
