"""Generate agent skill files for various AI coding tools.

Follows the Agent Skills specification (agentskills.io):
  - YAML frontmatter (name, description, compatibility, metadata)
  - Markdown body with instructions
  - Progressive disclosure: metadata ~100 tokens, instructions <5000 tokens

Writes standalone SKILL.md files into each tool's native discovery directory,
following OpenSpec Gen 3 pattern: never modify existing CLAUDE.md / AGENTS.md.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

SKILL_NAME = "board-md"

# Tool → (skill directory path template, command directory path template)
# Paths are relative to project root.
TOOL_CONFIGS: Dict[str, Dict] = {
    "claude": {
        "skill_dir": ".claude/skills/{name}",
    },
    "codex": {
        "skill_dir": ".codex/skills/{name}",
    },
    "gemini": {
        "skill_dir": ".gemini/skills/{name}",
    },
    "cursor": {
        "skill_dir": ".cursor/skills/{name}",
    },
    "copilot": {
        "skill_dir": ".github/skills/{name}",
    },
}


def _skill_content() -> str:
    """Generate the SKILL.md content for board.md."""
    return """\
---
name: board-md
description: >
  Markdown-native project board CLI. Manage tasks stored as board/*.md files.
  Use when the user mentions project status, task progress, deadlines, or
  wants to track work across multiple projects.
version: "0.2.0"
compatibility:
  - claude-code
  - codex-cli
  - gemini-cli
  - cursor
  - github-copilot
metadata:
  generatedBy: board-md
  category: project-management
---

# board.md — Task Management Skill

## When to activate

- User mentions project progress, task status, or deadlines
- User asks to track, update, or list tasks
- User says "board", "task", "milestone", "reminder"
- A `board/` directory exists in the project

## CLI Reference

```
board init                              # initialize board/ in current dir
board list                              # list all tasks (table view)
board list --json                       # JSON output for programmatic use
board list -s in-progress               # filter by status
board list -c GAIA                      # filter by column
board add "task name"                   # create a new task
board add "task" -d "description"       # with one-line description
board add "task" --slug my-slug         # with custom filename slug
board update <id> -s "in-progress"      # update task status
board update <id> -t "doing X"          # update current task
board show <id>                         # show task details
board archive <id>                      # archive a task
board remind <id> <when> [msg]          # set a reminder
board search <query>                    # full-text search
board config <key> <value>              # set configuration
```

Task IDs are 8-digit zero-padded (00000001). Shorthand supported: `board show 1`.

## Data Format

Each task is `board/{id}_{slug}.md` with YAML frontmatter:

```yaml
---
title: Task Name
description: One-line summary
id: "00000001"
status: in-progress    # backlog | todo | in-progress | blocked | done
column: GAIA           # board column
priority: high         # low | medium | high | critical
current_task: ...      # what's being worked on now
created: 2026-03-20
updated: 2026-03-20
---

## Current Task

Description of current work.

## Notes

Free-form markdown.
```

Frontmatter is source of truth. Body sections are rendered views.

## Conventions

- Use `board update` for writes (keeps timestamps and body sections in sync)
- Use `board list --json` for programmatic processing
- You MAY read `board/*.md` directly for information
- When providing `--slug`, use lowercase kebab-case
"""


def inject_skills(project_dir: Path, tools: List[str] = None) -> List[str]:
    """Write SKILL.md files into each tool's native discovery directory.

    Args:
        project_dir: Project root directory.
        tools: List of tool names to generate for. Default: all supported tools.

    Returns:
        List of created file paths (relative to project_dir).
    """
    if tools is None:
        tools = list(TOOL_CONFIGS.keys())

    content = _skill_content()
    created = []

    for tool in tools:
        cfg = TOOL_CONFIGS.get(tool)
        if not cfg:
            logger.warning("Unknown tool: %s (skipping)", tool)
            continue

        skill_dir = project_dir / cfg["skill_dir"].format(name=SKILL_NAME)
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content)
        created.append(str(skill_file.relative_to(project_dir)))
        logger.debug("Wrote %s", skill_file)

    return created


def clean_skills(project_dir: Path) -> List[str]:
    """Remove all board-md SKILL.md files from tool directories.

    Returns:
        List of removed file paths (relative to project_dir).
    """
    removed = []
    for cfg in TOOL_CONFIGS.values():
        skill_dir = project_dir / cfg["skill_dir"].format(name=SKILL_NAME)
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            skill_file.unlink()
            removed.append(str(skill_file.relative_to(project_dir)))
            # Remove empty directories
            try:
                skill_dir.rmdir()
            except OSError:
                pass  # Directory not empty, that's fine
    return removed
