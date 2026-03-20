"""Obsidian integration plugin for board.md.

Creates a minimal .obsidian/ configuration so the board/ directory
can be viewed as a kanban board in Obsidian.
"""

from __future__ import annotations

import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import List

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
