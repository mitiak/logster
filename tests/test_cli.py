import subprocess
import sys
from pathlib import Path

from logster import cli
from logster import __version__


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


def test_cli_prints_version() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert proc.stdout.strip() == f"logster {__version__}"
    assert proc.stderr == ""


def test_cli_formats_json_payloads_from_docker_compose_logs(tmp_path: Path):
    compose_json_line = (
        'cdrmind-raggy          | {"method":"GET","status_code":200,"latency_ms":1.64,'
        '"file":"health.py","function":"health_check","line":10,'
        '"event":"request_completed","request_id":"4f7ed318-e34f-44b8-a22b-cb9c8ab523c3",'
        '"path":"/health","timestamp":"2026-02-26T11:04:00.757676Z","level":"info"}'
    )
    compose_plain_line = (
        'cdrmind-raggy          | INFO:     127.0.0.1:58920 - "GET /health HTTP/1.1" 200 OK'
    )
    data = f"{compose_json_line}\n{compose_plain_line}\n"

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
        == "cdrmind-raggy          | [11:04:00][INFO][health.py][health_check:10] request_completed"
    )
    assert out_lines[1] == compose_plain_line


def test_cli_highlights_warning_and_error_in_passthrough_lines(tmp_path: Path):
    data = (
        'cdrmind-taskonaut-soc  | [13:33:49][WARNING][service.py] tool.execute.failed\n'
        'cdrmind-api            | [13:33:49][ERROR] agents.summarize.failed\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\033[33mWARNING\033[0m" in proc.stdout
    assert "\033[31mERROR\033[0m" in proc.stdout


def test_cli_does_not_highlight_passthrough_levels_with_no_color(tmp_path: Path):
    data = 'cdrmind-api            | [13:33:49][ERROR] agents.summarize.failed\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli", "--no-color"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert proc.stdout.strip() == data.strip()
    assert "\033[" not in proc.stdout


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


def test_cli_verbose_flag_enables_verbose_output(tmp_path: Path):
    data = '{"event":"hello world","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli", "--no-color", "--verbose"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert proc.stdout.strip() == "[10:12:05][INFO] hello world\n{}"


def test_cli_verbose_flag_applies_to_compose_prefixed_json(tmp_path: Path):
    data = (
        'cdrmind-raggy          | {"event":"hello world","timestamp":"2026-02-19T10:12:05Z","level":"info"}\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli", "--no-color", "--verbose"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert (
        proc.stdout.strip()
        == 'cdrmind-raggy          | [10:12:05][INFO] hello world\ncdrmind-raggy          | {}'
    )


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


def test_cli_reads_main_line_fields_config(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        (
            "no_color = true\n"
            'output_style = "verbose"\n'
            "[fields]\n"
            'main_line_fields = ["timestamp", "path", "message"]\n'
        ),
        encoding="utf-8",
    )
    data = (
        '{"event":"configured","timestamp":"2026-02-19T10:12:05Z","level":"warning",'
        '"path":"/query","request_id":"abc"}\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert proc.stdout.strip() == '[10:12:05]["/query"] configured\n{"level":"warning","request_id":"abc"}'


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

    assert "\033[95m[10:12:05]\033[0m" in proc.stdout
    assert "\033[95m[INFO]\033[0m" in proc.stdout
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

    assert "\033[32m[10:12:05]\033[0m" in proc.stdout
    assert "\033[32m[INFO]\033[0m" in proc.stdout
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

    assert "\033[94m[10:12:05]\033[0m" in proc.stdout
    assert "\033[94m[INFO]\033[0m" in proc.stdout
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

    assert "\033[32m[10:12:05]\033[0m" in proc.stdout
    assert "\033[32m[INFO]\033[0m" in proc.stdout
    assert "\033[93mhello\033[0m" in proc.stdout


def test_cli_allows_granular_color_configuration(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        (
            'time_color = "red"\n'
            'level_color = "green"\n'
            'file_color = "blue"\n'
            'origin_color = "magenta"\n'
            'message_color = "yellow"\n'
            'output_style = "verbose"\n'
            'verbose_metadata_key_color = "bright_cyan"\n'
            'verbose_metadata_value_color = "bright_white"\n'
            'verbose_metadata_punctuation_color = "bright_black"\n'
        ),
        encoding="utf-8",
    )
    data = (
        '{"event":"embedding_text_started","timestamp":"2026-02-19T10:12:05Z",'
        '"level":"info","file":"embedding.py","function":"embed_text","line":24,'
        '"path":"/embed"}\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    assert "\033[31m[10:12:05]\033[0m" in proc.stdout
    assert "\033[32m[INFO]\033[0m" in proc.stdout
    assert "\033[34m[embedding.py]\033[0m" in proc.stdout
    assert "\033[35m[embed_text:24]\033[0m" in proc.stdout
    assert "\033[33membedding_text_started\033[0m" in proc.stdout
    assert "\033[2m\033[96m\"path\"\033[0m" in proc.stdout
    assert "\033[2m\033[97m\"/embed\"\033[0m" in proc.stdout
    assert "\033[2m\033[90m{\033[0m" in proc.stdout


def test_cli_supports_monokai_github_meta_scheme(tmp_path: Path):
    (tmp_path / "logster.toml").write_text(
        'color_scheme = "monokai-github-meta"\noutput_style = "verbose"\n',
        encoding="utf-8",
    )
    data = (
        '{"event":"embedding_text_started","timestamp":"2026-02-19T10:12:05Z",'
        '"level":"info","file":"embedding.py","function":"embed_text","line":24,'
        '"path":"/embed"}\n'
    )

    proc = subprocess.run(
        [sys.executable, "-m", "logster.cli"],
        input=data,
        capture_output=True,
        text=True,
        check=True,
        cwd=tmp_path,
    )

    # Main line follows monokai.
    assert "\033[32m[10:12:05]\033[0m" in proc.stdout
    assert "\033[32m[INFO]\033[0m" in proc.stdout
    assert "\033[93membedding_text_started\033[0m" in proc.stdout
    # Verbose metadata follows github-dark.
    assert "\033[2m\033[90m\"path\"\033[0m" in proc.stdout
    assert "\033[2m\033[37m\"/embed\"\033[0m" in proc.stdout
