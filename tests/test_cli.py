"""Tests for the CLI interface (typer)."""

import json
from typer.testing import CliRunner
from board_md.cli import app

runner = CliRunner()


def test_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / "board").is_dir()


def test_add_and_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["add", "My first task", "-c", "Local", "-p", "high"])
    assert result.exit_code == 0
    assert "00000001" in result.output

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "My first task" in result.output


def test_add_with_description(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["add", "Task X", "-d", "A short description"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["show", "1"])
    assert "A short description" in result.output


def test_add_with_custom_slug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["add", "My Task", "--slug", "my-custom-name"])
    assert result.exit_code == 0
    assert (tmp_path / "board" / "00000001_my-custom-name.md").exists()


def test_list_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "Task A"])

    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "Task A"


def test_list_filter_by_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "Backlog task"])
    runner.invoke(app, ["add", "Active task", "-s", "in-progress"])

    result = runner.invoke(app, ["list", "-s", "in-progress"])
    assert "Active task" in result.output
    assert "Backlog task" not in result.output


def test_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "Detailed task", "-c", "GAIA"])

    result = runner.invoke(app, ["show", "1"])
    assert result.exit_code == 0
    assert "Detailed task" in result.output
    assert "GAIA" in result.output


def test_show_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["show", "999"])
    assert result.exit_code == 1


def test_update(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "Update me"])

    result = runner.invoke(app, ["update", "1", "-s", "in-progress", "-t", "Working hard"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["show", "1"])
    assert "in-progress" in result.output
    assert "Working hard" in result.output


def test_update_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "No change"])

    result = runner.invoke(app, ["update", "1"])
    assert result.exit_code == 1


def test_archive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "Archive me"])

    result = runner.invoke(app, ["archive", "1"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["list"])
    assert "Archive me" not in result.output


def test_search(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])
    runner.invoke(app, ["add", "ML Pipeline"])
    runner.invoke(app, ["add", "Frontend Work"])

    result = runner.invoke(app, ["search", "pipeline"])
    assert "ML Pipeline" in result.output
    assert "Frontend" not in result.output


def test_chinese_task(tmp_path, monkeypatch):
    """Chinese titles should work end-to-end."""
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["add", "训练基线模型", "-c", "CFFF"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["list"])
    assert "训练基线模型" in result.output
