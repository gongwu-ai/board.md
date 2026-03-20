"""Read/write board/*.md task files."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter


def init_board(project_dir: Path) -> Path:
    """Create board/ directory in project_dir. Returns the board path."""
    board = project_dir / "board"
    board.mkdir(exist_ok=True)
    return board


def _next_id(board_dir: Path) -> str:
    """Find the next available task ID (zero-padded 3 digits)."""
    existing = [f.name for f in board_dir.glob("[0-9]*_*.md")]
    if not existing:
        return "001"
    max_id = max(int(f.split("_")[0]) for f in existing)
    return f"{max_id + 1:03d}"


def _slugify(title: str) -> str:
    """Convert title to a filesystem-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "_", slug).strip("_")
    return slug[:40] if slug else "task"


def _task_file(board_dir: Path, task_id: str) -> Optional[Path]:
    """Find the file for a given task ID."""
    matches = list(board_dir.glob(f"{task_id}_*.md"))
    return matches[0] if matches else None


def add_task(
    board_dir: Path,
    title: str,
    *,
    status: str = "backlog",
    column: str = "",
    priority: str = "medium",
    host: str = "",
    path: str = "",
    milestone: str = "",
    milestone_name: str = "",
    tags: Optional[List[str]] = None,
) -> Dict:
    """Create a new task file. Returns the task metadata dict."""
    task_id = _next_id(board_dir)
    slug = _slugify(title)
    today = date.today().isoformat()

    metadata = {
        "title": title,
        "id": task_id,
        "status": status,
        "column": column,
        "priority": priority,
        "created": today,
        "updated": today,
    }
    if host:
        metadata["host"] = host
    if path:
        metadata["path"] = path
    if milestone:
        metadata["milestone"] = milestone
    if milestone_name:
        metadata["milestone_name"] = milestone_name
    if tags:
        metadata["tags"] = tags

    post = frontmatter.Post("", **metadata)
    filepath = board_dir / f"{task_id}_{slug}.md"
    filepath.write_text(frontmatter.dumps(post))

    return metadata


def list_tasks(board_dir: Path) -> List[Dict]:
    """List all non-archived tasks, sorted by ID."""
    tasks = []
    for f in sorted(board_dir.glob("[0-9]*_*.md")):
        post = frontmatter.load(str(f))
        tasks.append(dict(post.metadata, body=post.content))
    return tasks


def get_task(board_dir: Path, task_id: str) -> Dict:
    """Read a single task by ID. Raises FileNotFoundError if not found."""
    filepath = _task_file(board_dir, task_id)
    if not filepath:
        raise FileNotFoundError(f"Task {task_id} not found")
    post = frontmatter.load(str(filepath))
    return dict(post.metadata, body=post.content)


def update_task(board_dir: Path, task_id: str, **kwargs) -> Dict:
    """Update task metadata. Returns updated task dict."""
    filepath = _task_file(board_dir, task_id)
    if not filepath:
        raise FileNotFoundError(f"Task {task_id} not found")

    post = frontmatter.load(str(filepath))

    for key, value in kwargs.items():
        post.metadata[key] = value
    post.metadata["updated"] = date.today().isoformat()

    filepath.write_text(frontmatter.dumps(post))
    return dict(post.metadata, body=post.content)


def archive_task(board_dir: Path, task_id: str) -> None:
    """Move a task to board/archive/."""
    filepath = _task_file(board_dir, task_id)
    if not filepath:
        raise FileNotFoundError(f"Task {task_id} not found")

    archive = board_dir / "archive"
    archive.mkdir(exist_ok=True)
    filepath.rename(archive / filepath.name)


def search_tasks(board_dir: Path, query: str) -> List[Dict]:
    """Full-text search across all task files (title + metadata + body)."""
    query_lower = query.lower()
    results = []
    for f in sorted(board_dir.glob("[0-9]*_*.md")):
        content = f.read_text()
        if query_lower in content.lower():
            post = frontmatter.load(str(f))
            results.append(dict(post.metadata, body=post.content))
    return results
