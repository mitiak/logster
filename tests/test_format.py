from logster.config import FieldMapping
from logster.format import format_record, format_time


def test_format_record_example():
    rec = {
        "query": "timing",
        "top_k": 5,
        "event": "query_endpoint_started",
        "request_id": "5342fb6b-8ff0-4d9d-84a5-1f6b0e098528",
        "path": "/query",
        "timestamp": "2026-02-19T10:12:05.497600Z",
        "level": "info",
        "file": "query.py",
        "function": "query",
        "line": 17,
    }
    got = format_record(rec, use_color=False)
    assert (
        got
        == '[10:12:05][INFO][/query][q="timing"][top_k=5][query:17] query_endpoint_started'
    )


def test_missing_query_omits_query_segment():
    rec = {
        "event": "started",
        "timestamp": "2026-02-19T10:12:05Z",
        "level": "info",
        "path": "/query",
        "top_k": 5,
        "function": "query",
        "line": 17,
    }
    got = format_record(rec, use_color=False)
    assert '[q="' not in got


def test_missing_timestamp_omits_time_segment():
    rec = {"event": "started", "level": "info", "path": "/query"}
    got = format_record(rec, use_color=False)
    assert not got.startswith("[10:")
    assert got == "[INFO][/query] started"


def test_missing_line_omits_location_segment():
    rec = {"event": "started", "function": "query"}
    got = format_record(rec, use_color=False)
    assert "[query:" not in got
    assert got == "started"


def test_timestamp_truncation():
    assert format_time("2026-02-19T10:12:05.497600Z") == "10:12:05"


def test_color_scheme_uses_distinct_metadata_and_message_colors():
    rec = {"level": "info", "event": "started"}
    got = format_record(rec)
    assert "\033[36m[INFO]\033[0m" in got
    assert "\033[97mstarted\033[0m" in got


def test_verbose_output_style():
    rec = {
        "event": "query_endpoint_started",
        "path": "/query",
        "timestamp": "2026-02-19T10:12:05.497600Z",
        "level": "info",
    }
    got = format_record(rec, use_color=False, output_style="verbose")
    assert got == 'time=10:12:05 level=INFO path=/query msg="query_endpoint_started"'


def test_custom_field_mapping():
    rec = {
        "ts": "2026-02-19T10:12:05Z",
        "severity": "warning",
        "route": "/search",
        "q": "timing",
        "k": 3,
        "fn": "query",
        "ln": 11,
        "text": "hello",
    }
    got = format_record(
        rec,
        use_color=False,
        fields=FieldMapping(
            timestamp="ts",
            level="severity",
            path="route",
            query="q",
            top_k="k",
            function="fn",
            line="ln",
            message_fields=("text",),
        ),
    )
    assert got == '[10:12:05][WARNING][/search][q="timing"][top_k=3][query:11] hello'
