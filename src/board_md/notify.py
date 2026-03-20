"""Notification dispatcher — delegates to plugins.

This module is a thin router. Actual send logic lives in plugins/ntfy.py,
plugins/feishu.py, etc.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from board_md.plugins import get_plugin, notify_backends

logger = logging.getLogger(__name__)


def send(
    config: Dict,
    message: str,
    *,
    title: str = "board.md",
    delay: Optional[str] = None,
    **kwargs,
) -> bool:
    """Send a notification via the configured backend plugin.

    Backend is determined by config["notify_backend"] (default: "ntfy").
    """
    backend_name = config.get("notify_backend", "ntfy")
    plugin = get_plugin(backend_name)

    if plugin is None or not hasattr(plugin, "send"):
        logger.error(
            "Unknown or invalid notify backend: %s (available: %s)",
            backend_name,
            ", ".join(notify_backends()),
        )
        return False

    return plugin.send(config, message, title=title, delay=delay, **kwargs)
