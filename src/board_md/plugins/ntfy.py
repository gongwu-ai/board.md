"""ntfy.sh notification plugin for board.md."""

from __future__ import annotations

import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

NAME = "ntfy"
DESCRIPTION = "Push notifications via ntfy.sh (zero account, built-in scheduling)"


def init(project_dir: Path) -> List[str]:
    """No files to create for ntfy — config lives in .board.json."""
    return []


def clean(project_dir: Path) -> List[str]:
    """Nothing to clean."""
    return []


def send(
    config: Dict,
    message: str,
    *,
    title: str = "board.md",
    delay: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Send a notification via ntfy.sh."""
    topic = config.get("ntfy_topic")
    if not topic:
        logger.error("ntfy_topic not configured")
        return False

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
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        logger.debug("ntfy send failed: %s: %s", type(e).__name__, e)
        return False
