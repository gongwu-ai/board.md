# board.md

Markdown-native project board for the AI agent era.

```
board list

 ID  │ Title            │ Status      │ Column    │ Priority │ Milestone
─────┼──────────────────┼─────────────┼───────────┼──────────┼──────────
 001 │ geo_spo          │ in-progress │ CFFF      │ high     │ 2026-04-01
 002 │ virec_fusion     │ in-progress │ GAIA      │ high     │
 003 │ atmocat          │ blocked     │ AIStation │ medium   │
```

## Philosophy

**board.md does six things. Not seven.**

1. **Store tasks as markdown files** — `board/*.md`, YAML frontmatter + freeform notes
2. **List/filter/search** — table view, JSON output, full-text search
3. **Update status** — via CLI, keeps timestamps consistent
4. **Remind** — deadline notifications via [ntfy.sh](https://ntfy.sh) (zero server, zero account)
5. **Work with any AI agent** — Claude Code, Codex, Cursor, Gemini CLI read `AGENTS.md`
6. **Work with any editor** — Obsidian, VS Code, vim, cat — it's just `.md` files

### What board.md does NOT do

- **No GUI** — build one if you want, we won't
- **No server, no database** — your filesystem is the database, git is the sync
- **No MCP** — CLI is 35x cheaper for AI agents ([source](https://www.scalekit.com/blog/mcp-vs-cli-use))
- **No plugin for any app** — we are a standalone CLI, not a parasite
- **No data format changes** — markdown + YAML frontmatter, v1 to v100

If we stop maintaining this tomorrow, your data is still a folder of `.md` files. Zero loss.

## Install

```bash
# TODO: pip install board.md / brew install board.md / cargo install board.md
```

## Quick Start

```bash
# Initialize a board in your project
board init

# Add a task
board add "Build recommendation engine" --column GAIA --priority high

# Update progress
board update 001 -t "Training baseline model" -s in-progress

# Set a reminder (requires ntfy.sh app on your phone)
board remind 001 24h "Baseline training should be done"

# List all tasks
board list

# AI agents use it the same way — via CLI or by reading AGENTS.md
```

## Data Format

Each task lives in `board/<id>_<slug>.md`:

```yaml
---
title: Build recommendation engine
status: in-progress
column: GAIA
priority: high
created: 2026-03-20
updated: 2026-03-20
---

## Current Task

Training baseline model on MovieLens dataset.

## Notes

- Using collaborative filtering as baseline
- GPU allocated on GAIA: 2x A100
```

Human-readable. Git-diffable. Editor-agnostic. Agent-friendly.

## AI Agent Integration

board.md ships an `AGENTS.md` file — the emerging cross-tool standard (Linux Foundation / Agentic AI Foundation) supported by Codex, Cursor, Copilot, Gemini CLI, and others.

For Claude Code, symlink it: `ln -s AGENTS.md CLAUDE.md`

No MCP server needed. Any agent that can call `bash` can use board.md.

## Notifications

board.md uses [ntfy.sh](https://ntfy.sh) for reminders — zero account, zero server:

```bash
# Set up your topic (one time)
board config ntfy-topic my-secret-board-topic

# Then reminders just work
board remind 001 30m "Check training loss"
board remind 002 2026-04-01T09:00 "Milestone deadline"
```

Install the ntfy app on your phone → subscribe to your topic → done.

## License

MIT
