# -*- coding: utf-8 -*-
"""Unit tests for the Agent Manager module."""

import os
from pathlib import Path
import pytest

from templates.core.agent_manager import verify, list_agents, create_agent, load_agent_prompt

def test_verify_valid(temp_project_dir):
    problems = verify(temp_project_dir)
    assert len(problems) == 0

def test_verify_missing_agent(temp_project_dir):
    # Remove orchestrator.md
    orchestrator = temp_project_dir / ".agent" / "team" / "orchestrator.md"
    orchestrator.unlink()
    
    problems = verify(temp_project_dir)
    assert len(problems) > 0
    assert any("orchestrator.md" in p for p in problems)

def test_verify_requires_subagent_first_team_policies(temp_project_dir):
    manifest = temp_project_dir / ".agent" / "subagent.config.yaml"
    manifest.write_text("""# Manifesto antigo
subagents_policy:
  role_play_permitido: false
enforcement_adapters:
  - bali-runtime
time:
  espinha:
    - orchestrator
""", encoding="utf-8")

    problems = verify(temp_project_dir)

    assert any("product_spine" in p for p in problems)
    assert any("model_policy" in p for p in problems)
    assert any("project_fixed" in p for p in problems)
    assert any("temporary_policy" in p for p in problems)

def test_create_agent_valid(temp_project_dir):
    res = create_agent(
        temp_project_dir,
        agent_id="spec-frontend-styles",
        scope="Cuida dos estilos CSS e layouts.",
        overwrite=True
    )
    assert res == 0
    
    # Check that file exists and manifest is updated
    agent_file = temp_project_dir / ".agent" / "team" / "spec-frontend-styles.md"
    assert agent_file.is_file()
    
    manifest_text = (temp_project_dir / ".agent" / "subagent.config.yaml").read_text(encoding="utf-8")
    assert "spec-frontend-styles" in manifest_text

def test_load_agent_prompt(temp_project_dir):
    prompt = load_agent_prompt(temp_project_dir, "planner")
    assert "# planner agent definition" in prompt
    
    # Missing agent throws FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_agent_prompt(temp_project_dir, "nonexistent")
