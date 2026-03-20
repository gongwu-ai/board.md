# board.md — Agent Instructions

## What is board.md?

A markdown-native project board CLI. Data lives in `board/*.md` files — one file per task/project. No server, no database, no lock-in.

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
board update <id> -t "doing X"          # update current task description
board update <id> -d "new desc"         # update description
board show <id>                         # show task details
board archive <id>                      # archive a task
board remind <id> <when> [msg]          # set a reminder
board search <query>                    # full-text search
board config <key> <value>              # set configuration
```

Task IDs are 8-digit zero-padded integers (00000001, 00000002, ...).
Shorthand is supported: `board show 1` resolves to `board show 00000001`.

## Data Format

Each task is a markdown file in `board/` with YAML frontmatter:

```yaml
---
title: Project Name
description: One-line summary of this task
id: "00000001"
status: in-progress        # backlog | todo | in-progress | blocked | done
column: GAIA               # board column (e.g., Local, CFFF, AIStation, GAIA)
priority: high             # low | medium | high | critical
current_task: Training baseline model  # what's being worked on now
host: TELEFONICA-GAIA      # optional: associated host
path: /data/wenh/project/  # optional: project path
milestone: 2026-04-01      # optional: next milestone date
milestone_name: "v1 release" # optional: milestone description
tags: [backend, ml]        # optional: tags
created: 2026-03-20
updated: 2026-03-20
---

## Current Task

Training baseline model on MovieLens dataset.

## Notes

Free-form markdown notes, logs, context.
```

**Source of truth**: frontmatter fields are authoritative. Body sections
(`## Current Task`, `## Notes`) are rendered views — kept in sync by the CLI
but frontmatter wins if there's a discrepancy.

## Notification Backends

Configured via `board config`:

```bash
# ntfy.sh (default) — zero account, built-in scheduling
board config notify-backend ntfy
board config ntfy-topic my-secret-topic

# Feishu bot webhook — Chinese dev ecosystem
board config notify-backend feishu
board config feishu-webhook https://open.feishu.cn/open-apis/bot/v2/hook/<token>
```

Note: Feishu webhooks do not support delayed delivery (the `when` argument
is ignored). ntfy.sh supports built-in scheduling via the `At` header.

## Agent Conventions

- When the user mentions project progress, use `board update` to reflect it.
- When the user sets a deadline, use `board remind` to schedule a notification.
- Prefer `board list --json` when you need to process task data programmatically.
- You MAY read `board/*.md` files directly for information, but use the CLI
  for writes so timestamps and body sections stay consistent.
- When providing a custom slug via `board add --slug`, use lowercase kebab-case.
- `current_task` is stored in frontmatter (source of truth) AND rendered in
  the body's `## Current Task` section. Always update via CLI, not by
  editing the file directly.
