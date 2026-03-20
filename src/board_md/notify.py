"""ntfy.sh notification integration."""

from __future__ import annotations

import urllib.request
import urllib.error
from typing import List, Optional


def send_notification(
    topic: str,
    message: str,
    *,
    title: str = "board.md",
    delay: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Send a notification via ntfy.sh. Returns True on success."""
    url = f"https://ntfy.sh/{topic}"
    headers = {"Title": title}

    if delay:
        headers["At"] = delay
    if priority:
        headers["Priority"] = priority
    if tags:
        headers["Tags"] = ",".join(tags)

    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False
