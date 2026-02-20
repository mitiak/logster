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


def _format_metadata_json(
    value: Any,
    *,
    use_color: bool,
    key_color: str,
    value_color: str,
    punctuation_color: str,
) -> str:
    def punct(text: str) -> str:
        return _colorize(text, punctuation_color, use_color, dim=True)

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
                punctuation_color=punctuation_color,
            )
            parts.append(f"{key_token}{punct(':')}{value_token}")
        return f"{punct('{')}{punct(',').join(parts)}{punct('}')}"
    if isinstance(value, list):
        parts = [
            _format_metadata_json(
                item,
                use_color=use_color,
                key_color=key_color,
                value_color=value_color,
                punctuation_color=punctuation_color,
            )
            for item in value
        ]
        return f"{punct('[')}{punct(',').join(parts)}{punct(']')}"
    rendered = json.dumps(value, separators=(",", ":"))
    return _colorize(rendered, value_color, use_color, dim=True)


def format_record(
    rec: dict[str, Any],
    *,
    use_color: bool = True,
    output_style: str = DEFAULT_OUTPUT_STYLE,
    time_color: str | None = None,
    level_color: str | None = None,
    file_color: str | None = None,
    origin_color: str | None = None,
    metadata_color: str = DEFAULT_METADATA_COLOR,
    message_color: str = DEFAULT_MESSAGE_COLOR,
    verbose_metadata_key_color: str | None = None,
    verbose_metadata_value_color: str | None = None,
    verbose_metadata_punctuation_color: str | None = None,
    fields: FieldMapping | None = None,
) -> str:
    """Format a JSON log record into a compact one-line representation."""
    if output_style not in {"compact", "verbose"}:
        raise ValueError(f"Unsupported output style: {output_style}")
    mapping = fields or FieldMapping()
    resolved_time_color = time_color or metadata_color
    resolved_level_color = level_color or metadata_color
    resolved_file_color = file_color or metadata_color
    resolved_origin_color = origin_color or metadata_color
    resolved_verbose_key_color = verbose_metadata_key_color or metadata_color
    resolved_verbose_value_color = verbose_metadata_value_color or message_color
    resolved_verbose_punctuation_color = (
        verbose_metadata_punctuation_color or metadata_color
    )

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

    known_keys: dict[str, str] = {
        "timestamp": mapping.timestamp,
        "level": mapping.level,
        "path": mapping.path,
        "query": mapping.query,
        "top_k": mapping.top_k,
        "file": mapping.file,
        "function": mapping.function,
        "line": mapping.line,
    }

    bracket_segments: list[str] = []
    main_message: str | None = None
    rendered_main_keys: set[str] = set()
    for main_field in mapping.main_line_fields:
        if main_field == "timestamp" and time_text is not None:
            bracket_segments.append(_colorize(f"[{time_text}]", resolved_time_color, use_color))
            rendered_main_keys.add(mapping.timestamp)
            continue
        if main_field == "level" and level_text is not None:
            bracket_segments.append(_colorize(f"[{level_text}]", resolved_level_color, use_color))
            rendered_main_keys.add(mapping.level)
            continue
        if main_field == "file" and file_text is not None:
            bracket_segments.append(_colorize(f"[{file_text}]", resolved_file_color, use_color))
            rendered_main_keys.add(mapping.file)
            continue
        if main_field == "origin" and origin_text is not None:
            bracket_segments.append(_colorize(f"[{origin_text}]", resolved_origin_color, use_color))
            rendered_main_keys.add(mapping.line)
            if function is not None:
                rendered_main_keys.add(mapping.function)
            elif file_name is not None:
                rendered_main_keys.add(mapping.file)
            continue
        if main_field == "message" and message is not None:
            main_message = _colorize(message, message_color, use_color)
            if message_key is not None:
                rendered_main_keys.add(message_key)
            continue
        if main_field in {"function", "line"}:
            continue

        resolved_key = known_keys.get(main_field, main_field)
        raw_value = rec.get(resolved_key)
        if raw_value is None:
            continue
        raw_label = known_keys.get(main_field)
        if raw_label is None:
            token = f"[{main_field}={json.dumps(raw_value, separators=(',', ':'))}]"
        else:
            token = f"[{json.dumps(raw_value, separators=(',', ':'))}]"
        bracket_segments.append(_colorize(token, metadata_color, use_color))
        rendered_main_keys.add(resolved_key)

    base = "".join(bracket_segments)
    if main_message is not None:
        if base:
            main_line = f"{base} {main_message}"
        else:
            main_line = main_message
    else:
        main_line = base

    if output_style == "compact":
        return main_line

    metadata_obj = {key: value for key, value in rec.items() if key not in rendered_main_keys}
    metadata_line = _format_metadata_json(
        metadata_obj,
        use_color=use_color,
        key_color=resolved_verbose_key_color,
        value_color=resolved_verbose_value_color,
        punctuation_color=resolved_verbose_punctuation_color,
    )
    if main_line:
        return f"{main_line}\n{metadata_line}"
    return metadata_line
