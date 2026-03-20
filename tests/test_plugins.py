"""Tests for the plugin system."""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from board_md.cli import app
from board_md import plugins

runner = CliRunner()


# --- Plugin registry ---

def test_list_plugins():
    all_plugins = plugins.list_plugins()
    assert "obsidian" in all_plugins
    assert "ntfy" in all_plugins
    assert "feishu" in all_plugins


def test_get_plugin():
    mod = plugins.get_plugin("obsidian")
    assert mod is not None
    assert hasattr(mod, "NAME")
    assert hasattr(mod, "init")
    assert hasattr(mod, "clean")


def test_get_unknown_plugin():
    assert plugins.get_plugin("nonexistent") is None


def test_notify_backends():
    backends = plugins.notify_backends()
    assert "ntfy" in backends
    assert "feishu" in backends
    assert "obsidian" not in backends  # obsidian has no send()


# --- Obsidian plugin ---

def test_obsidian_init(tmp_path):
    mod = plugins.get_plugin("obsidian")
    created = mod.init(tmp_path)
    assert any("app.json" in p for p in created)
    assert any("types.json" in p for p in created)
    assert (tmp_path / ".obsidian" / "app.json").exists()
    assert (tmp_path / ".obsidian" / "types.json").exists()


def test_obsidian_init_idempotent(tmp_path):
    """Second init should not overwrite existing files."""
    mod = plugins.get_plugin("obsidian")
    mod.init(tmp_path)
    # Modify app.json
    app_file = tmp_path / ".obsidian" / "app.json"
    app_file.write_text('{"custom": true}')
    # Second init should NOT overwrite
    created = mod.init(tmp_path)
    assert created == []
    assert json.loads(app_file.read_text()) == {"custom": True}


def test_obsidian_types_json(tmp_path):
    """types.json should declare frontmatter property types."""
    mod = plugins.get_plugin("obsidian")
    mod.init(tmp_path)
    types = json.loads((tmp_path / ".obsidian" / "types.json").read_text())
    assert types["types"]["status"] == "text"
    assert types["types"]["milestone"] == "date"
    assert types["types"]["tags"] == "tags"


def test_obsidian_clean(tmp_path):
    mod = plugins.get_plugin("obsidian")
    mod.init(tmp_path)
    removed = mod.clean(tmp_path)
    assert len(removed) > 0
    assert not (tmp_path / ".obsidian" / "app.json").exists()


def test_obsidian_clean_noop(tmp_path):
    mod = plugins.get_plugin("obsidian")
    removed = mod.clean(tmp_path)
    assert removed == []


# --- Notify via plugins ---

def test_notify_dispatches_to_ntfy():
    """notify.send should route to the ntfy plugin."""
    from unittest.mock import patch, MagicMock
    from board_md import notify

    with patch("board_md.plugins.ntfy.urllib.request.urlopen") as mock:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp

        result = notify.send(
            {"notify_backend": "ntfy", "ntfy_topic": "test"},
            "hello",
        )
        assert result is True


def test_notify_dispatches_to_feishu():
    from unittest.mock import patch, MagicMock
    from board_md import notify

    with patch("board_md.plugins.feishu.urllib.request.urlopen") as mock:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"code": 0}'
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp

        result = notify.send(
            {"notify_backend": "feishu", "feishu_webhook": "https://example.com/hook"},
            "hello",
        )
        assert result is True


def test_notify_unknown_backend():
    from board_md import notify
    assert notify.send({"notify_backend": "telegram"}, "msg") is False


# --- CLI integration ---

def test_cli_init_with_obsidian(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "--with", "obsidian"])
    assert result.exit_code == 0
    assert "obsidian" in result.output.lower()
    assert (tmp_path / ".obsidian" / "app.json").exists()


def test_cli_plugin_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Need a board dir for plugin commands
    (tmp_path / "board").mkdir()
    (tmp_path / "board" / "00000001_test.md").write_text("---\ntitle: x\n---\n")

    result = runner.invoke(app, ["plugin", "list"])
    assert result.exit_code == 0
    assert "obsidian" in result.output
    assert "ntfy" in result.output
    assert "feishu" in result.output


def test_cli_plugin_enable_disable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["plugin", "enable", "obsidian"])
    assert result.exit_code == 0
    assert (tmp_path / ".obsidian" / "types.json").exists()

    result = runner.invoke(app, ["plugin", "disable", "obsidian"])
    assert result.exit_code == 0
    assert not (tmp_path / ".obsidian" / "types.json").exists()
