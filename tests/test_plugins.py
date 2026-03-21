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


def _make_task(board_dir, task_id, title, column, priority="medium",
               description="", milestone="", milestone_name="", body=""):
    """Helper: write a task card file."""
    import frontmatter as fm
    meta = {"title": title, "id": task_id, "status": "in-progress",
            "column": column, "priority": priority, "created": "2026-03-21",
            "updated": "2026-03-21"}
    if description:
        meta["description"] = description
    if milestone:
        meta["milestone"] = milestone
    if milestone_name:
        meta["milestone_name"] = milestone_name
    post = fm.Post(body, **meta)
    slug = title.lower().replace(" ", "-")
    (board_dir / f"{task_id}_{slug}.md").write_text(fm.dumps(post))


# --- sync_kanban ---

def test_sync_kanban_basic(tmp_path):
    """sync_kanban should generate kanban.md with enriched card content."""
    board = tmp_path / "board"
    board.mkdir()
    _make_task(board, "00000001", "alpha", "Dev", priority="high",
               description="First task")
    _make_task(board, "00000002", "beta", "Dev", priority="low",
               description="Second task")

    mod = plugins.get_plugin("obsidian")
    kanban = mod.sync_kanban(tmp_path)
    text = kanban.read_text()

    assert "## Dev" in text
    assert "## Archive" in text
    assert "[[00000001_alpha|alpha]] #high" in text
    assert "[[00000002_beta|beta]] #low" in text
    assert "\tFirst task" in text
    assert "\tSecond task" in text


def test_sync_kanban_milestone(tmp_path):
    """Milestone should appear as bold date in card body."""
    board = tmp_path / "board"
    board.mkdir()
    _make_task(board, "00000001", "release", "Work",
               milestone="2026-04-21", milestone_name="paper deadline")

    mod = plugins.get_plugin("obsidian")
    mod.sync_kanban(tmp_path)
    text = (tmp_path / "board" / "kanban.md").read_text()

    assert "**2026-04-21** paper deadline" in text


def test_sync_kanban_checklist(tmp_path):
    """Body checklists should be pulled into kanban cards."""
    board = tmp_path / "board"
    board.mkdir()
    body = "## Tasks\n\n- [ ] Do thing A\n- [x] Done thing B\n\nSome notes."
    _make_task(board, "00000001", "checky", "Work", body=body)

    mod = plugins.get_plugin("obsidian")
    mod.sync_kanban(tmp_path)
    text = (tmp_path / "board" / "kanban.md").read_text()

    assert "\t- [ ] Do thing A" in text
    assert "\t- [x] Done thing B" in text
    assert "Some notes" not in text  # non-checklist body not included


def test_sync_kanban_preserves_column_order(tmp_path):
    """Existing column order should be preserved, new columns appended before Archive."""
    board = tmp_path / "board"
    board.mkdir()
    # Write existing kanban.md with custom column order
    (board / "kanban.md").write_text(
        "---\nkanban-plugin: board\n---\n\n## Zebra\n\n## Alpha\n\n## Archive\n"
    )
    _make_task(board, "00000001", "z-task", "Zebra")
    _make_task(board, "00000002", "a-task", "Alpha")
    _make_task(board, "00000003", "n-task", "NewCol")

    mod = plugins.get_plugin("obsidian")
    mod.sync_kanban(tmp_path)
    text = (tmp_path / "board" / "kanban.md").read_text()

    # Zebra before Alpha (preserved), NewCol before Archive
    z_pos = text.index("## Zebra")
    a_pos = text.index("## Alpha")
    n_pos = text.index("## NewCol")
    ar_pos = text.index("## Archive")
    assert z_pos < a_pos < n_pos < ar_pos


def test_sync_kanban_medium_priority_no_tag(tmp_path):
    """Medium priority should not get a tag."""
    board = tmp_path / "board"
    board.mkdir()
    _make_task(board, "00000001", "mid", "Work", priority="medium")

    mod = plugins.get_plugin("obsidian")
    mod.sync_kanban(tmp_path)
    text = (tmp_path / "board" / "kanban.md").read_text()

    assert "[[00000001_mid|mid]]" in text
    assert "#medium" not in text


def test_cli_sync(tmp_path, monkeypatch):
    """board sync CLI command should work."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init", "--with", "obsidian"])
    _make_task(tmp_path / "board", "00000001", "task-one", "Work",
               description="hello")

    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert "Synced" in result.output
    text = (tmp_path / "board" / "kanban.md").read_text()
    assert "hello" in text


def test_cli_plugin_enable_disable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["plugin", "enable", "obsidian"])
    assert result.exit_code == 0
    assert (tmp_path / ".obsidian" / "types.json").exists()

    result = runner.invoke(app, ["plugin", "disable", "obsidian"])
    assert result.exit_code == 0
    assert not (tmp_path / ".obsidian" / "types.json").exists()
