"""CLI entrypoint for logster."""

from __future__ import annotations

import argparse
import json
import re
import sys

from logster import __version__
from logster.config import ANSI_COLOR_CODES
from logster.config import load_config
from logster.format import format_record


ANSI_RESET = "\033[0m"
LEVEL_TOKEN_COLORS = {
    "WARNING": "yellow",
    "ERROR": "red",
}


def _split_compose_prefix(line: str) -> tuple[str, str]:
    """Split `docker-compose logs` prefix (`service | `) from the payload."""
    prefix, sep, payload = line.partition(" | ")
    if sep and prefix.strip():
        return f"{prefix}{sep}", payload
    return "", line


def _with_newline(line: str) -> str:
    if line.endswith("\n"):
        return line
    return f"{line}\n"


def _highlight_passthrough_levels(line: str, *, use_color: bool) -> str:
    if not use_color:
        return line

    highlighted = line
    for level_token, color_name in LEVEL_TOKEN_COLORS.items():
        color_code = ANSI_COLOR_CODES[color_name]
        highlighted = re.sub(
            rf"\b{level_token}\b",
            lambda match: f"{color_code}{match.group(0)}{ANSI_RESET}",
            highlighted,
        )
    return highlighted


def main() -> None:
    parser = argparse.ArgumentParser(prog="logster")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Use verbose output style (overrides config)",
    )
    parser.add_argument(
        "--config",
        help="Path to TOML config file (logster.toml or pyproject.toml)",
    )
    args = parser.parse_args()
    try:
        config = load_config(config_path=args.config)
    except (FileNotFoundError, ValueError) as err:
        parser.error(str(err))
    use_color = not (config.no_color or args.no_color)
    output_style = "verbose" if args.verbose else config.output_style

    try:
        for raw_line in sys.stdin:
            parse_line = raw_line.rstrip("\n")
            compose_prefix, parse_line = _split_compose_prefix(parse_line)
            output: str

            try:
                parsed = json.loads(parse_line)
            except json.JSONDecodeError:
                output = _with_newline(
                    _highlight_passthrough_levels(raw_line, use_color=use_color)
                )
            else:
                if isinstance(parsed, dict):
                    formatted = format_record(
                        parsed,
                        use_color=use_color,
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
                    if compose_prefix:
                        output = "".join(
                            f"{compose_prefix}{line}\n"
                            for line in formatted.splitlines()
                        )
                    else:
                        output = f"{formatted}\n"
                else:
                    output = _with_newline(raw_line)

            sys.stdout.write(output)
            sys.stdout.flush()
    except (KeyboardInterrupt, BrokenPipeError):
        # Exit quietly on interrupted stdin or closed stdout pipeline.
        return


if __name__ == "__main__":
    main()
