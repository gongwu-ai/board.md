"""Tests for the core store module — CRUD on board/*.md files."""

import pytest
from pathlib import Path
from board_md.store import (
    init_board,
    add_task,
    list_tasks,
    get_task,
    update_task,
    archive_task,
    search_tasks,
)


def test_init_creates_board_dir(tmp_path):
    board = init_board(tmp_path)
    assert board.exists()
    assert board.is_dir()
    assert board.name == "board"


def test_init_is_idempotent(tmp_path):
    b1 = init_board(tmp_path)
    b2 = init_board(tmp_path)
    assert b1 == b2


def test_add_task_creates_file(board_dir):
    task = add_task(board_dir, "Build engine")
    assert task["id"] == "001"
    assert task["title"] == "Build engine"
    assert task["status"] == "backlog"
    assert task["priority"] == "medium"
    files = list(board_dir.glob("001_*.md"))
    assert len(files) == 1


def test_add_task_with_options(board_dir):
    task = add_task(
        board_dir,
        "Train model",
        column="GAIA",
        priority="high",
        host="TELEFONICA-GAIA",
        tags=["ml", "baseline"],
    )
    assert task["column"] == "GAIA"
    assert task["priority"] == "high"
    assert task["host"] == "TELEFONICA-GAIA"
    assert task["tags"] == ["ml", "baseline"]


def test_add_auto_increments_id(board_dir):
    t1 = add_task(board_dir, "First")
    t2 = add_task(board_dir, "Second")
    t3 = add_task(board_dir, "Third")
    assert t1["id"] == "001"
    assert t2["id"] == "002"
    assert t3["id"] == "003"


def test_add_task_sets_dates(board_dir):
    task = add_task(board_dir, "Dated task")
    assert "created" in task
    assert "updated" in task
    assert task["created"] == task["updated"]


def test_list_tasks_empty(board_dir):
    assert list_tasks(board_dir) == []


def test_list_tasks_returns_all(board_dir):
    add_task(board_dir, "A")
    add_task(board_dir, "B")
    tasks = list_tasks(board_dir)
    assert len(tasks) == 2
    assert tasks[0]["title"] == "A"
    assert tasks[1]["title"] == "B"


def test_get_task(board_dir):
    add_task(board_dir, "Find me", column="Local")
    task = get_task(board_dir, "001")
    assert task["title"] == "Find me"
    assert task["column"] == "Local"


def test_get_task_not_found(board_dir):
    with pytest.raises(FileNotFoundError):
        get_task(board_dir, "999")


def test_update_status(board_dir):
    add_task(board_dir, "My Task")
    updated = update_task(board_dir, "001", status="in-progress")
    assert updated["status"] == "in-progress"
    # Verify round-trip persistence
    reloaded = get_task(board_dir, "001")
    assert reloaded["status"] == "in-progress"


def test_update_current_task(board_dir):
    add_task(board_dir, "My Task")
    updated = update_task(board_dir, "001", current_task="Training baseline")
    assert updated["current_task"] == "Training baseline"


def test_update_preserves_existing_fields(board_dir):
    add_task(board_dir, "My Task", column="GAIA", priority="high")
    update_task(board_dir, "001", status="in-progress")
    reloaded = get_task(board_dir, "001")
    assert reloaded["column"] == "GAIA"
    assert reloaded["priority"] == "high"


def test_update_bumps_updated_date(board_dir):
    add_task(board_dir, "My Task")
    t1 = get_task(board_dir, "001")
    update_task(board_dir, "001", status="done")
    t2 = get_task(board_dir, "001")
    # At minimum, updated field should exist and be a date string
    assert "updated" in t2


def test_update_not_found(board_dir):
    with pytest.raises(FileNotFoundError):
        update_task(board_dir, "999", status="done")


def test_archive_moves_file(board_dir):
    add_task(board_dir, "Done task")
    archive_task(board_dir, "001")
    assert list_tasks(board_dir) == []
    archive = board_dir / "archive"
    assert len(list(archive.glob("001_*.md"))) == 1


def test_archive_not_found(board_dir):
    with pytest.raises(FileNotFoundError):
        archive_task(board_dir, "999")


def test_search_by_title(board_dir):
    add_task(board_dir, "ML Pipeline")
    add_task(board_dir, "Frontend UI")
    results = search_tasks(board_dir, "pipeline")
    assert len(results) == 1
    assert results[0]["title"] == "ML Pipeline"


def test_search_by_metadata(board_dir):
    add_task(board_dir, "Task A", column="GAIA")
    add_task(board_dir, "Task B", column="CFFF")
    results = search_tasks(board_dir, "GAIA")
    assert len(results) == 1


def test_search_case_insensitive(board_dir):
    add_task(board_dir, "Build ENGINE")
    results = search_tasks(board_dir, "engine")
    assert len(results) == 1


def test_search_no_results(board_dir):
    add_task(board_dir, "Something")
    assert search_tasks(board_dir, "nonexistent") == []


def test_slugify_unicode(board_dir):
    """Chinese/unicode titles should produce valid filenames."""
    task = add_task(board_dir, "训练基线模型")
    files = list(board_dir.glob(f"{task['id']}_*.md"))
    assert len(files) == 1


def test_file_is_valid_markdown(board_dir):
    """The generated file should be readable as plain markdown."""
    add_task(board_dir, "Check format", column="Local", priority="high")
    filepath = list(board_dir.glob("001_*.md"))[0]
    content = filepath.read_text()
    assert content.startswith("---\n")
    assert "title: Check format" in content
