# -*- coding: utf-8 -*-
"""Integration tests for the subagent loop and CLI fallback chains."""

import os
import sys
from pathlib import Path
import pytest

import templates.core.llm_client as llm_client
from templates.runtime.bali_runtime import run_task
from templates.core.agent_loop import run_agent_loop

def test_cli_dry_run(temp_project_dir):
    # Test CLI dry run does not trigger LLM calls and completes successfully
    res = run_task(
        temp_project_dir,
        task="Corrigir logins",
        dry_run=True,
        specialist_name="spec-implementer",
        workflow="operate"
    )
    assert res == 0
    
    # Dry run file created
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").glob("*"))
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "dry-run.txt").is_file()

def test_runtime_provider_uses_templates_run_bridge(temp_project_dir, monkeypatch):
    bridge = temp_project_dir / ".agent" / "templates" / "run.py"
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.write_text("# runtime bridge", encoding="utf-8")

    calls = []

    class Completed:
        returncode = 0

    def fake_run(command, *args, **kwargs):
        calls.append(command)
        return Completed()

    import templates.runtime.bali_runtime as bali_runtime

    monkeypatch.setenv("BALI_LLM_PROVIDER", "openai")
    monkeypatch.setattr(bali_runtime.subprocess, "run", fake_run)

    res = run_task(temp_project_dir, task="Corrigir logins", dry_run=False)

    assert res == 0
    assert calls
    assert Path(calls[0][1]) == bridge

def test_agent_loop_execution(temp_project_dir, monkeypatch):
    mock_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Tarefa concluída com sucesso!"
                }
            }
        ]
    }
    
    # We must monkeypatch call_llm_api on agent_loop module, as it was already imported there
    import templates.core.agent_loop as agent_loop
    monkeypatch.setattr(agent_loop, "call_llm_api", lambda *args, **kwargs: mock_response)
    
    # Run the loop for planner subagent
    result = run_agent_loop("planner", "Por favor crie o plano de login.", temp_project_dir)
    assert result == "Tarefa concluída com sucesso!"
    
    # Validate session file was created
    session_file = temp_project_dir / ".agent" / "sessions" / "planner.json"
    assert session_file.is_file()
