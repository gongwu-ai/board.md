"""Pluggable notification backends for board.md.

Supported backends:
  - ntfy: ntfy.sh push notifications (default)
  - feishu: Feishu/Lark bot webhook
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def send(
    config: Dict,
    message: str,
    *,
    title: str = "board.md",
    delay: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Send a notification via the configured backend. Returns True on success."""
    backend = config.get("notify_backend", "ntfy")

    if backend == "ntfy":
        topic = config.get("ntfy_topic")
        if not topic:
            logger.error("ntfy_topic not configured")
            return False
        return _send_ntfy(topic, message, title=title, delay=delay,
                          priority=priority, tags=tags)

    elif backend == "feishu":
        webhook = config.get("feishu_webhook")
        if not webhook:
            logger.error("feishu_webhook not configured")
            return False
        return _send_feishu(webhook, message, title=title)

    else:
        logger.error("Unknown notify backend: %s", backend)
        return False


def _send_ntfy(
    topic: str,
    message: str,
    *,
    title: str = "board.md",
    delay: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> bool:
    """Send via ntfy.sh."""
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


def _send_feishu(
    webhook_url: str,
    message: str,
    *,
    title: str = "board.md",
) -> bool:
    """Send via Feishu/Lark bot webhook.

    Webhook URL format: https://open.feishu.cn/open-apis/bot/v2/hook/<token>
    Note: Feishu webhooks do not support scheduled delivery.
    """
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
