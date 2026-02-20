"""Configuration loading for logster."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib
from typing import Any


DEFAULT_OUTPUT_STYLE = "compact"
ALLOWED_OUTPUT_STYLES = {"compact", "verbose"}
DEFAULT_COLOR_SCHEME = "default"
ANSI_COLOR_CODES = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "orange": "\033[38;5;208m",
    "pink": "\033[38;5;213m",
    "purple": "\033[38;5;141m",
}
COLOR_SCHEME_PRESETS = {
    "default": ("cyan", "bright_white"),
    "dracula": ("bright_magenta", "bright_cyan"),
    "nord": ("bright_blue", "white"),
    "gruvbox": ("yellow", "bright_yellow"),
    "solarized-dark": ("cyan", "green"),
    "solarized-light": ("blue", "black"),
    "monokai": ("green", "bright_yellow"),
    "one-dark": ("bright_blue", "bright_white"),
    "tokyo-night": ("bright_cyan", "purple"),
    "catppuccin-mocha": ("pink", "bright_blue"),
    "github-dark": ("bright_black", "white"),
    "monokai-github-meta": ("green", "bright_yellow"),
}
COLOR_SCHEME_VERBOSE_PRESETS = {
    "github-dark": ("bright_black", "white", "bright_black"),
    "monokai-github-meta": ("bright_black", "white", "bright_black"),
}
DEFAULT_METADATA_COLOR, DEFAULT_MESSAGE_COLOR = COLOR_SCHEME_PRESETS[DEFAULT_COLOR_SCHEME]
DEFAULT_VERBOSE_METADATA_KEY_COLOR = DEFAULT_METADATA_COLOR
DEFAULT_VERBOSE_METADATA_VALUE_COLOR = DEFAULT_MESSAGE_COLOR
DEFAULT_VERBOSE_METADATA_PUNCTUATION_COLOR = DEFAULT_METADATA_COLOR


@dataclass(frozen=True)
class FieldMapping:
    timestamp: str = "timestamp"
    level: str = "level"
    path: str = "path"
    query: str = "query"
    top_k: str = "top_k"
    file: str = "file"
    function: str = "function"
    line: str = "line"
    message_fields: tuple[str, ...] = ("event", "message", "msg")


@dataclass(frozen=True)
class Config:
    no_color: bool = False
    output_style: str = DEFAULT_OUTPUT_STYLE
    theme: str = DEFAULT_COLOR_SCHEME
    color_scheme: str = DEFAULT_COLOR_SCHEME
    time_color: str = DEFAULT_METADATA_COLOR
    level_color: str = DEFAULT_METADATA_COLOR
    file_color: str = DEFAULT_METADATA_COLOR
    origin_color: str = DEFAULT_METADATA_COLOR
    metadata_color: str = DEFAULT_METADATA_COLOR
    message_color: str = DEFAULT_MESSAGE_COLOR
    verbose_metadata_key_color: str = DEFAULT_VERBOSE_METADATA_KEY_COLOR
    verbose_metadata_value_color: str = DEFAULT_VERBOSE_METADATA_VALUE_COLOR
    verbose_metadata_punctuation_color: str = DEFAULT_VERBOSE_METADATA_PUNCTUATION_COLOR
    fields: FieldMapping = FieldMapping()


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid TOML object in {path}")
    return data


def _normalize(data: dict[str, Any], source: Path) -> Config:
    no_color = data.get("no_color", False)
    if not isinstance(no_color, bool):
        raise ValueError(f"'no_color' must be a boolean in {source}")

    output_style = data.get("output_style", DEFAULT_OUTPUT_STYLE)
    if not isinstance(output_style, str) or output_style not in ALLOWED_OUTPUT_STYLES:
        allowed = ", ".join(sorted(ALLOWED_OUTPUT_STYLES))
        raise ValueError(
            f"'output_style' must be one of [{allowed}] in {source}"
        )

    raw_theme = data.get("theme")
    if raw_theme is not None and not isinstance(raw_theme, str):
        raise ValueError(f"'theme' must be a string in {source}")

    color_scheme = data.get("color_scheme", DEFAULT_COLOR_SCHEME)
    if not isinstance(color_scheme, str) or color_scheme not in COLOR_SCHEME_PRESETS:
        allowed = ", ".join(sorted(COLOR_SCHEME_PRESETS))
        raise ValueError(
            f"'color_scheme' must be one of [{allowed}] in {source}"
        )
    theme = raw_theme if raw_theme is not None else color_scheme
    if theme not in COLOR_SCHEME_PRESETS:
        allowed = ", ".join(sorted(COLOR_SCHEME_PRESETS))
        raise ValueError(
            f"'theme' must be one of [{allowed}] in {source}"
        )
    default_metadata_color, default_message_color = COLOR_SCHEME_PRESETS[theme]
    (
        default_verbose_metadata_key_color,
        default_verbose_metadata_value_color,
        default_verbose_metadata_punctuation_color,
    ) = COLOR_SCHEME_VERBOSE_PRESETS.get(
        theme,
        (
            default_metadata_color,
            default_message_color,
            default_metadata_color,
        ),
    )

    metadata_color = data.get("metadata_color", default_metadata_color)
    if not isinstance(metadata_color, str) or metadata_color not in ANSI_COLOR_CODES:
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'metadata_color' must be one of [{allowed}] in {source}"
        )

    time_color = data.get("time_color", metadata_color)
    if not isinstance(time_color, str) or time_color not in ANSI_COLOR_CODES:
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'time_color' must be one of [{allowed}] in {source}"
        )

    level_color = data.get("level_color", metadata_color)
    if not isinstance(level_color, str) or level_color not in ANSI_COLOR_CODES:
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'level_color' must be one of [{allowed}] in {source}"
        )

    file_color = data.get("file_color", metadata_color)
    if not isinstance(file_color, str) or file_color not in ANSI_COLOR_CODES:
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'file_color' must be one of [{allowed}] in {source}"
        )

    origin_color = data.get("origin_color", metadata_color)
    if not isinstance(origin_color, str) or origin_color not in ANSI_COLOR_CODES:
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'origin_color' must be one of [{allowed}] in {source}"
        )

    message_color = data.get("message_color", default_message_color)
    if not isinstance(message_color, str) or message_color not in ANSI_COLOR_CODES:
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'message_color' must be one of [{allowed}] in {source}"
        )

    verbose_metadata_key_color = data.get(
        "verbose_metadata_key_color",
        default_verbose_metadata_key_color,
    )
    if (
        not isinstance(verbose_metadata_key_color, str)
        or verbose_metadata_key_color not in ANSI_COLOR_CODES
    ):
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'verbose_metadata_key_color' must be one of [{allowed}] in {source}"
        )

    verbose_metadata_value_color = data.get(
        "verbose_metadata_value_color",
        default_verbose_metadata_value_color,
    )
    if (
        not isinstance(verbose_metadata_value_color, str)
        or verbose_metadata_value_color not in ANSI_COLOR_CODES
    ):
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'verbose_metadata_value_color' must be one of [{allowed}] in {source}"
        )

    verbose_metadata_punctuation_color = data.get(
        "verbose_metadata_punctuation_color",
        default_verbose_metadata_punctuation_color,
    )
    if (
        not isinstance(verbose_metadata_punctuation_color, str)
        or verbose_metadata_punctuation_color not in ANSI_COLOR_CODES
    ):
        allowed = ", ".join(sorted(ANSI_COLOR_CODES))
        raise ValueError(
            f"'verbose_metadata_punctuation_color' must be one of [{allowed}] in {source}"
        )

    raw_fields = data.get("fields", {})
    if not isinstance(raw_fields, dict):
        raise ValueError(f"'fields' must be a table in {source}")

    field_values = dict(FieldMapping().__dict__)
    for key in ("timestamp", "level", "path", "query", "top_k", "file", "function", "line"):
        if key in raw_fields:
            value = raw_fields[key]
            if not isinstance(value, str) or not value:
                raise ValueError(f"'fields.{key}' must be a non-empty string in {source}")
            field_values[key] = value

    if "message_fields" in raw_fields:
        raw_message_fields = raw_fields["message_fields"]
        if (
            not isinstance(raw_message_fields, list)
            or not raw_message_fields
            or any(not isinstance(item, str) or not item for item in raw_message_fields)
        ):
            raise ValueError(
                f"'fields.message_fields' must be a non-empty list of strings in {source}"
            )
        field_values["message_fields"] = tuple(raw_message_fields)

    fields = FieldMapping(**field_values)
    return Config(
        no_color=no_color,
        output_style=output_style,
        theme=theme,
        color_scheme=color_scheme,
        time_color=time_color,
        level_color=level_color,
        file_color=file_color,
        origin_color=origin_color,
        metadata_color=metadata_color,
        message_color=message_color,
        verbose_metadata_key_color=verbose_metadata_key_color,
        verbose_metadata_value_color=verbose_metadata_value_color,
        verbose_metadata_punctuation_color=verbose_metadata_punctuation_color,
        fields=fields,
    )


def _from_file(path: Path) -> Config:
    data = _read_toml(path)
    if path.name == "pyproject.toml":
        tool = data.get("tool", {})
        if not isinstance(tool, dict):
            raise ValueError(f"'tool' must be a table in {path}")
        raw = tool.get("logster", {})
        if raw == {}:
            return Config()
        if not isinstance(raw, dict):
            raise ValueError(f"'tool.logster' must be a table in {path}")
        return _normalize(raw, path)
    return _normalize(data, path)


def _find_default_file(cwd: Path) -> Path | None:
    logster_toml = cwd / "logster.toml"
    if logster_toml.exists():
        return logster_toml
    pyproject = cwd / "pyproject.toml"
    if pyproject.exists():
        return pyproject
    return None


def load_config(*, config_path: str | None = None, cwd: Path | None = None) -> Config:
    base = cwd or Path.cwd()
    if config_path:
        candidate = Path(config_path).expanduser()
        if not candidate.is_absolute():
            candidate = (base / candidate).resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"Config file not found: {candidate}")
        return _from_file(candidate)

    env_path = os.environ.get("LOGSTER_CONFIG")
    if env_path:
        return load_config(config_path=env_path, cwd=base)

    discovered = _find_default_file(base)
    if discovered is None:
        return Config()
    return _from_file(discovered)
