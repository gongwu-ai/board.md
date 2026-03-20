"""Output formatting for board.md CLI."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from wcwidth import wcswidth


def _display_width(s: str) -> int:
    """Get the display width of a string, accounting for CJK characters."""
    w = wcswidth(s)
    return w if w >= 0 else len(s)


def _pad(s: str, width: int) -> str:
    """Left-align a string with padding, accounting for display width."""
    current = _display_width(s)
    padding = max(0, width - current)
    return s + " " * padding


def render_table(tasks: List[Dict], columns: Optional[List[str]] = None) -> str:
    """Render tasks as an ASCII table with CJK-aware column alignment."""
    if not tasks:
        return "No tasks found."

    if columns is None:
        columns = ["id", "title", "status", "column", "priority", "milestone"]

    headers = {col: col.upper() for col in columns}
    widths = {col: _display_width(headers[col]) for col in columns}

    for task in tasks:
        for col in columns:
            val = str(task.get(col, ""))
            widths[col] = max(widths[col], _display_width(val))

    header_line = " │ ".join(_pad(headers[col], widths[col]) for col in columns)
    separator = "─┼─".join("─" * widths[col] for col in columns)

    lines = [header_line, separator]
    for task in tasks:
        row = " │ ".join(
            _pad(str(task.get(col, "")), widths[col]) for col in columns
        )
        lines.append(row)

    return "\n".join(lines)


def render_json(tasks: List[Dict]) -> str:
    """Render tasks as JSON (strips body for cleanliness)."""
    clean = [{k: v for k, v in t.items() if k != "body"} for t in tasks]
    return json.dumps(clean, indent=2, ensure_ascii=False, default=str)


def render_detail(task: Dict) -> str:
    """Render a single task in detail view."""
    lines = []
    for key in [
        "id", "title", "description", "status", "column", "priority",
        "current_task", "host", "path", "milestone", "milestone_name",
        "tags", "created", "updated",
    ]:
        val = task.get(key)
        if val:
            lines.append(f"  {key:16s} {val}")

    body = task.get("body", "").strip()
    if body:
        lines.append("")
        lines.append(body)

    return "\n".join(lines)
