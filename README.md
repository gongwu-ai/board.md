# board.md

Markdown-native project board for the AI agent era.

```
board list

ID       │ TITLE              │ STATUS      │ COLUMN  │ PRIORITY │ MILESTONE
─────────┼────────────────────┼─────────────┼─────────┼──────────┼──────────
00000001 │ recommendation-api │ in-progress │ Backend │ high     │ 2026-04-01
00000002 │ search-reindex     │ todo        │ Infra   │ medium   │
00000003 │ landing-page       │ backlog     │ Frontend│ low      │
```

## Install

```bash
pip install board-md
```

## Quick Start

```bash
# Initialize a board in your project
board init

# Add a task
board add "Build recommendation engine" -c GAIA -p high

# Update progress
board update 1 -t "Training baseline model" -s in-progress

# Set a reminder
board remind 1 24h "Baseline training should be done"

# List all tasks
board list
board list --json        # JSON output for scripts/agents
board list -s in-progress  # filter by status
```

## Philosophy

**board.md does six things. Not seven.**

1. **Store tasks as markdown files** — `board/*.md`, YAML frontmatter + freeform notes
2. **List/filter/search** — table view, JSON output, full-text search
3. **Update status** — via CLI, keeps timestamps consistent
4. **Remind** — pluggable notification backends (ntfy.sh, Feishu)
5. **Work with any AI agent** — auto-injects SKILL.md into Claude Code, Codex, Cursor, Gemini CLI, Copilot
6. **Work with any editor** — Obsidian, VS Code, vim, cat — it's just `.md` files

### What board.md does NOT do

- **No GUI** — use Obsidian as a viewer (see Plugins below)
- **No server, no database** — your filesystem is the database, git is the sync
- **No MCP** — CLI is [35x cheaper](https://www.scalekit.com/blog/mcp-vs-cli-use) for AI agents
- **No data format changes** — markdown + YAML frontmatter, v1 to v100

If we stop maintaining this tomorrow, your data is still a folder of `.md` files.

## Data Format

Each task lives in `board/{id}_{slug}.md`:

```yaml
---
title: Build recommendation engine
description: Core rec engine for video platform
id: "00000001"
status: in-progress
column: Backend
priority: high
current_task: Training baseline model
created: 2026-03-20
updated: 2026-03-20
---

## Current Task

Training baseline model on MovieLens dataset.

## Notes

Free-form markdown. Your knowledge base lives here.
```

IDs are 8-digit zero-padded. Shorthand works: `board show 1` resolves to `board show 00000001`.

## Plugins

Plugins are opt-in integrations that keep the core clean.

```bash
board plugin list              # show available plugins
board plugin enable obsidian   # enable a plugin
board plugin disable feishu    # disable a plugin
board init --with obsidian     # enable during init
```

### Obsidian — visual kanban board

**1. Install Obsidian** (if you don't have it):

```bash
# macOS
brew install --cask obsidian

# Or download from https://obsidian.md/download
```

**2. Enable the plugin and open your board:**

```bash
board init --with obsidian   # creates .obsidian/ config with property types
board open                   # launch Obsidian (registers vault automatically)
```

**3. Install Kanban plugin** (one-time, inside Obsidian):

- `Cmd+,` (Settings) → Community plugins → Turn off Safe Mode
- Browse → search **Kanban** → Install → Enable

**4. Done.** Open `board/kanban.md` in Obsidian to see your drag-and-drop kanban board.
Cards link to task files — click to see full details and notes.

### ntfy — push notifications (default)

```bash
board config notify-backend ntfy
board config ntfy-topic my-secret-topic
board remind 1 30m "Check training loss"
```

Zero account, zero server. Install [ntfy app](https://ntfy.sh) on your phone.

### Feishu — 飞书 bot webhook

```bash
board config notify-backend feishu
board config feishu-webhook https://open.feishu.cn/open-apis/bot/v2/hook/<token>
board remind 1 now "实验跑完了"
```

## AI Agent Integration

`board init` auto-injects SKILL.md into each AI tool's native discovery directory:

```
.claude/skills/board-md/SKILL.md
.codex/skills/board-md/SKILL.md
.gemini/skills/board-md/SKILL.md
.cursor/skills/board-md/SKILL.md
.github/skills/board-md/SKILL.md
```

No MCP server needed. Any agent that can call `bash` can use board.md. Follows the [Agent Skills specification](https://agentskills.io) and [AGENTS.md standard](https://agents.md) (Linux Foundation).

## CLI Reference

```
board init [--with PLUGIN] [--skip-skills]   Initialize board
board add TITLE [-c COL] [-p PRI] [-s STATUS] [-d DESC]  Add task
board list [--json] [-s STATUS] [-c COLUMN]  List tasks
board show ID                                Show details
board update ID [-s STATUS] [-t TASK] [-c COL] [-p PRI]  Update task
board archive ID                             Archive task
board search QUERY                           Full-text search
board remind ID WHEN [MESSAGE]               Set reminder
board config KEY VALUE                       Set config
board open                                   Open in Obsidian
board plugin list|enable|disable             Manage plugins
```

## License

MIT
