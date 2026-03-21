"""Obsidian integration plugin for board.md.

Creates a minimal .obsidian/ configuration so the board/ directory
can be viewed as a kanban board in Obsidian.
"""

from __future__ import annotations

import json
import logging
import platform
import re
import subprocess
from pathlib import Path
from typing import Dict, List

import frontmatter

logger = logging.getLogger(__name__)

NAME = "obsidian"
DESCRIPTION = "View board as a kanban in Obsidian (local viewer, no lock-in)"

# Minimal Obsidian app config
_APP_CONFIG = {
    "showFrontmatter": True,
    "livePreview": True,
    "readableLineLength": True,
}

# Workspace layout pointing at board/
_WORKSPACE = {
    "main": {
        "id": "board-workspace",
        "type": "split",
        "children": [
            {
                "id": "board-leaf",
                "type": "leaf",
                "state": {
                    "type": "file-explorer",
                    "state": {},
                },
            }
        ],
        "direction": "vertical",
    },
    "left": {"id": "left", "type": "split", "children": [], "direction": "vertical"},
    "right": {"id": "right", "type": "split", "children": [], "direction": "vertical"},
    "active": "board-leaf",
    "lastOpenFiles": [],
}


def init(project_dir: Path) -> List[str]:
    """Create minimal .obsidian/ config for viewing board/ as a vault.

    The project_dir itself becomes the Obsidian vault root, with board/
    as a subfolder containing the task files.
    """
    obsidian_dir = project_dir / ".obsidian"
    obsidian_dir.mkdir(exist_ok=True)
    created = []

    # app.json — basic settings
    app_file = obsidian_dir / "app.json"
    if not app_file.exists():
        app_file.write_text(json.dumps(_APP_CONFIG, indent=2) + "\n")
        created.append(".obsidian/app.json")

    # workspace.json
    workspace_file = obsidian_dir / "workspace.json"
    if not workspace_file.exists():
        workspace_file.write_text(json.dumps(_WORKSPACE, indent=2) + "\n")
        created.append(".obsidian/workspace.json")

    # .obsidian/types.json — tell Obsidian about our frontmatter property types
    types_file = obsidian_dir / "types.json"
    if not types_file.exists():
        types_file.write_text(json.dumps({
            "types": {
                "title": "text",
                "description": "text",
                "id": "text",
                "status": "text",
                "column": "text",
                "priority": "text",
                "current_task": "text",
                "host": "text",
                "path": "text",
                "milestone": "date",
                "milestone_name": "text",
                "tags": "tags",
                "created": "date",
                "updated": "date",
            }
        }, indent=2) + "\n")
        created.append(".obsidian/types.json")

    return created


def clean(project_dir: Path) -> List[str]:
    """Remove board.md-created .obsidian/ files.

    Only removes files we created (app.json, workspace.json, types.json).
    Does NOT remove .obsidian/ itself — user may have other config there.
    """
    obsidian_dir = project_dir / ".obsidian"
    removed = []
    for name in ["app.json", "workspace.json", "types.json"]:
        f = obsidian_dir / name
        if f.exists():
            f.unlink()
            removed.append(f".obsidian/{name}")
    return removed


def _render_card(task: Dict, filename: str) -> str:
    """Render a single task as an enriched kanban card entry."""
    slug = filename.rsplit(".", 1)[0]  # strip .md
    title = task.get("title", slug)
    priority = task.get("priority", "medium")

    # Title line: - [ ] [[slug|title]] #priority
    priority_tag = ""
    if priority in ("high", "critical"):
        priority_tag = f" #{priority}"
    elif priority == "low":
        priority_tag = " #low"

    line = f"- [ ] [[{slug}|{title}]]{priority_tag}"
    parts = [line]

    # Description
    desc = task.get("description", "")
    if desc:
        parts.append(f"\t{desc}")

    # Milestone
    milestone = task.get("milestone", "")
    milestone_name = task.get("milestone_name", "")
    if milestone:
        ms_text = f"**{milestone}**"
        if milestone_name:
            ms_text += f" {milestone_name}"
        parts.append(f"\t{ms_text}")

    # Body checklists (extract - [ ] / - [x] lines from body)
    body = task.get("body", "")
    if body:
        for m in re.finditer(r"^- \[[ x]\] .+$", body, re.MULTILINE):
            parts.append(f"\t{m.group(0)}")

    return "\n".join(parts)


def _parse_existing_columns(kanban_path: Path) -> List[str]:
    """Extract column order from an existing kanban.md."""
    if not kanban_path.exists():
        return []
    text = kanban_path.read_text()
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


def sync_kanban(project_dir: Path) -> Path:
    """Generate or update kanban.md from all task card files.

    Reads each board/*.md file, groups by column, and writes enriched
    kanban.md with descriptions, milestones, and checklists.
    Preserves existing column order; appends new columns before Archive.
    """
    board_dir = project_dir / "board"
    kanban_path = board_dir / "kanban.md"

    # Read all tasks
    tasks = []
    for f in sorted(board_dir.glob("[0-9]*_*.md")):
        post = frontmatter.load(str(f))
        tasks.append(dict(post.metadata, body=post.content, _filename=f.name))

    # Group by column
    by_column: Dict[str, List[Dict]] = {}
    for t in tasks:
        col = t.get("column", "") or "Uncategorized"
        by_column.setdefault(col, []).append(t)

    # Determine column order: preserve existing, append new before Archive
    existing_columns = _parse_existing_columns(kanban_path)
    # Ensure Archive is always last
    if "Archive" in existing_columns:
        existing_columns.remove("Archive")

    all_columns = list(existing_columns)
    for col in by_column:
        if col not in all_columns and col != "Archive":
            all_columns.append(col)
    all_columns.append("Archive")

    # Build kanban.md content
    lines = [
        "---",
        "kanban-plugin: board",
        "kanban-settings:",
        "  show-checkboxes: false",
        "  hide-tags-in-title: true",
        "---",
        "",
    ]

    for col in all_columns:
        lines.append(f"## {col}")
        lines.append("")
        for t in by_column.get(col, []):
            lines.append(_render_card(t, t["_filename"]))
        lines.append("")

    kanban_path.write_text("\n".join(lines))
    return kanban_path


def open_vault(project_dir: Path) -> bool:
    """Open the project directory in Obsidian.

    Tries the Obsidian URI scheme first, falls back to `open -a Obsidian`.
    Returns True on success.
    """
    system = platform.system()
    vault_path = str(project_dir.resolve())

    if system == "Darwin":
        # macOS: open -a Obsidian <path> works for both new and existing vaults.
        # It registers the vault automatically on first open.
        try:
            subprocess.run(
                ["open", "-a", "Obsidian", vault_path],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    elif system == "Linux":
        try:
            subprocess.run(
                ["xdg-open", f"obsidian://open?path={vault_path}"],
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    else:
        logger.warning("Unsupported platform for open_vault: %s", system)
        return False
