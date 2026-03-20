"""board.md CLI entry point."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from board_md.store import (
    init_board, add_task, list_tasks, get_task,
    update_task, archive_task, search_tasks,
)
from board_md.render import render_table, render_json, render_detail
from board_md.notify import send_notification


def _find_board() -> Path:
    """Walk up from cwd to find a board/ directory with task files."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        board = parent / "board"
        if board.is_dir() and any(board.glob("[0-9]*_*.md")):
            return board
    return cwd / "board"


def _load_config() -> dict:
    """Load .board.json from the project root (board's parent)."""
    board = _find_board()
    config_file = board.parent / ".board.json"
    if config_file.exists():
        return json.loads(config_file.read_text())
    return {}


@click.group()
@click.version_option(package_name="board-md")
def cli():
    """board.md — Markdown-native project board."""
    pass


@cli.command()
def init():
    """Initialize a board in the current directory."""
    board = init_board(Path.cwd())
    click.echo(f"Initialized board at {board}/")


@cli.command("add")
@click.argument("title")
@click.option("-s", "--status", default="backlog", help="Task status")
@click.option("-c", "--column", default="", help="Board column")
@click.option("-p", "--priority", default="medium", help="Priority (low/medium/high/critical)")
@click.option("--host", default="", help="Associated host")
@click.option("--path", default="", help="Project path")
@click.option("--milestone", default="", help="Milestone date (YYYY-MM-DD)")
@click.option("--milestone-name", default="", help="Milestone description")
@click.option("-t", "--tag", multiple=True, help="Tags (repeatable)")
def add_cmd(title, status, column, priority, host, path, milestone, milestone_name, tag):
    """Add a new task."""
    board = _find_board()
    if not board.exists():
        board.mkdir(parents=True)
    task = add_task(
        board, title,
        status=status, column=column, priority=priority,
        host=host, path=path, milestone=milestone,
        milestone_name=milestone_name,
        tags=list(tag) if tag else None,
    )
    click.echo(f"Created task {task['id']}: {title}")


@cli.command("list")
@click.option("--json", "as_json", is_flag=True, help="JSON output")
@click.option("-s", "--status", help="Filter by status")
@click.option("-c", "--column", help="Filter by column")
def list_cmd(as_json, status, column):
    """List all tasks."""
    board = _find_board()
    if not board.exists():
        click.echo("No board found. Run `board init` first.", err=True)
        sys.exit(1)

    tasks = list_tasks(board)
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    if column:
        tasks = [t for t in tasks if t.get("column") == column]

    if as_json:
        click.echo(render_json(tasks))
    else:
        click.echo(render_table(tasks))


@cli.command("show")
@click.argument("task_id")
def show_cmd(task_id):
    """Show task details."""
    board = _find_board()
    try:
        task = get_task(board, task_id)
        click.echo(render_detail(task))
    except FileNotFoundError:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)


@cli.command("update")
@click.argument("task_id")
@click.option("-s", "--status", help="New status")
@click.option("-t", "--task", "current_task", help="Current task description")
@click.option("-c", "--column", help="Move to column")
@click.option("-p", "--priority", help="Set priority")
@click.option("--milestone", help="Milestone date")
@click.option("--milestone-name", help="Milestone description")
def update_cmd(task_id, status, current_task, column, priority, milestone, milestone_name):
    """Update a task."""
    board = _find_board()
    kwargs = {}
    if status:
        kwargs["status"] = status
    if current_task:
        kwargs["current_task"] = current_task
    if column:
        kwargs["column"] = column
    if priority:
        kwargs["priority"] = priority
    if milestone:
        kwargs["milestone"] = milestone
    if milestone_name:
        kwargs["milestone_name"] = milestone_name

    if not kwargs:
        click.echo("Nothing to update. Use --help for options.", err=True)
        sys.exit(1)

    try:
        task = update_task(board, task_id, **kwargs)
        click.echo(f"Updated task {task_id}: {task['title']}")
    except FileNotFoundError:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)


@cli.command()
@click.argument("task_id")
def archive(task_id):
    """Archive a task."""
    board = _find_board()
    try:
        archive_task(board, task_id)
        click.echo(f"Archived task {task_id}")
    except FileNotFoundError:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)


@cli.command()
@click.argument("query")
def search(query):
    """Search tasks by keyword."""
    board = _find_board()
    results = search_tasks(board, query)
    if results:
        click.echo(render_table(results))
    else:
        click.echo("No matching tasks found.")


@cli.command()
@click.argument("task_id")
@click.argument("when")
@click.argument("message", required=False)
def remind(task_id, when, message):
    """Set a reminder for a task via ntfy.sh.

    WHEN can be a delay (30m, 2h) or an absolute time (2026-04-01T09:00).
    """
    config = _load_config()
    topic = config.get("ntfy_topic")
    if not topic:
        click.echo(
            "No ntfy topic configured. Run: board config ntfy-topic <your-topic>",
            err=True,
        )
        sys.exit(1)

    board = _find_board()
    try:
        task = get_task(board, task_id)
    except FileNotFoundError:
        click.echo(f"Task {task_id} not found.", err=True)
        sys.exit(1)

    msg = message or f"Reminder: {task['title']}"
    ok = send_notification(topic, msg, title=f"board.md [{task_id}]", delay=when)
    if ok:
        click.echo(f"Reminder set: {when} → {msg}")
    else:
        click.echo("Failed to send notification.", err=True)
        sys.exit(1)


@cli.command()
@click.argument("key")
@click.argument("value")
def config(key, value):
    """Set board configuration (e.g., ntfy-topic)."""
    board = _find_board()
    config_file = board.parent / ".board.json"

    cfg = {}
    if config_file.exists():
        cfg = json.loads(config_file.read_text())

    key = key.replace("-", "_")
    cfg[key] = value
    config_file.write_text(json.dumps(cfg, indent=2) + "\n")
    click.echo(f"Set {key} = {value}")
