"""Tests for output rendering with CJK support."""

import json
from board_md.render import render_table, render_json, render_detail


SAMPLE_TASKS = [
    {"id": "00000001", "title": "Build engine", "status": "in-progress",
     "column": "GAIA", "priority": "high", "milestone": "2026-04-01"},
    {"id": "00000002", "title": "Fix bug", "status": "todo",
     "column": "Local", "priority": "low", "milestone": ""},
]


def test_render_table_has_headers():
    output = render_table(SAMPLE_TASKS)
    assert "ID" in output
    assert "TITLE" in output
    assert "STATUS" in output


def test_render_table_has_data():
    output = render_table(SAMPLE_TASKS)
    assert "Build engine" in output
    assert "Fix bug" in output
    assert "in-progress" in output


def test_render_table_empty():
    output = render_table([])
    assert "No tasks" in output


def test_render_table_alignment():
    """Columns should be aligned (separator line exists)."""
    output = render_table(SAMPLE_TASKS)
    lines = output.strip().split("\n")
    assert len(lines) >= 3
    assert "─" in lines[1]


def test_render_table_cjk():
    """CJK characters should not break alignment."""
    tasks = [
        {"id": "00000001", "title": "训练模型", "status": "in-progress",
         "column": "GAIA", "priority": "high", "milestone": ""},
        {"id": "00000002", "title": "Build API", "status": "todo",
         "column": "Local", "priority": "low", "milestone": ""},
    ]
    output = render_table(tasks)
    lines = output.strip().split("\n")
    # All separator segments should be present
    assert lines[1].count("┼") == 5  # 6 columns = 5 separators


def test_render_json_valid():
    output = render_json(SAMPLE_TASKS)
    parsed = json.loads(output)
    assert len(parsed) == 2
    assert parsed[0]["id"] == "00000001"


def test_render_json_excludes_body():
    tasks = [{"id": "00000001", "title": "X", "body": "some notes"}]
    output = render_json(tasks)
    parsed = json.loads(output)
    assert "body" not in parsed[0]


def test_render_detail():
    task = {
        "id": "00000001",
        "title": "Build engine",
        "description": "Core recommendation engine",
        "status": "in-progress",
        "column": "GAIA",
        "priority": "high",
        "created": "2026-03-20",
        "updated": "2026-03-20",
        "body": "## Notes\n\nSome context here.",
    }
    output = render_detail(task)
    assert "Build engine" in output
    assert "in-progress" in output
    assert "Core recommendation engine" in output
    assert "Some context here." in output


def test_render_detail_skips_empty_fields():
    task = {"id": "00000001", "title": "Minimal", "status": "backlog"}
    output = render_detail(task)
    assert "host" not in output
    assert "milestone" not in output
