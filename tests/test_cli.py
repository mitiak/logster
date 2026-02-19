import subprocess
import sys

from logster import cli


def test_cli_formats_json_and_passthrough_non_json():
    json_line = (
        '{"query":"timing","top_k":5,"event":"query_endpoint_started",'
        '"request_id":"5342fb6b-8ff0-4d9d-84a5-1f6b0e098528","path":"/query",'
        '"timestamp":"2026-02-19T10:12:05.497600Z","level":"info",'
        '"file":"query.py","function":"query","line":17}'
    )
    plain_line = "plain non-json log line"
    data = f"{json_line}\n{plain_line}\n"

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli", "--no-color"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
    )

    out_lines = proc.stdout.splitlines()
    assert (
        out_lines[0]
        == '[10:12:05][INFO][/query][q="timing"][top_k=5][query:17] query_endpoint_started'
    )
    assert out_lines[1] == plain_line


def test_cli_exits_quietly_on_keyboard_interrupt(monkeypatch):
    class InterruptingStdin:
        def __iter__(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "argv", ["logster", "--no-color"])
    monkeypatch.setattr(sys, "stdin", InterruptingStdin())

    cli.main()
