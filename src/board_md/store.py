"""Read/write board/*.md task files."""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter
from slugify import slugify

logger = logging.getLogger(__name__)

ID_WIDTH = 8


def init_board(project_dir: Path) -> Path:
    """Create board/ directory in project_dir. Returns the board path."""
    board = project_dir / "board"
    board.mkdir(exist_ok=True)
    return board


def _next_id(board_dir: Path) -> str:
    """Find the next available task ID (zero-padded 8 digits)."""
    existing = [f.name for f in board_dir.glob("[0-9]*_*.md")]
    if not existing:
        return "0" * (ID_WIDTH - 1) + "1"
    max_id = max(int(f.split("_")[0]) for f in existing)
    return str(max_id + 1).zfill(ID_WIDTH)


def _make_slug(title: str) -> str:
    """Convert title to a filesystem-safe slug using python-slugify."""
    slug = slugify(title, allow_unicode=True, max_length=40)
    return slug or "task"


def _task_file(board_dir: Path, task_id: str) -> Optional[Path]:
    """Find the file for a given task ID, supporting prefix matching.

    Supports:
      - Exact match: "00000001"
      - Numeric shorthand: "1" → zero-pads to "00000001"
      - Prefix match: "000" → matches if unique
    Raises ValueError if prefix is ambiguous.
    """
    # Try exact match
    matches = list(board_dir.glob(f"{task_id}_*.md"))
    if len(matches) == 1:
        return matches[0]

    # Try zero-padded match for numeric input
    if task_id.isdigit():
        padded = task_id.zfill(ID_WIDTH)
        matches = list(board_dir.glob(f"{padded}_*.md"))
        if len(matches) == 1:
            return matches[0]

    # Prefix match across all task files
    all_tasks = sorted(board_dir.glob("[0-9]*_*.md"))
    matches = [f for f in all_tasks if f.name.split("_")[0].startswith(task_id.zfill(1))]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        ids = [f.name.split("_")[0] for f in matches]
        raise ValueError(f"Ambiguous ID prefix '{task_id}', matches: {ids}")

    return None


def _update_body_section(body: str, heading: str, content: str) -> str:
    """Insert or replace a ## section in the markdown body.

    Preserves all other sections. If the section doesn't exist, prepends it.
    """
    pattern = re.compile(
        rf"(## {re.escape(heading)}\n\n)(.*?)(\n\n## |\Z)",
        re.DOTALL,
    )
    match = pattern.search(body)
    if match:
        replacement = match.group(1) + content + match.group(3)
        return body[: match.start()] + replacement + body[match.end() :]

    # Section not found — prepend
    section = f"## {heading}\n\n{content}\n"
    if body.strip():
        return section + "\n" + body
    return section


def add_task(
    board_dir: Path,
    title: str,
    *,
    description: str = "",
    status: str = "backlog",
    column: str = "",
    priority: str = "medium",
    host: str = "",
    path: str = "",
    milestone: str = "",
    milestone_name: str = "",
    tags: Optional[List[str]] = None,
    slug: Optional[str] = None,
) -> Dict:
    """Create a new task file. Returns the task metadata dict."""
    task_id = _next_id(board_dir)
    file_slug = slug or _make_slug(title)
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
    if description:
        metadata["description"] = description
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
    filepath = board_dir / f"{task_id}_{file_slug}.md"
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
    """Update task metadata and/or body sections. Returns updated task dict."""
    filepath = _task_file(board_dir, task_id)
    if not filepath:
        raise FileNotFoundError(f"Task {task_id} not found")

    post = frontmatter.load(str(filepath))

    # Handle current_task: write to both frontmatter and body section
    current_task = kwargs.pop("current_task", None)
    if current_task is not None:
        post.metadata["current_task"] = current_task
        post.content = _update_body_section(
            post.content, "Current Task", current_task
        )

    # Handle notes: append to body
    notes = kwargs.pop("notes", None)
    if notes is not None:
        post.content = _update_body_section(post.content, "Notes", notes)

    # Update remaining metadata
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
