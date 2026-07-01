# -*- coding: utf-8 -*-
"""Tests for dynamic Orchestrator-led Bali Runtime execution."""

import json
from pathlib import Path

import pytest

import templates.runtime.bali_runtime as runtime


def _reviewer_verdict(approved=True, summary="Mudanca revisada com escopo, testes, seguranca e regressao verificados.", blockers=None, checks=None):
    if blockers is None:
        blockers = []
    if checks is None:
        checks = {
            "scope": True,
            "tests": True,
            "security": True,
            "regression": True,
        }
    return json.dumps(
        {
            "approved": approved,
            "summary": summary,
            "checks": checks,
            "blockers": blockers,
            "warnings": [],
            "nits": [],
        }
    )


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
    assert plan["execution_mode"] == "sequential"
    assert plan["max_parallel"] == 1
    assert plan["context_scope"] == "minimal"
    assert plan["steps"][0]["agent"] == "spec-implementer"
    assert plan["steps"][0]["depends_on"] == []
    assert plan["steps"][0]["produces"] == []
    assert plan["steps"][0]["consumes"] == []


def test_parse_routing_plan_rejects_missing_json():
    with pytest.raises(ValueError, match="routing plan"):
        runtime._parse_routing_plan("Vou fazer isso sem JSON.")


def test_parse_routing_plan_rejects_parallel_dispatch_by_default():
    output = json.dumps(
        {
            "classification": "medium",
            "execution_mode": "parallel",
            "max_parallel": 2,
            "steps": [
                {"agent": "spec-backend", "prompt": "Criar API"},
                {"agent": "spec-frontend", "prompt": "Criar UI"},
            ],
        }
    )

    with pytest.raises(ValueError, match="sequential|max_parallel"):
        runtime._parse_routing_plan(output)


def test_orchestrator_prompts_define_runtime_routing_plan_contract():
    root_prompt = Path("agents/_spine/orchestrator/AGENT.md").read_text(encoding="utf-8")
    package_prompt = Path("bali_agent/agents/_spine/orchestrator/AGENT.md").read_text(encoding="utf-8")

    for prompt in (root_prompt, package_prompt):
        assert "routing_plan" in prompt
        assert '"classification"' in prompt
        assert '"steps"' in prompt
        assert '"specialists"' in prompt
        assert '"execution_mode"' in prompt
        assert '"max_parallel"' in prompt
        assert '"context_scope"' in prompt
        assert '"depends_on"' in prompt
        assert '"produces"' in prompt
        assert '"consumes"' in prompt


def test_reviewer_gate_rejects_boilerplate_verdict():
    with pytest.raises(ValueError, match="summary|checks|blockers"):
        runtime._reviewer_approved('{"approved": true, "summary": "ok"}')


def test_reviewer_gate_accepts_structured_verdict():
    verdict = {
        "approved": True,
        "summary": "Mudanca validada com testes e sem risco de regressao identificado.",
        "checks": {
            "scope": True,
            "tests": True,
            "security": True,
            "regression": True,
        },
        "blockers": [],
        "warnings": [],
        "nits": [],
    }

    approved, feedback = runtime._reviewer_approved(json.dumps(verdict))

    assert approved is True
    assert feedback == verdict["summary"]


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
            output_path.write_text(_reviewer_verdict(), encoding="utf-8")
        else:
            output_path.write_text(f"Unexpected agent: {agent_name}", encoding="utf-8")

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Corrigir logins", dry_run=False, workflow="operate")

    assert res == 0
    assert calls == ["orchestrator", "spec-implementer", "reviewer", "memory-curator"]


