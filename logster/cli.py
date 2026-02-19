"""CLI entrypoint for logster."""

from __future__ import annotations

import argparse
import json
import sys

from logster.format import format_record


def main() -> None:
    parser = argparse.ArgumentParser(prog="logster")
    parser.add_argument("--no-color", action="store_true", help="Disable colors")
    args = parser.parse_args()

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
                    output = f"{format_record(parsed, use_color=not args.no_color)}\n"
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
