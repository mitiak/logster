"""Configuration loading for logster."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib
from typing import Any


@dataclass(frozen=True)
class Config:
    no_color: bool = False


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
    return Config(no_color=no_color)


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
