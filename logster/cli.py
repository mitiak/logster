"""CLI entrypoint for logster."""

from __future__ import annotations

import argparse
import json
import sys

from logster.config import load_config
from logster.format import format_record


def main() -> None:
    parser = argparse.ArgumentParser(prog="logster")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")
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

    try:
        for raw_line in sys.stdin:
            parse_line = raw_line.rstrip("\n")
            output: str

            try:
                parsed = json.loads(parse_line)
            except json.JSONDecodeError:
                output = raw_line
                if not output.endswith("\n"):
                    output += "\n"
            else:
                if isinstance(parsed, dict):
                    output = (
                        f"{format_record(parsed, use_color=use_color, output_style=config.output_style, time_color=config.time_color, level_color=config.level_color, file_color=config.file_color, origin_color=config.origin_color, metadata_color=config.metadata_color, message_color=config.message_color, verbose_metadata_key_color=config.verbose_metadata_key_color, verbose_metadata_value_color=config.verbose_metadata_value_color, verbose_metadata_punctuation_color=config.verbose_metadata_punctuation_color, fields=config.fields)}\n"
                    )
                else:
                    output = raw_line
                    if not output.endswith("\n"):
                        output += "\n"

            sys.stdout.write(output)
            sys.stdout.flush()
    except (KeyboardInterrupt, BrokenPipeError):
        # Exit quietly on interrupted stdin or closed stdout pipeline.
        return


if __name__ == "__main__":
    main()
