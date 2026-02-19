"""Formatting utilities for logster."""

from __future__ import annotations

from datetime import datetime, timezone
import json
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
ANSI_DIM = "\033[2m"


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


def _colorize(text: str, color_name: str, use_color: bool, *, dim: bool = False) -> str:
    if not use_color or not text:
        return text
    color_code = ANSI_COLOR_CODES.get(color_name)
    if color_code is None:
        raise ValueError(f"Unsupported color: {color_name}")
    prefix = f"{ANSI_DIM}{color_code}" if dim else color_code
    return f"{prefix}{text}{ANSI_RESET}"


def _format_compact(
    *,
    time_text: str | None,
    level_text: str | None,
    file_text: str | None,
    origin_text: str | None,
) -> str:
    segments: list[str] = []
    if time_text is not None:
        segments.append(f"[{time_text}]")
    if level_text is not None:
        segments.append(f"[{level_text}]")
    if file_text is not None:
        segments.append(f"[{file_text}]")
    if origin_text is not None:
        segments.append(f"[{origin_text}]")
    return "".join(segments)


def _format_metadata_json(
    value: Any,
    *,
    use_color: bool,
    key_color: str,
    value_color: str,
) -> str:
    if isinstance(value, dict):
        parts: list[str] = []
        for key in sorted(value):
            key_json = json.dumps(key, separators=(",", ":"))
            key_token = _colorize(key_json, key_color, use_color, dim=True)
            value_token = _format_metadata_json(
                value[key],
                use_color=use_color,
                key_color=key_color,
                value_color=value_color,
            )
            parts.append(f"{key_token}:{value_token}")
        return "{" + ",".join(parts) + "}"
    if isinstance(value, list):
        inner = ",".join(
            _format_metadata_json(
                item,
                use_color=use_color,
                key_color=key_color,
                value_color=value_color,
            )
            for item in value
        )
        return "[" + inner + "]"
    rendered = json.dumps(value, separators=(",", ":"))
    return _colorize(rendered, value_color, use_color, dim=True)


def format_record(
    rec: dict[str, Any],
    *,
    use_color: bool = True,
    output_style: str = DEFAULT_OUTPUT_STYLE,
    metadata_color: str = DEFAULT_METADATA_COLOR,
    message_color: str = DEFAULT_MESSAGE_COLOR,
    verbose_metadata_key_color: str = DEFAULT_METADATA_COLOR,
    verbose_metadata_value_color: str = DEFAULT_MESSAGE_COLOR,
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

    line = rec.get(mapping.line)
    function = rec.get(mapping.function)
    file_name = rec.get(mapping.file)
    file_text = str(file_name) if file_name is not None else None
    origin_text: str | None = None
    if line is not None and (function is not None or file_name is not None):
        origin = function if function is not None else file_name
        origin_text = f"{origin}:{line}"

    message = None
    message_key: str | None = None
    for key in mapping.message_fields:
        if rec.get(key) is not None:
            message = str(rec[key])
            message_key = key
            break

    first_line = _format_compact(
        time_text=time_text,
        level_text=level_text,
        file_text=file_text,
        origin_text=origin_text,
    )
    base = _colorize(first_line, metadata_color, use_color)
    if message:
        message_text = message
        colored_message = _colorize(message_text, message_color, use_color)
        if base:
            main_line = f"{base} {colored_message}"
        else:
            main_line = colored_message
    else:
        main_line = base

    if output_style == "compact":
        return main_line

    mandatory_keys = {
        mapping.timestamp,
        mapping.level,
        mapping.file,
        mapping.function,
        mapping.line,
    }
    if message_key is not None:
        mandatory_keys.add(message_key)

    metadata_obj = {key: value for key, value in rec.items() if key not in mandatory_keys}
    metadata_line = _format_metadata_json(
        metadata_obj,
        use_color=use_color,
        key_color=verbose_metadata_key_color,
        value_color=verbose_metadata_value_color,
    )
    if main_line:
        return f"{main_line}\n{metadata_line}"
    return metadata_line
