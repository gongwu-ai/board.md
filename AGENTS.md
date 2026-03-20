# board.md — Agent Instructions

## What is board.md?

A markdown-native project board CLI. Data lives in `board/*.md` files — one file per task/project. No server, no database, no lock-in.

## CLI Reference

```
board list                        # list all tasks (table view)
board list --json                 # JSON output for programmatic use
board add "task name"             # create a new task
board update <id> -s "status"     # update task status
board update <id> -t "doing X"   # update current task description
board show <id>                   # show task details
board move <id> <column>          # move task to a column
board archive <id>                # archive a task
board remind <id> <when> [msg]    # set a reminder (via ntfy.sh)
board search <query>              # full-text search across all tasks
```

## Data Format

Each task is a markdown file in `board/` with YAML frontmatter:

```yaml
---
title: Project Name
status: in-progress        # backlog | todo | in-progress | blocked | done
column: GAIA               # board column (e.g., Local, CFFF, AIStation, GAIA)
priority: high             # low | medium | high | critical
host: TELEFONICA-GAIA      # optional: associated host
path: /data/wenh/project/  # optional: project path
milestone: 2026-04-01      # optional: next milestone date
milestone_name: "v1 release" # optional: milestone description
tags: [backend, ml]        # optional: tags
created: 2026-03-20
updated: 2026-03-20
---

## Current Task

What you're working on right now — one paragraph.

## Notes

Free-form markdown notes, logs, context. This is the knowledge management part.
```

## Agent Conventions

- When the user mentions project progress, use `board update` to reflect it.
- When the user sets a deadline, use `board remind` to schedule a notification.
- Prefer `board list --json` when you need to process task data programmatically.
- Do NOT modify `board/*.md` files directly — use the CLI so timestamps stay consistent.
- If the CLI is not installed, you MAY read `board/*.md` files directly for information.
