"""board.md plugin registry.

Plugins are opt-in integrations that extend board.md without polluting the core.
Each plugin module exposes:
  - NAME: str
  - DESCRIPTION: str
  - init(project_dir: Path) -> List[str]   (files created)
  - clean(project_dir: Path) -> List[str]  (files removed)

Notification plugins additionally expose:
  - send(config: dict, message: str, **kwargs) -> bool
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Plugin name → module path
_REGISTRY: Dict[str, str] = {
    "obsidian": "board_md.plugins.obsidian",
    "ntfy": "board_md.plugins.ntfy",
    "feishu": "board_md.plugins.feishu",
}


def list_plugins() -> Dict[str, str]:
    """Return {name: description} for all registered plugins."""
    result = {}
    for name, module_path in _REGISTRY.items():
        mod = importlib.import_module(module_path)
        result[name] = getattr(mod, "DESCRIPTION", "")
    return result


def get_plugin(name: str):
    """Import and return a plugin module by name. Returns None if not found."""
    module_path = _REGISTRY.get(name)
    if not module_path:
        return None
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        logger.warning("Failed to import plugin %s: %s", name, e)
        return None


def init_plugin(name: str, project_dir: Path) -> List[str]:
    """Run a plugin's init(). Returns list of created file paths."""
    mod = get_plugin(name)
    if mod and hasattr(mod, "init"):
        return mod.init(project_dir)
    return []


def clean_plugin(name: str, project_dir: Path) -> List[str]:
    """Run a plugin's clean(). Returns list of removed file paths."""
    mod = get_plugin(name)
    if mod and hasattr(mod, "clean"):
        return mod.clean(project_dir)
    return []


def notify_backends() -> List[str]:
    """Return names of plugins that support send()."""
    backends = []
    for name, module_path in _REGISTRY.items():
        mod = importlib.import_module(module_path)
        if hasattr(mod, "send"):
            backends.append(name)
    return backends
