# board.md — Claude Code Instructions

See [AGENTS.md](AGENTS.md) for the full agent specification. This file exists for Claude Code compatibility until AGENTS.md is natively supported.

## Development Rules

- Language: Python 3.10+ (no exotic dependencies)
- CLI framework: `click` or `typer` (TBD)
- Data format: markdown + YAML frontmatter — this is a social contract, never change it
- Tests: `pytest`, run with `python -m pytest tests/`
- Keep it simple — if a feature needs more than 100 lines, reconsider

## Project Structure

```
board.md/
  board/              # Python package
    __init__.py
    cli.py            # CLI entry point
    store.py          # Read/write board/*.md files
    notify.py         # ntfy.sh integration
    render.py         # Table/JSON output formatting
  tests/
  AGENTS.md           # Cross-tool agent instructions
  CLAUDE.md           # This file (Claude Code compat)
  README.md
  pyproject.toml
```
