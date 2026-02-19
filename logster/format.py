"""Formatting utilities for logster."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from logster.config import (
    ANSI_COLOR_CODES,
    DEFAULT_MESSAGE_COLOR,
    DEFAULT_METADATA_COLOR,
    DEFAULT_OUTPUT_STYLE,
    FieldMapping,
)


_TIME_RE = re.compile(r"(\d{2}:\d{2}:\d{2})")
ANSI_RESET = "\033[0m"


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


def _colorize(text: str, color_name: str, use_color: bool) -> str:
    if not use_color or not text:
        return text
    color_code = ANSI_COLOR_CODES.get(color_name)
    if color_code is None:
        raise ValueError(f"Unsupported color: {color_name}")
    return f"{color_code}{text}{ANSI_RESET}"


def _format_compact(
    *,
    time_text: str | None,
    level_text: str | None,
    path_text: str | None,
    query_text: str | None,
    top_k_text: str | None,
    origin_text: str | None,
) -> str:
    segments: list[str] = []
    if time_text is not None:
        segments.append(f"[{time_text}]")
    if level_text is not None:
        segments.append(f"[{level_text}]")
    if path_text is not None:
        segments.append(f"[{path_text}]")
    if query_text is not None:
        escaped_query = query_text.replace('"', '\\"')
        segments.append(f'[q="{escaped_query}"]')
    if top_k_text is not None:
        segments.append(f"[top_k={top_k_text}]")
    if origin_text is not None:
        segments.append(f"[{origin_text}]")
    return "".join(segments)


def _format_verbose(
    *,
    time_text: str | None,
    level_text: str | None,
    path_text: str | None,
    query_text: str | None,
    top_k_text: str | None,
    origin_text: str | None,
) -> str:
    segments: list[str] = []
    if time_text is not None:
        segments.append(f"time={time_text}")
    if level_text is not None:
        segments.append(f"level={level_text}")
    if path_text is not None:
        segments.append(f"path={path_text}")
    if query_text is not None:
        escaped_query = query_text.replace('"', '\\"')
        segments.append(f'query="{escaped_query}"')
    if top_k_text is not None:
        segments.append(f"top_k={top_k_text}")
    if origin_text is not None:
        segments.append(f"origin={origin_text}")
    return " ".join(segments)


def format_record(
    rec: dict[str, Any],
    *,
    use_color: bool = True,
    output_style: str = DEFAULT_OUTPUT_STYLE,
    metadata_color: str = DEFAULT_METADATA_COLOR,
    message_color: str = DEFAULT_MESSAGE_COLOR,
    fields: FieldMapping | None = None,
) -> str:
    """Format a JSON log record into a compact one-line representation."""
    if output_style not in {"compact", "verbose"}:
        raise ValueError(f"Unsupported output style: {output_style}")
    mapping = fields or FieldMapping()

    timestamp = rec.get(mapping.timestamp)
    time_text = format_time(timestamp) if isinstance(timestamp, str) else None

    level = rec.get(mapping.level)
    level_text = str(level).upper() if level is not None else None

    path = rec.get(mapping.path)
    path_text = str(path) if path is not None else None

    query = rec.get(mapping.query)
    query_text = str(query) if query is not None else None

    top_k = rec.get(mapping.top_k)
    top_k_text = str(top_k) if top_k is not None else None

    line = rec.get(mapping.line)
    function = rec.get(mapping.function)
    file_name = rec.get(mapping.file)
    origin_text: str | None = None
    if line is not None and (function is not None or file_name is not None):
        origin = function if function is not None else file_name
        origin_text = f"{origin}:{line}"

    message = None
    for key in mapping.message_fields:
        if rec.get(key) is not None:
            message = str(rec[key])
            break

    if output_style == "compact":
        metadata = _format_compact(
            time_text=time_text,
            level_text=level_text,
            path_text=path_text,
            query_text=query_text,
            top_k_text=top_k_text,
            origin_text=origin_text,
        )
    else:
        metadata = _format_verbose(
            time_text=time_text,
            level_text=level_text,
            path_text=path_text,
            query_text=query_text,
            top_k_text=top_k_text,
            origin_text=origin_text,
        )

    base = _colorize(metadata, metadata_color, use_color)
    if message:
        if output_style == "compact":
            message_text = message
        else:
            escaped_message = message.replace('"', '\\"')
            message_text = f'msg="{escaped_message}"'
        colored_message = _colorize(message_text, message_color, use_color)
        if base:
            return f"{base} {colored_message}"
        return colored_message
    return base
