"""Tests for agent skill injection."""

import pytest
from pathlib import Path
from board_md.skills import inject_skills, clean_skills, TOOL_CONFIGS, SKILL_NAME


def test_inject_all_tools(tmp_path):
    """Should create SKILL.md for all supported tools."""
    created = inject_skills(tmp_path)
    assert len(created) == len(TOOL_CONFIGS)
    for tool, cfg in TOOL_CONFIGS.items():
        skill_dir = tmp_path / cfg["skill_dir"].format(name=SKILL_NAME)
        assert (skill_dir / "SKILL.md").exists()


def test_inject_specific_tools(tmp_path):
    """Should only create for specified tools."""
    created = inject_skills(tmp_path, tools=["claude", "codex"])
    assert len(created) == 2
    assert any("claude" in p for p in created)
    assert any("codex" in p for p in created)
    # gemini should NOT exist
    gemini_dir = tmp_path / ".gemini" / "skills" / SKILL_NAME
    assert not gemini_dir.exists()


def test_inject_unknown_tool(tmp_path):
    """Unknown tools should be skipped without error."""
    created = inject_skills(tmp_path, tools=["claude", "nonexistent"])
    assert len(created) == 1


def test_inject_idempotent(tmp_path):
    """Running inject twice should overwrite without error."""
    inject_skills(tmp_path)
    created = inject_skills(tmp_path)
    assert len(created) == len(TOOL_CONFIGS)


def test_skill_content_has_frontmatter(tmp_path):
    """SKILL.md should have valid YAML frontmatter."""
    inject_skills(tmp_path, tools=["claude"])
    skill_file = tmp_path / ".claude" / "skills" / SKILL_NAME / "SKILL.md"
    content = skill_file.read_text()
    assert content.startswith("---\n")
    assert "name: board-md" in content
    assert "description:" in content
    assert "compatibility:" in content


def test_skill_content_has_cli_reference(tmp_path):
    """SKILL.md should contain CLI usage instructions."""
    inject_skills(tmp_path, tools=["claude"])
    skill_file = tmp_path / ".claude" / "skills" / SKILL_NAME / "SKILL.md"
    content = skill_file.read_text()
    assert "board init" in content
    assert "board list" in content
    assert "board add" in content
    assert "board update" in content


def test_clean_removes_skill_files(tmp_path):
    """clean_skills should remove all injected SKILL.md files."""
    inject_skills(tmp_path)
    removed = clean_skills(tmp_path)
    assert len(removed) == len(TOOL_CONFIGS)
    for tool, cfg in TOOL_CONFIGS.items():
        skill_dir = tmp_path / cfg["skill_dir"].format(name=SKILL_NAME)
        assert not (skill_dir / "SKILL.md").exists()


def test_clean_noop_when_no_skills(tmp_path):
    """clean_skills should do nothing if no skills exist."""
    removed = clean_skills(tmp_path)
    assert removed == []


def test_init_cli_creates_skills(tmp_path, monkeypatch):
    """board init should create skill files by default."""
    from typer.testing import CliRunner
    from board_md.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Agent skills injected" in result.output
    assert (tmp_path / ".claude" / "skills" / SKILL_NAME / "SKILL.md").exists()


def test_init_cli_skip_skills(tmp_path, monkeypatch):
    """board init --skip-skills should not create skill files."""
    from typer.testing import CliRunner
    from board_md.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--skip-skills"])
    assert result.exit_code == 0
    assert "Agent skills" not in result.output
    assert not (tmp_path / ".claude" / "skills" / SKILL_NAME).exists()


def test_init_cli_specific_tools(tmp_path, monkeypatch):
    """board init --tool claude --tool codex should only create for those."""
    from typer.testing import CliRunner
    from board_md.cli import app

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--tool", "claude", "--tool", "codex"])
    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "skills" / SKILL_NAME / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / SKILL_NAME / "SKILL.md").exists()
    assert not (tmp_path / ".gemini" / "skills" / SKILL_NAME).exists()
