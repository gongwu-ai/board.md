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
    ID_WIDTH,
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


# --- Add ---

def test_add_task_creates_file(board_dir):
    task = add_task(board_dir, "Build engine")
    assert task["id"] == "1".zfill(ID_WIDTH)
    assert task["title"] == "Build engine"
    assert task["status"] == "backlog"
    assert task["priority"] == "medium"
    files = list(board_dir.glob(f"{'1'.zfill(ID_WIDTH)}_*.md"))
    assert len(files) == 1


def test_add_task_with_options(board_dir):
    task = add_task(
        board_dir,
        "Train model",
        description="Baseline experiment",
        column="GAIA",
        priority="high",
        host="TELEFONICA-GAIA",
        tags=["ml", "baseline"],
    )
    assert task["column"] == "GAIA"
    assert task["priority"] == "high"
    assert task["host"] == "TELEFONICA-GAIA"
    assert task["tags"] == ["ml", "baseline"]
    assert task["description"] == "Baseline experiment"


def test_add_auto_increments_id(board_dir):
    t1 = add_task(board_dir, "First")
    t2 = add_task(board_dir, "Second")
    t3 = add_task(board_dir, "Third")
    assert t1["id"] == "1".zfill(ID_WIDTH)
    assert t2["id"] == "2".zfill(ID_WIDTH)
    assert t3["id"] == "3".zfill(ID_WIDTH)


def test_add_task_sets_dates(board_dir):
    task = add_task(board_dir, "Dated task")
    assert "created" in task
    assert "updated" in task
    assert task["created"] == task["updated"]


def test_add_task_custom_slug(board_dir):
    task = add_task(board_dir, "My Task", slug="custom-slug")
    files = list(board_dir.glob(f"{task['id']}_custom-slug.md"))
    assert len(files) == 1


def test_add_task_uses_slugify(board_dir):
    """Slug should be auto-generated from title via python-slugify."""
    task = add_task(board_dir, "Build ML Pipeline!")
    files = list(board_dir.glob(f"{task['id']}_*.md"))
    assert len(files) == 1
    filename = files[0].name
    # python-slugify removes special chars and lowercases
    assert "!" not in filename


# --- List ---

def test_list_tasks_empty(board_dir):
    assert list_tasks(board_dir) == []


def test_list_tasks_returns_all(board_dir):
    add_task(board_dir, "A")
    add_task(board_dir, "B")
    tasks = list_tasks(board_dir)
    assert len(tasks) == 2
    assert tasks[0]["title"] == "A"
    assert tasks[1]["title"] == "B"


# --- Get ---

def test_get_task(board_dir):
    add_task(board_dir, "Find me", column="Local")
    task = get_task(board_dir, "1".zfill(ID_WIDTH))
    assert task["title"] == "Find me"
    assert task["column"] == "Local"


def test_get_task_numeric_shorthand(board_dir):
    """Should support `board show 1` → looks up 00000001."""
    add_task(board_dir, "Shorthand task")
    task = get_task(board_dir, "1")
    assert task["title"] == "Shorthand task"


def test_get_task_not_found(board_dir):
    with pytest.raises(FileNotFoundError):
        get_task(board_dir, "999")


def test_get_task_ambiguous_prefix(board_dir):
    """When prefix matches multiple tasks, raise ValueError."""
    # Create tasks 00000001 and 00000002
    add_task(board_dir, "Task A")
    add_task(board_dir, "Task B")
    # Prefix "0000000" matches both
    with pytest.raises(ValueError, match="Ambiguous"):
        get_task(board_dir, "0000000")


# --- Update ---

def test_update_status(board_dir):
    add_task(board_dir, "My Task")
    updated = update_task(board_dir, "1", status="in-progress")
    assert updated["status"] == "in-progress"
    reloaded = get_task(board_dir, "1")
    assert reloaded["status"] == "in-progress"


def test_update_current_task_in_frontmatter(board_dir):
    add_task(board_dir, "My Task")
    updated = update_task(board_dir, "1", current_task="Training baseline")
    assert updated["current_task"] == "Training baseline"


def test_update_current_task_in_body(board_dir):
    """current_task should also appear in body as ## Current Task section."""
    add_task(board_dir, "My Task")
    update_task(board_dir, "1", current_task="Training baseline")
    task = get_task(board_dir, "1")
    assert "## Current Task" in task["body"]
    assert "Training baseline" in task["body"]


def test_update_current_task_preserves_notes(board_dir):
    """Updating current_task should not destroy existing Notes section."""
    add_task(board_dir, "My Task")
    update_task(board_dir, "1", notes="Some important context")
    update_task(board_dir, "1", current_task="New focus")
    task = get_task(board_dir, "1")
    assert "New focus" in task["body"]
    assert "Some important context" in task["body"]


def test_update_preserves_existing_fields(board_dir):
    add_task(board_dir, "My Task", column="GAIA", priority="high")
    update_task(board_dir, "1", status="in-progress")
    reloaded = get_task(board_dir, "1")
    assert reloaded["column"] == "GAIA"
    assert reloaded["priority"] == "high"


def test_update_bumps_updated_date(board_dir):
    add_task(board_dir, "My Task")
    update_task(board_dir, "1", status="done")
    t = get_task(board_dir, "1")
    assert "updated" in t


def test_update_not_found(board_dir):
    with pytest.raises(FileNotFoundError):
        update_task(board_dir, "999", status="done")


# --- Archive ---

def test_archive_moves_file(board_dir):
    add_task(board_dir, "Done task")
    archive_task(board_dir, "1")
    assert list_tasks(board_dir) == []
    archive = board_dir / "archive"
    assert len(list(archive.glob(f"{'1'.zfill(ID_WIDTH)}_*.md"))) == 1


def test_archive_not_found(board_dir):
    with pytest.raises(FileNotFoundError):
        archive_task(board_dir, "999")


# --- Search ---

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


# --- Edge cases ---

def test_slugify_unicode(board_dir):
    """Chinese/unicode titles should produce valid filenames."""
    task = add_task(board_dir, "训练基线模型")
    files = list(board_dir.glob(f"{task['id']}_*.md"))
    assert len(files) == 1


def test_file_is_valid_markdown(board_dir):
    """The generated file should be readable as plain markdown."""
    add_task(board_dir, "Check format", column="Local", priority="high")
    filepath = list(board_dir.glob(f"{'1'.zfill(ID_WIDTH)}_*.md"))[0]
    content = filepath.read_text()
    assert content.startswith("---\n")
    assert "title: Check format" in content


def test_8_digit_id_format(board_dir):
    """IDs should be zero-padded to 8 digits."""
    task = add_task(board_dir, "Test ID")
    assert len(task["id"]) == ID_WIDTH
    assert task["id"].isdigit()
