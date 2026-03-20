"""board.md CLI entry point — built with typer."""

# NOTE: Do NOT use `from __future__ import annotations` here.
# Typer inspects type annotations at runtime for CLI argument generation.
# PEP 563 deferred annotations break this on Python 3.9.

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

import typer

from board_md.store import (
    init_board, add_task, list_tasks, get_task,
    update_task, archive_task, search_tasks,
)
from board_md.render import render_table, render_json, render_detail
from board_md import notify
from board_md.skills import inject_skills, clean_skills, TOOL_CONFIGS

app = typer.Typer(
    name="board",
    help="board.md — Markdown-native project board.",
    no_args_is_help=True,
)


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


def _resolve_task(board: Path, task_id: str) -> dict:
    """Get task, handling not-found and ambiguous ID errors."""
    try:
        return get_task(board, task_id)
    except FileNotFoundError:
        typer.echo(f"Task {task_id} not found.", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


@app.command()
def init(
    skip_skills: bool = typer.Option(False, "--skip-skills", help="Don't generate agent skill files"),
    tools: Optional[List[str]] = typer.Option(None, "--tool", help=f"Agent tools to generate for (default: all). Choices: {', '.join(TOOL_CONFIGS)}"),
):
    """Initialize a board in the current directory.

    Creates board/ for task files and writes SKILL.md into each AI tool's
    native discovery directory (.claude/skills/, .codex/skills/, etc.).
    """
    cwd = Path.cwd()
    board = init_board(cwd)
    typer.echo(f"Initialized board at {board}/")

    if not skip_skills:
        created = inject_skills(cwd, tools=tools)
        for path in created:
            typer.echo(f"  wrote {path}")
        typer.echo(f"Agent skills injected for {len(created)} tool(s).")


@app.command("add")
def add_cmd(
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "-d", "--description", help="One-line description"),
    status: str = typer.Option("backlog", "-s", "--status", help="Task status"),
    column: str = typer.Option("", "-c", "--column", help="Board column"),
    priority: str = typer.Option("medium", "-p", "--priority", help="Priority (low/medium/high/critical)"),
    host: str = typer.Option("", help="Associated host"),
    path: str = typer.Option("", help="Project path"),
    milestone: str = typer.Option("", help="Milestone date (YYYY-MM-DD)"),
    milestone_name: str = typer.Option("", "--milestone-name", help="Milestone description"),
    tag: Optional[List[str]] = typer.Option(None, "-t", "--tag", help="Tags (repeatable)"),
    slug: Optional[str] = typer.Option(None, "--slug", help="Custom filename slug"),
):
    """Add a new task."""
    board = _find_board()
    if not board.exists():
        board.mkdir(parents=True)
    task = add_task(
        board, title,
        description=description, status=status, column=column,
        priority=priority, host=host, path=path, milestone=milestone,
        milestone_name=milestone_name,
        tags=tag if tag else None,
        slug=slug,
    )
    typer.echo(f"Created task {task['id']}: {title}")


@app.command("list")
def list_cmd(
    as_json: bool = typer.Option(False, "--json", help="JSON output"),
    status: Optional[str] = typer.Option(None, "-s", "--status", help="Filter by status"),
    column: Optional[str] = typer.Option(None, "-c", "--column", help="Filter by column"),
):
    """List all tasks."""
    board = _find_board()
    if not board.exists():
        typer.echo("No board found. Run `board init` first.", err=True)
        raise typer.Exit(1)

    tasks = list_tasks(board)
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    if column:
        tasks = [t for t in tasks if t.get("column") == column]

    if as_json:
        typer.echo(render_json(tasks))
    else:
        typer.echo(render_table(tasks))


@app.command("show")
def show_cmd(
    task_id: str = typer.Argument(..., help="Task ID (or prefix)"),
):
    """Show task details."""
    board = _find_board()
    task = _resolve_task(board, task_id)
    typer.echo(render_detail(task))


@app.command("update")
def update_cmd(
    task_id: str = typer.Argument(..., help="Task ID (or prefix)"),
    status: Optional[str] = typer.Option(None, "-s", "--status", help="New status"),
    current_task: Optional[str] = typer.Option(None, "-t", "--task", help="Current task description"),
    column: Optional[str] = typer.Option(None, "-c", "--column", help="Move to column"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="Set priority"),
    description: Optional[str] = typer.Option(None, "-d", "--description", help="Update description"),
    milestone: Optional[str] = typer.Option(None, "--milestone", help="Milestone date"),
    milestone_name: Optional[str] = typer.Option(None, "--milestone-name", help="Milestone description"),
):
    """Update a task."""
    board = _find_board()
    kwargs = {}
    if status is not None:
        kwargs["status"] = status
    if current_task is not None:
        kwargs["current_task"] = current_task
    if column is not None:
        kwargs["column"] = column
    if priority is not None:
        kwargs["priority"] = priority
    if description is not None:
        kwargs["description"] = description
    if milestone is not None:
        kwargs["milestone"] = milestone
    if milestone_name is not None:
        kwargs["milestone_name"] = milestone_name

    if not kwargs:
        typer.echo("Nothing to update. Use --help for options.", err=True)
        raise typer.Exit(1)

    try:
        task = update_task(board, task_id, **kwargs)
        typer.echo(f"Updated task {task_id}: {task['title']}")
    except FileNotFoundError:
        typer.echo(f"Task {task_id} not found.", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


@app.command()
def archive(
    task_id: str = typer.Argument(..., help="Task ID (or prefix)"),
):
    """Archive a task."""
    board = _find_board()
    try:
        archive_task(board, task_id)
        typer.echo(f"Archived task {task_id}")
    except FileNotFoundError:
        typer.echo(f"Task {task_id} not found.", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search keyword"),
):
    """Search tasks by keyword."""
    board = _find_board()
    results = search_tasks(board, query)
    if results:
        typer.echo(render_table(results))
    else:
        typer.echo("No matching tasks found.")


@app.command()
def remind(
    task_id: str = typer.Argument(..., help="Task ID (or prefix)"),
    when: str = typer.Argument(..., help="Delay (30m, 2h) or absolute time"),
    message: Optional[str] = typer.Argument(None, help="Custom message"),
):
    """Set a reminder for a task via configured notification backend."""
    config = _load_config()
    backend = config.get("notify_backend", "ntfy")

    if backend == "ntfy" and not config.get("ntfy_topic"):
        typer.echo(
            "No ntfy topic configured. Run: board config ntfy-topic <your-topic>",
            err=True,
        )
        raise typer.Exit(1)
    if backend == "feishu" and not config.get("feishu_webhook"):
        typer.echo(
            "No feishu webhook configured. Run: board config feishu-webhook <url>",
            err=True,
        )
        raise typer.Exit(1)

    board = _find_board()
    task = _resolve_task(board, task_id)

    msg = message or f"Reminder: {task['title']}"
    ok = notify.send(config, msg, title=f"board.md [{task_id}]", delay=when)
    if ok:
        typer.echo(f"Reminder set: {when} → {msg}")
    else:
        typer.echo("Failed to send notification.", err=True)
        raise typer.Exit(1)


@app.command()
def config(
    key: str = typer.Argument(..., help="Config key (e.g., ntfy-topic, feishu-webhook, notify-backend)"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set board configuration."""
    board = _find_board()
    config_file = board.parent / ".board.json"

    cfg = {}
    if config_file.exists():
        cfg = json.loads(config_file.read_text())

    key = key.replace("-", "_")
    cfg[key] = value
    config_file.write_text(json.dumps(cfg, indent=2) + "\n")
    typer.echo(f"Set {key} = {value}")
