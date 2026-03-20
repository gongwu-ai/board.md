"""Tests for the CLI interface."""

import json
from click.testing import CliRunner
from board_md.cli import cli


def test_init(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / "board").is_dir()


def test_add_and_list(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    result = runner.invoke(cli, ["add", "My first task", "-c", "Local", "-p", "high"])
    assert result.exit_code == 0
    assert "001" in result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "My first task" in result.output


def test_list_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "Task A"])

    result = runner.invoke(cli, ["list", "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed) == 1
    assert parsed[0]["title"] == "Task A"


def test_list_filter_by_status(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "Backlog task"])
    runner.invoke(cli, ["add", "Active task", "-s", "in-progress"])

    result = runner.invoke(cli, ["list", "-s", "in-progress"])
    assert "Active task" in result.output
    assert "Backlog task" not in result.output


def test_show(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "Detailed task", "-c", "GAIA"])

    result = runner.invoke(cli, ["show", "001"])
    assert result.exit_code == 0
    assert "Detailed task" in result.output
    assert "GAIA" in result.output


def test_show_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])

    result = runner.invoke(cli, ["show", "999"])
    assert result.exit_code == 1


def test_update(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "Update me"])

    result = runner.invoke(cli, ["update", "001", "-s", "in-progress", "-t", "Working hard"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["show", "001"])
    assert "in-progress" in result.output


def test_update_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "No change"])

    result = runner.invoke(cli, ["update", "001"])
    assert result.exit_code == 1


def test_archive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "Archive me"])

    result = runner.invoke(cli, ["archive", "001"])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["list"])
    assert "Archive me" not in result.output


def test_search(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["add", "ML Pipeline"])
    runner.invoke(cli, ["add", "Frontend Work"])

    result = runner.invoke(cli, ["search", "pipeline"])
    assert "ML Pipeline" in result.output
    assert "Frontend" not in result.output