def test_greenfield_runtime_persists_product_spine_artifacts(temp_project_dir, monkeypatch):
    calls = []

    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        calls.append(agent_name)
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "large",
                        "max_retries": 1,
                        "steps": [
                            {"agent": "discovery", "prompt": "Descobrir produto", "review": False},
                            {"agent": "prd-writer", "prompt": "Escrever PRD", "review": False},
                            {"agent": "sdd-architect", "prompt": "Escrever SDD", "review": False},
                            {"agent": "planner", "prompt": "Quebrar tasks", "review": False},
                            {"agent": "spec-implementer", "prompt": "Implementar", "review": True},
                        ],
                    }
                ),
                encoding="utf-8",
            )
        elif agent_name == "reviewer":
            output_path.write_text(_reviewer_verdict(), encoding="utf-8")
        else:
            output_path.write_text(f"Saida controlada de {agent_name}.", encoding="utf-8")

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Criar produto novo", dry_run=False, workflow="greenfield")

    assert res == 0
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").iterdir())
    artifacts = run_dirs[0] / "artifacts"
    assert (artifacts / "discovery.md").read_text(encoding="utf-8") == "Saida controlada de discovery."
    assert (artifacts / "prd.md").read_text(encoding="utf-8") == "Saida controlada de prd-writer."
    assert (artifacts / "sdd.md").read_text(encoding="utf-8") == "Saida controlada de sdd-architect."
    assert (artifacts / "tasks.md").read_text(encoding="utf-8") == "Saida controlada de planner."
    manifest = json.loads((run_dirs[0] / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["workflow"] == "greenfield"
    assert "artifacts/prd.md" in manifest["artifacts"]
    assert "artifacts/sdd.md" in manifest["artifacts"]


def test_runtime_calls_memory_curator_after_approved_run(temp_project_dir, monkeypatch):
    calls = []

    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        calls.append(agent_name)
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "small",
                        "steps": [
                            {"agent": "spec-implementer", "prompt": "Corrigir logins", "review": True}
                        ],
                    }
                ),
                encoding="utf-8",
            )
        elif agent_name == "reviewer":
            output_path.write_text(_reviewer_verdict(), encoding="utf-8")
        elif agent_name == "memory-curator":
            output_path.write_text("Memoria curada do run.", encoding="utf-8")
        else:
            output_path.write_text("Implementacao concluida.", encoding="utf-8")

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Corrigir logins", dry_run=False, workflow="operate")

    assert res == 0
    assert calls == ["orchestrator", "spec-implementer", "reviewer", "memory-curator"]
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").iterdir())
    assert (run_dirs[0] / "artifacts" / "memory-summary.md").read_text(encoding="utf-8") == "Memoria curada do run."
    memory_text = (temp_project_dir / ".agent" / "memory.md").read_text(encoding="utf-8")
    assert "Bali Runtime: Corrigir logins" in memory_text


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
                    _reviewer_verdict(
                        approved=False,
                        summary="Implementacao ainda nao demonstrou testes suficientes.",
                        blockers=[{"severity": "blocker", "reason": "faltam testes"}],
                        checks={
                            "scope": True,
                            "tests": False,
                            "security": True,
                            "regression": True,
                        },
                    ),
                    encoding="utf-8",
                )
            else:
                output_path.write_text(_reviewer_verdict(), encoding="utf-8")
        elif agent_name == "memory-curator":
            output_path.write_text("Memoria do retry aprovado.", encoding="utf-8")

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Corrigir logins", dry_run=False, workflow="operate")

    assert res == 0
    assert calls == ["orchestrator", "spec-implementer", "reviewer", "spec-implementer", "reviewer", "memory-curator"]


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

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Ajustar checkout", dry_run=False, workflow="operate")

    assert res == 0
    assert (temp_project_dir / ".agent" / "team" / "spec-payments.md").is_file()
    assert not (temp_project_dir / ".agent" / "team" / "spec-one-shot.md").exists()
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "temp-agents" / "spec-one-shot.md").is_file()
    assert calls == ["orchestrator", "spec-payments", "spec-one-shot", "memory-curator"]


def test_runtime_passes_contract_metadata_to_dependent_step(temp_project_dir, monkeypatch):
    calls = []

    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        calls.append(agent_name)
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "medium",
                        "specialists": [
                            {
                                "id": "spec-backend",
                                "scope": "APIs e contratos de dados",
                                "lifecycle": "temporary",
                            },
                            {
                                "id": "spec-frontend",
                                "scope": "UI consumidora de contratos",
                                "lifecycle": "temporary",
                            },
                        ],
                        "steps": [
                            {
                                "id": "api-contract",
                                "agent": "spec-backend",
                                "prompt": "Definir UnifiedEvent",
                                "review": False,
                                "produces": ["types/unified-event.ts"],
                            },
                            {
                                "id": "ui-implementation",
                                "agent": "spec-frontend",
                                "prompt": "Consumir UnifiedEvent",
                                "review": False,
                                "depends_on": ["api-contract"],
                                "consumes": ["types/unified-event.ts"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
        else:
            output_path.write_text(f"Output de {agent_name}", encoding="utf-8")

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    res = runtime.run_task(temp_project_dir, "Criar painel", dry_run=False, workflow="operate")

    assert res == 0
    assert calls == ["orchestrator", "spec-backend", "spec-frontend", "memory-curator"]
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").iterdir())
    frontend_prompt = (run_dirs[0] / "spec-frontend.prompt.md").read_text(encoding="utf-8")
    assert "## Step Contract" in frontend_prompt
    assert "Depends on: api-contract" in frontend_prompt
    assert "Consumes: types/unified-event.ts" in frontend_prompt
    assert "Context scope: minimal" in frontend_prompt


def test_runtime_writes_structured_failure_event(temp_project_dir, monkeypatch):
    def fake_run_llm(command_template, prompt_path, output_path, agent_name):
        if agent_name == "orchestrator":
            output_path.write_text(
                json.dumps(
                    {
                        "classification": "small",
                        "steps": [
                            {"agent": "spec-implementer", "prompt": "Corrigir API", "review": False}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            return
        raise RuntimeError("RESOURCE_EXHAUSTED: quota exceeded")

    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)
    monkeypatch.setenv("BALI_SUBAGENT_RUNNER", "fake {prompt_file} {output_file} {agent}")
    monkeypatch.setattr(runtime, "_run_llm", fake_run_llm)

    with pytest.raises(SystemExit) as exc:
        runtime.run_task(temp_project_dir, "Corrigir API", dry_run=False, workflow="operate")

    assert exc.value.code == 1
    run_dirs = list((temp_project_dir / ".agent" / "output" / "runtime").iterdir())
    failure = json.loads((run_dirs[0] / "agent_failed.json").read_text(encoding="utf-8"))
    assert failure["event_type"] == "agent_failed"
    assert failure["agent"] == "spec-implementer"
    assert failure["error_type"] == "rate_limit"
    assert failure["retryable"] is True
