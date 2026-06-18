# -*- coding: utf-8 -*-
"""Pytest configuration and shared test fixtures."""

import shutil
import tempfile
from pathlib import Path
import pytest

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with a mock .agent structure."""
    temp_dir = tempfile.mkdtemp()
    proj_path = Path(temp_dir)
    
    # Create agent structure
    agent_dir = proj_path / ".agent"
    team_dir = agent_dir / "team"
    runtime_dir = agent_dir / "runtime"
    output_dir = agent_dir / "output"
    
    team_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create config file
    config = agent_dir / "subagent.config.yaml"
    config.write_text("""# Manifesto
versao_base: "2.1.0"
projeto: "test-project"
modo: "operate"
subagents_policy:
  role_play_permitido: false
  fallback_obrigatorio: "bali-runtime"
enforcement_adapters:
  - bali-runtime
time:
  espinha:
    - orchestrator
    - planner
    - reviewer
  base:
    - discovery
    - prd-writer
    - sdd-architect
  especialistas:
    - id: spec-implementer
      arquivo: .agent/team/spec-implementer.md
      escopo: "test escopo"
""", encoding="utf-8")

    # Create spine and base agents
    for name in ["orchestrator", "planner", "reviewer", "discovery", "prd-writer", "sdd-architect", "spec-implementer"]:
        agent_file = team_dir / f"{name}.md"
        agent_file.write_text(f"# {name} agent definition\nEscopo de teste.", encoding="utf-8")
        
    # Create dummy bali_runtime.py and memory.md
    (runtime_dir / "bali_runtime.py").write_text("# Dummy runtime", encoding="utf-8")
    (agent_dir / "memory.md").write_text("# Memoria\n", encoding="utf-8")
    (agent_dir / "working-context.md").write_text("# Working Context\n## Status Atual\n## Progresso Recente\n", encoding="utf-8")
    
    yield proj_path
    
    shutil.rmtree(temp_dir)
