# -*- coding: utf-8 -*-
"""Tests for project-local auditable skill creation."""

from pathlib import Path

import pytest


def test_create_or_update_skill_writes_skill_and_audit(temp_project_dir):
    from templates.core.skills import create_or_update_skill

    result = create_or_update_skill(
        temp_project_dir,
        skill_id="render-debugging",
        title="Render Debugging",
        body="Use when diagnosing recurring render pipeline failures.",
        reason="needed for recurring render incidents",
        agent="orchestrator",
    )

    skill_path = temp_project_dir / ".agent" / "skills" / "render-debugging" / "SKILL.md"
    audit_path = temp_project_dir / ".agent" / "skills" / "AUDIT.md"

    assert "Skill criada/atualizada" in result
    assert skill_path.is_file()
    assert "# Render Debugging" in skill_path.read_text(encoding="utf-8")
    audit_text = audit_path.read_text(encoding="utf-8")
    assert "render-debugging" in audit_text
    assert "needed for recurring render incidents" in audit_text
    assert "orchestrator" in audit_text


@pytest.mark.parametrize("skill_id", ["../escape", "bad id", ".hidden", "UPPER"])
def test_create_or_update_skill_rejects_invalid_ids(temp_project_dir, skill_id):
    from templates.core.skills import create_or_update_skill

    with pytest.raises(ValueError):
        create_or_update_skill(
            temp_project_dir,
            skill_id=skill_id,
            title="Bad Skill",
            body="This should not be written.",
            reason="invalid id",
            agent="orchestrator",
        )


def test_create_skill_tool_uses_project_local_skill_store(temp_project_dir):
    from templates.core.tools import execute_tool

    result = execute_tool(
        "create_skill",
        {
            "skill_id": "db-migrations",
            "title": "Database Migrations",
            "body": "Use when changing database schema or migrations.",
            "reason": "database changes are recurring in this project",
        },
        temp_project_dir,
        current_agent="spec-database",
    )

    assert "Skill criada/atualizada" in result
    assert (temp_project_dir / ".agent" / "skills" / "db-migrations" / "SKILL.md").is_file()
