"""Configuration loading for logster."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib
from typing import Any


DEFAULT_OUTPUT_STYLE = "compact"
ALLOWED_OUTPUT_STYLES = {"compact", "verbose"}


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
    return Config(no_color=no_color, output_style=output_style, fields=fields)


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
