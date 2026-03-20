"""Feishu/Lark bot webhook notification plugin for board.md."""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

NAME = "feishu"
DESCRIPTION = "Notifications via Feishu/Lark bot webhook (Chinese dev ecosystem)"


def init(project_dir: Path) -> List[str]:
    """No files to create — config lives in .board.json."""
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
    **kwargs,
) -> bool:
    """Send via Feishu/Lark bot webhook.

    Note: Feishu webhooks do not support delayed delivery.
    The `delay` parameter is accepted but ignored.
    """
    webhook_url = config.get("feishu_webhook")
    if not webhook_url:
        logger.error("feishu_webhook not configured")
        return False

    if delay:
        logger.warning("Feishu does not support delayed delivery, ignoring delay=%s", delay)

    payload = json.dumps({
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": [
                {"tag": "markdown", "content": message},
            ],
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            return body.get("code") == 0 or body.get("StatusCode") == 0
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            json.JSONDecodeError) as e:
        logger.debug("feishu send failed: %s: %s", type(e).__name__, e)
        return False
