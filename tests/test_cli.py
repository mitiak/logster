import subprocess
import sys
from pathlib import Path

from logster import cli


def test_cli_formats_json_and_passthrough_non_json(tmp_path: Path):
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
        cwd=tmp_path,
    )

    out_lines = proc.stdout.splitlines()
    assert (
        out_lines[0]
        == "[10:12:05][INFO][query.py][query:17] query_endpoint_started"
    )
    assert out_lines[1] == plain_line


def test_cli_exits_quietly_on_keyboard_interrupt(monkeypatch):
    class InterruptingStdin:
        def __iter__(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "argv", ["logster", "--no-color"])
    monkeypatch.setattr(sys, "stdin", InterruptingStdin())

    cli.main()


def test_cli_reads_logster_toml_config(tmp_path: Path):
    (tmp_path / "logster.toml").write_text("no_color = true\n", encoding="utf-8")
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\x1b[" not in proc.stdout
    assert proc.stdout.strip() == "[10:12:05][INFO] hello"


def test_cli_reads_pyproject_tool_logster_config(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.logster]\nno_color = true\n",
        encoding="utf-8",
    )
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\x1b[" not in proc.stdout
    assert proc.stdout.strip() == "[10:12:05][INFO] hello"


def test_cli_prefers_logster_toml_over_pyproject(tmp_path: Path):
    (tmp_path / "logster.toml").write_text("no_color = true\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[tool.logster]\nno_color = false\n",
        encoding="utf-8",
    )
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\x1b[" not in proc.stdout
    assert proc.stdout.strip() == "[10:12:05][INFO] hello"


def test_cli_reads_output_style_verbose_config(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        "no_color = true\noutput_style = \"verbose\"\n",
        encoding="utf-8",
    )
    data = '{"event":"hello world","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert proc.stdout.strip() == "[10:12:05][INFO] hello world\n{}"


def test_cli_reads_field_mapping_config(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        (
            "no_color = true\n"
            "[fields]\n"
            "timestamp = \"ts\"\n"
            "level = \"severity\"\n"
            "path = \"route\"\n"
            "query = \"q\"\n"
            "top_k = \"k\"\n"
            "function = \"fn\"\n"
            "line = \"ln\"\n"
            "message_fields = [\"text\"]\n"
        ),
        encoding="utf-8",
    )
    data = (
        '{"ts":"2026-02-19T10:12:05Z","severity":"warning","route":"/search",'
        '"q":"timing","k":7,"fn":"handler","ln":21,"text":"configured"}\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert (
        proc.stdout.strip()
        == "[10:12:05][WARNING][handler:21] configured"
    )


def test_cli_reads_color_scheme_preset_from_config(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        'color_scheme = "dracula"\n',
        encoding="utf-8",
    )
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\033[95m[10:12:05][INFO]\033[0m" in proc.stdout
    assert "\033[96mhello\033[0m" in proc.stdout


def test_cli_allows_custom_color_overrides(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        'color_scheme = "dracula"\nmetadata_color = "green"\nmessage_color = "blue"\n',
        encoding="utf-8",
    )
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\033[32m[10:12:05][INFO]\033[0m" in proc.stdout
    assert "\033[34mhello\033[0m" in proc.stdout


def test_cli_reads_theme_from_config(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        'theme = "nord"\n',
        encoding="utf-8",
    )
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\033[94m[10:12:05][INFO]\033[0m" in proc.stdout
    assert "\033[37mhello\033[0m" in proc.stdout


def test_cli_theme_overrides_color_scheme(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        'color_scheme = "dracula"\ntheme = "monokai"\n',
        encoding="utf-8",
    )
    data = '{"event":"hello","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\033[32m[10:12:05][INFO]\033[0m" in proc.stdout
    assert "\033[93mhello\033[0m" in proc.stdout
