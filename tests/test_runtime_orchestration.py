# -*- coding: utf-8 -*-
"""Tests for dynamic Orchestrator-led Bali Runtime execution."""

import json
from pathlib import Path

import pytest

import templates.runtime.bali_runtime as runtime


def test_parse_routing_plan_from_orchestrator_output():
    output = """
    Roteando a tarefa.
    {
      "classification": "small",
      "max_retries": 2,
      "steps": [
        {"agent": "spec-implementer", "prompt": "Fix login", "review": true}
      ]
    }
    """

    plan = runtime._parse_routing_plan(output)

    assert plan["classification"] == "small"
    assert plan["max_retries"] == 2
    assert plan["steps"][0]["agent"] == "spec-implementer"


def test_parse_routing_plan_rejects_missing_json():
    with pytest.raises(ValueError, match="routing plan"):
        runtime._parse_routing_plan("Vou fazer isso sem JSON.")


def test_runtime_executes_orchestrator_dynamic_plan(temp_project_dir, monkeypatch):
    calls = []

    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        calls.append(agent_name)
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "small",
                        "max_retries": 1,
                        "steps": [
                            {
                                "agent": "spec-implementer",
                                "prompt": "Corrigir logins",
                                "review": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
        elif agent_name == "spec-implementer":
            output_path.write_text("Implementacao concluida.", encoding="utf-8")
        elif agent_name == "reviewer":
            output_path.write_text('{"approved": true, "summary": "ok"}', encoding="utf-8")
        else:
            output_path.write_text(f"Unexpected agent: {agent_name}", encoding="utf-8")

    monkeypatch.delenv("BALI_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_LLM_COMMAND", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Corrigir logins", dry_run=False, workflow="operate")

    assert res == 0
    assert calls == ["orchestrator", "spec-implementer", "reviewer"]


def test_runtime_retries_step_when_reviewer_rejects(temp_project_dir, monkeypatch):
    calls = []
    specialist_runs = 0
    reviewer_runs = 0

    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        nonlocal specialist_runs, reviewer_runs
        calls.append(agent_name)
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "small",
                        "max_retries": 1,
                        "steps": [
                            {
                                "agent": "spec-implementer",
                                "prompt": "Corrigir logins",
                                "review": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
        elif agent_name == "spec-implementer":
            specialist_runs += 1
            output_path.write_text(
                "Implementacao sem testes." if specialist_runs == 1 else "Implementacao com testes.",
                encoding="utf-8",
            )
        elif agent_name == "reviewer":
            reviewer_runs += 1
            if reviewer_runs == 1:
                output_path.write_text(
                    '{"approved": false, "blockers": [{"reason": "faltam testes"}]}',
                    encoding="utf-8",
                )
            else:
                output_path.write_text('{"approved": true, "summary": "ok"}', encoding="utf-8")

    monkeypatch.delenv("BALI_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_LLM_COMMAND", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Corrigir logins", dry_run=False, workflow="operate")

    assert res == 0
    assert calls == ["orchestrator", "spec-implementer", "reviewer", "spec-implementer", "reviewer"]


def test_runtime_materializes_permanent_and_temporary_specialists(temp_project_dir, monkeypatch):
    calls = []

    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        calls.append(agent_name)
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "medium",
                        "max_retries": 1,
                        "specialists": [
                            {
                                "id": "spec-payments",
                                "scope": "Pagamentos e webhooks recorrentes",
                                "lifecycle": "permanent",
                            },
                            {
                                "id": "spec-one-shot",
                                "scope": "Investigacao pontual",
                                "lifecycle": "temporary",
                            },
                        ],
                        "steps": [
                            {"agent": "spec-payments", "prompt": "Ajustar checkout", "review": False},
                            {"agent": "spec-one-shot", "prompt": "Comparar alternativa", "review": False},
                        ],
                    }
                ),
                encoding="utf-8",
            )
        else:
            output_path.write_text(f"Output de {agent_name}", encoding="utf-8")

    monkeypatch.delenv("BALI_LLM_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_LLM_COMMAND", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Ajustar checkout", dry_run=False, workflow="operate")

    assert res == 0
    assert (temp_project_dir / ".agent" / "team" / "spec-payments.md").is_file()
    assert not (temp_project_dir / ".agent" / "team" / "spec-one-shot.md").exists()
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "temp-agents" / "spec-one-shot.md").is_file()
    assert calls == ["orchestrator", "spec-payments", "spec-one-shot"]
