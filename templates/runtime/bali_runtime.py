#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bali Runtime: executor local para orquestracao de subagentes.

Este runtime existe para ambientes sem subagentes nativos. Ele executa cada
agente como uma etapa isolada, com prompt e output próprios. Qualquer LLM/CLI
preserva contrato, artefatos e revisao separados por agente.
"""

import argparse
import datetime as _dt
import json
import os
import sys
import shlex
import subprocess
import time as _time
from pathlib import Path
from typing import Optional

# Path injection helper to support imports in both repository and target environments
current_dir = os.path.abspath(os.path.dirname(__file__))
templates_parent = None
if os.path.basename(current_dir) == "templates":
    templates_parent = os.path.dirname(current_dir)
elif os.path.basename(os.path.dirname(current_dir)) == "templates":
    templates_parent = os.path.dirname(os.path.dirname(current_dir))
elif os.path.isdir(os.path.join(current_dir, "templates")):
    templates_parent = current_dir
elif os.path.isdir(os.path.join(os.path.dirname(current_dir), "templates")):
    templates_parent = os.path.dirname(current_dir)

if templates_parent and templates_parent not in sys.path:
    sys.path.insert(0, templates_parent)

from templates.core.agent_manager import verify, list_agents, create_agent, load_agent_prompt
from templates.core.llm_client import _truncate_prior
from templates.core.security import _sanitize_llm_command
from templates.core.memory import remember

SPINE = ("orchestrator", "planner", "reviewer")
BASE_AGENTS = ("discovery", "prd-writer", "sdd-architect")
REVIEW_REQUIRED_CHECKS = ("scope", "tests", "security", "regression")
AGENT_ARTIFACTS = {
    "discovery": "discovery.md",
    "prd-writer": "prd.md",
    "sdd-architect": "sdd.md",
    "planner": "tasks.md",
    "memory-curator": "memory-summary.md",
}

def _root(path: str) -> Path:
    return Path(path).resolve()

def _agent_dir(root: Path) -> Path:
    return root / ".agent" / "team"

def _runtime_dir(root: Path) -> Path:
    return root / ".agent" / "runtime"

def _output_dir(root: Path) -> Path:
    return root / ".agent" / "output" / "runtime"

def _agent_output_dir(root: Path) -> Path:
    return root / ".agent" / "output"

def _agent_files(root: Path) -> dict:
    team = _agent_dir(root)
    if not team.is_dir():
        return {}
    agents = {}
    for path in sorted(team.glob("*.md")):
        agents[path.stem] = path
    return agents

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def _extract_json_object(text: str) -> dict:
    json_start = text.find("{")
    if json_start == -1:
        raise ValueError("routing plan JSON ausente na resposta do Orchestrator")

    depth = 0
    json_end = -1
    for index, char in enumerate(text[json_start:], start=json_start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                json_end = index + 1
                break

    if json_end == -1:
        raise ValueError("routing plan JSON incompleto na resposta do Orchestrator")

    try:
        return json.loads(text[json_start:json_end])
    except json.JSONDecodeError as exc:
        raise ValueError(f"routing plan JSON invalido: {exc}") from exc

def _list_field(value: object, field: str) -> list:
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError(f"routing plan field '{field}' deve ser lista de strings")

def _parse_routing_plan(text: str) -> dict:
    plan = _extract_json_object(text)
    classification = plan.get("classification")
    if classification not in {"trivial", "small", "medium", "large"}:
        raise ValueError("routing plan deve declarar classification: trivial, small, medium ou large")

    execution_mode = plan.setdefault("execution_mode", "sequential")
    if execution_mode != "sequential":
        raise ValueError("routing plan deve usar execution_mode sequential")

    try:
        max_parallel = int(plan.setdefault("max_parallel", 1))
    except (TypeError, ValueError) as exc:
        raise ValueError("routing plan max_parallel deve ser inteiro") from exc
    if max_parallel != 1:
        raise ValueError("routing plan max_parallel deve ser 1 para evitar colisao de quota")
    plan["max_parallel"] = max_parallel

    context_scope = plan.setdefault("context_scope", "minimal")
    if context_scope not in {"minimal", "contract", "full"}:
        raise ValueError("routing plan context_scope deve ser minimal, contract ou full")

    if classification != "trivial":
        steps = plan.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError("routing plan nao-trivial deve declarar steps")
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict) or not step.get("agent"):
                raise ValueError("routing plan step deve declarar agent")
            step.setdefault("id", f"step-{index}")
            step["depends_on"] = _list_field(step.get("depends_on"), "depends_on")
            step["produces"] = _list_field(step.get("produces"), "produces")
            step["consumes"] = _list_field(step.get("consumes"), "consumes")

    plan.setdefault("max_retries", 3)
    plan.setdefault("steps", [])
    return plan

def _review_issue_reason(item: dict) -> str:
    reason = item.get("reason") or item.get("description")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Reviewer issues devem declarar reason ou description")
    return reason.strip()

def _review_issue_list(verdict: dict, field: str) -> list:
    value = verdict.get(field)
    if not isinstance(value, list):
        raise ValueError(f"Reviewer deve retornar JSON com {field} como lista")
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"Reviewer field {field} deve conter objetos")
        _review_issue_reason(item)
    return value

def _reviewer_approved(text: str) -> tuple[bool, str]:
    verdict = _extract_json_object(text)
    if "approved" not in verdict or not isinstance(verdict["approved"], bool):
        raise ValueError("Reviewer deve retornar JSON com approved boolean")

    summary = verdict.get("summary")
    if not isinstance(summary, str) or len(summary.strip()) < 12:
        raise ValueError("Reviewer deve retornar summary descritivo")

    checks = verdict.get("checks")
    if not isinstance(checks, dict):
        raise ValueError("Reviewer deve retornar checks estruturados")
    for check in REVIEW_REQUIRED_CHECKS:
        if not isinstance(checks.get(check), bool):
            raise ValueError(f"Reviewer checks.{check} deve ser boolean")

    blockers = _review_issue_list(verdict, "blockers")
    warnings = _review_issue_list(verdict, "warnings")
    nits = _review_issue_list(verdict, "nits")
    failed_checks = [check for check in REVIEW_REQUIRED_CHECKS if not checks[check]]

    if verdict["approved"] and (blockers or failed_checks):
        raise ValueError("Reviewer nao pode aprovar com blockers ou checks falsos")
    if not verdict["approved"] and not blockers and not failed_checks:
        raise ValueError("Reviewer reprovado deve declarar blockers ou checks falsos")

    if blockers:
        feedback = "; ".join(_review_issue_reason(item) for item in blockers)
    elif failed_checks:
        feedback = "checks falharam: " + ", ".join(failed_checks)
    else:
        feedback = summary.strip()
    return verdict["approved"], feedback

def _select_specialist(agents: dict, requested: Optional[str] = None) -> str:
    if requested:
        if requested not in agents:
            raise ValueError(f"Especialista solicitado nao existe: {requested}")
        if not requested.startswith("spec-"):
            raise ValueError(f"Especialista solicitado deve comecar com spec-: {requested}")
        return requested
    for name in sorted(agents):
        if name.startswith("spec-"):
            return name
    return "spec-implementer"

def _materialize_plan_specialists(root: Path, run_dir: Path, agents: dict, plan: dict) -> dict:
    for specialist in plan.get("specialists", []):
        agent_id = specialist.get("id")
        scope = specialist.get("scope", "")
        lifecycle = specialist.get("lifecycle", "temporary")
        if not agent_id or not agent_id.startswith("spec-"):
            raise ValueError("specialist deve declarar id spec-*")
        if agent_id in agents:
            continue

        if lifecycle == "permanent":
            result = create_agent(root, agent_id, scope or agent_id, overwrite=False)
            if result != 0:
                raise ValueError(f"Falha ao criar especialista permanente: {agent_id}")
            agents = _agent_files(root)
        elif lifecycle == "temporary":
            temp_path = run_dir / "temp-agents" / f"{agent_id}.md"
            body = "\n".join(
                [
                    "---",
                    f"id: {agent_id}",
                    "tipo: especialista-temporario",
                    "created_by: bali-runtime",
                    "---",
                    "",
                    f"# {agent_id}",
                    "",
                    "Subagente temporario criado para esta execucao.",
                    "",
                    "## Escopo",
                    scope or agent_id,
                    "",
                ]
            )
            _write(temp_path, body)
            agents[agent_id] = temp_path
        else:
            raise ValueError(f"lifecycle invalido para {agent_id}: {lifecycle}")
    return agents

def _format_contract_items(items: list) -> str:
    return ", ".join(items) if items else "(none)"

def _step_contract_lines(step_contract: Optional[dict]) -> list:
    if not step_contract:
        return []
    step = step_contract.get("step", {})
    return [
        "",
        "## Step Contract",
        f"Step id: {step.get('id', '(none)')}",
        f"Execution mode: {step_contract.get('execution_mode', 'sequential')}",
        f"Max parallel: {step_contract.get('max_parallel', 1)}",
        f"Context scope: {step_contract.get('context_scope', 'minimal')}",
        f"Depends on: {_format_contract_items(step.get('depends_on', []))}",
        f"Produces: {_format_contract_items(step.get('produces', []))}",
        f"Consumes: {_format_contract_items(step.get('consumes', []))}",
        "",
        "Use only the task, listed contract artifacts, and prior output needed for this step.",
    ]

def _classify_failure(exc: Exception) -> tuple[str, bool]:
    text = str(exc).lower()
    if "429" in text or "resource_exhausted" in text or "quota" in text or "rate" in text:
        return "rate_limit", True
    if "timeout" in text or "timed out" in text:
        return "timeout", True
    if "exit" in text or "failed" in text or "error" in text:
        return "worker_error", False
    return exc.__class__.__name__, False

def _write_failure_event(run_dir: Path, agent_name: str, exc: Exception) -> None:
    error_type, retryable = _classify_failure(exc)
    event = {
        "event_type": "agent_failed",
        "timestamp": _dt.datetime.now().isoformat(),
        "agent": agent_name,
        "error_type": error_type,
        "retryable": retryable,
        "message": str(exc),
        "next_retry_at": None,
    }
    if retryable:
        event["next_retry_at"] = (_dt.datetime.now() + _dt.timedelta(seconds=30)).isoformat()
    _write(run_dir / "agent_failed.json", json.dumps(event, indent=2, ensure_ascii=False))

def _artifact_for_agent(agent_name: str) -> Optional[str]:
    return AGENT_ARTIFACTS.get(agent_name)

def _persist_agent_artifact(run_dir: Path, agent_name: str, content: str) -> Optional[str]:
    artifact_name = _artifact_for_agent(agent_name)
    if not artifact_name:
        return None
    artifact_path = run_dir / "artifacts" / artifact_name
    _write(artifact_path, content)
    return str(artifact_path.relative_to(run_dir)).replace("\\", "/")

def _write_run_manifest(
    run_dir: Path,
    *,
    workflow: str,
    task: str,
    status: str,
    plan: Optional[dict],
    steps: list,
    artifacts: list,
) -> None:
    manifest = {
        "workflow": workflow,
        "task": task,
        "status": status,
        "created_at": _dt.datetime.now().isoformat(),
        "classification": plan.get("classification") if plan else None,
        "steps": steps,
        "artifacts": sorted(set(artifacts)),
    }
    _write(run_dir / "run_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

def _run_memory_curator(
    root: Path,
    run_dir: Path,
    command_template: str,
    agents: dict,
    task: str,
    prior: str,
    artifacts: list,
    steps: list,
) -> None:
    if "memory-curator" not in agents:
        return
    prompt = "\n".join(
        [
            "Atualize a memoria curada deste run aprovado.",
            "",
            f"Tarefa: {task}",
            f"Artefatos: {', '.join(artifacts) if artifacts else '(none)'}",
            f"Agentes: {', '.join(step.get('agent', '(unknown)') for step in steps) if steps else '(none)'}",
        ]
    )
    prompt_path = _write_prompt(run_dir, "memory-curator", agents["memory-curator"], prompt, prior)
    output_path = run_dir / "memory-curator.output.md"
    _run_llm(command_template, prompt_path, output_path, "memory-curator")
    memory_text = _read(output_path)
    artifact = _persist_agent_artifact(run_dir, "memory-curator", memory_text)
    if artifact:
        artifacts.append(artifact)
    remember(
        root,
        "task",
        f"Bali Runtime: {task[:80]}",
        memory_text[:1200] or "Run aprovado pelo Bali Runtime.",
        ref=str(run_dir.relative_to(root)),
        files=", ".join(sorted(set(artifacts))) if artifacts else None,
    )

def _write_prompt(
    run_dir: Path,
    agent_name: str,
    agent_path: Path,
    task: str,
    prior_output: str,
    step_contract: Optional[dict] = None,
) -> Path:
    prompt_path = run_dir / f"{agent_name}.prompt.md"
    body = [
        f"# Bali Runtime Agent: {agent_name}",
        "",
        "## Agent Definition",
        _read(agent_path),
        "",
        "## Task",
        task,
        *_step_contract_lines(step_contract),
        "",
        "## Prior Output",
        _truncate_prior(prior_output) or "(none)",
        "",
        "## Output Contract",
        "Return only this agent's result. Do not impersonate other agents.",
    ]
    prompt_path.write_text("\n".join(body), encoding="utf-8")
    return prompt_path

def _run_llm(command_template: str, prompt_path: Path, output_path: Path, agent_name: str) -> None:
    """Executa o LLM CLI com retry exponencial e timeout de 300 segundos."""
    cmd_template = _sanitize_llm_command(command_template)
    command = cmd_template.format(
        prompt_file=str(prompt_path),
        output_file=str(output_path),
        agent=agent_name,
    )
    max_attempts = 3
    delay = 2
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            with output_path.open("w", encoding="utf-8") as out:
                # Security: shlex.split the command and run with shell=False when possible
                # But Ollama / external CLIs usually need shell=True or parsing.
                # To align with Fase 1, we split the command and run with shell=False.
                tokens = shlex.split(command)
                
                # Resolve executable wrapper on Windows
                if os.name == "nt" and tokens:
                    import shutil
                    resolved = shutil.which(tokens[0])
                    if resolved:
                        tokens[0] = resolved
                        
                completed = subprocess.run(
                    tokens,
                    shell=False,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=300  # max 5 minutes (Fase 3.3)
                )
            if completed.returncode == 0:
                return
            last_error = RuntimeError(
                f"LLM command failed for {agent_name} (attempt {attempt}/{max_attempts}) "
                f"with exit {completed.returncode}: {completed.stderr}"
            )
            if attempt < max_attempts:
                print(
                    f"[!] {last_error}. Aguardando {delay}s antes de tentar novamente...",
                    file=sys.stderr,
                )
                _time.sleep(delay)
                delay *= 2
        except FileNotFoundError as exc:
            # Fatal error, do not retry
            raise exc
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                print(
                    f"[!] Erro inesperado ao executar LLM (attempt {attempt}/{max_attempts}): {exc}. "
                    f"Aguardando {delay}s...",
                    file=sys.stderr,
                )
                _time.sleep(delay)
                delay *= 2

    raise last_error

def _build_chain(agents: dict, workflow: str, specialist: str) -> list:
    if workflow == "greenfield":
        return ["orchestrator", "discovery", "prd-writer", "sdd-architect", "planner", specialist, "reviewer"]
    return ["orchestrator", "planner", specialist, "reviewer"]

def run_task(root: Path, task: str, dry_run: bool = False, specialist_name: Optional[str] = None, workflow: str = "operate") -> int:
    """Execute a full agent chain pipeline using the CLI fallback mechanism."""
    problems = verify(root)
    if problems:
        for problem in problems:
            print(f"[!] {problem}", file=sys.stderr)
        return 1

    if not dry_run and os.environ.get("BALI_SUBAGENT_PROVIDER"):
        run_script = root / ".agent" / "templates" / "run.py"
        if not run_script.is_file():
            run_script = root / "templates" / "run.py"
        if run_script.is_file():
            print("[*] BALI_SUBAGENT_PROVIDER detectado. Roteando para o motor agentico...", file=sys.stderr)
            completed = subprocess.run([sys.executable, str(run_script), task])
            return completed.returncode

    agents = _agent_files(root)
    try:
        specialist = _select_specialist(agents, specialist_name)
    except ValueError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2
    if workflow not in ("operate", "greenfield"):
        print("[!] workflow invalido. Use operate ou greenfield.", file=sys.stderr)
        return 2
        
    chain = _build_chain(agents, workflow, specialist)
    missing = [name for name in chain if name not in agents]
    if missing:
        for name in missing:
            print(f"[!] Agente da cadeia ausente: .agent/team/{name}.md", file=sys.stderr)
        return 1
        
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = _output_dir(root) / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        plan = [
            "Bali Runtime dry-run",
            f"Workflow: {workflow}",
            f"Task: {task}",
            "Chain:",
            *[f"{index}. {agent_name}" for index, agent_name in enumerate(chain, start=1)],
            f"Run dir: {run_dir.relative_to(root)}",
        ]
        (run_dir / "dry-run.txt").write_text("\n".join(plan), encoding="utf-8")
        print("\n".join(plan))
        return 0

    command_template = os.environ.get("BALI_SUBAGENT_RUNNER")
    if not command_template:
        print(
            "[!] Runner de subagente nao configurado. Configure BALI_SUBAGENT_RUNNER "
            "com {prompt_file}, {output_file} e {agent}, ou rode com --dry-run.",
            file=sys.stderr,
        )
        return 2

    prior = ""
    current_agent = "orchestrator"
    plan = None
    executed_steps = []
    artifacts = []
    try:
        orchestrator_prompt = _write_prompt(run_dir, "orchestrator", agents["orchestrator"], task, prior)
        orchestrator_output = run_dir / "orchestrator.output.md"
        _run_llm(command_template, orchestrator_prompt, orchestrator_output, "orchestrator")
        orchestrator_text = _read(orchestrator_output)
        plan = _parse_routing_plan(orchestrator_text)
        agents = _materialize_plan_specialists(root, run_dir, agents, plan)

        if plan["classification"] == "trivial":
            _write_run_manifest(
                run_dir,
                workflow=workflow,
                task=task,
                status="completed",
                plan=plan,
                steps=[{"agent": "orchestrator"}],
                artifacts=artifacts,
            )
            print(orchestrator_text)
            print(f"Bali Runtime concluido: {run_dir.relative_to(root)}")
            return 0

        max_retries = int(plan.get("max_retries", 3))
        for index, step in enumerate(plan["steps"], start=1):
            agent_name = step["agent"]
            current_agent = agent_name
            if agent_name not in agents:
                raise ValueError(f"Agente do plano ausente: .agent/team/{agent_name}.md")

            step_prompt = step.get("prompt") or task
            feedback = ""
            approved = False
            for attempt in range(max_retries + 1):
                prompt = step_prompt
                if feedback:
                    prompt += f"\n\nFeedback do Reviewer para corrigir:\n{feedback}"
                step_contract = {
                    "step": step,
                    "execution_mode": plan["execution_mode"],
                    "max_parallel": plan["max_parallel"],
                    "context_scope": plan["context_scope"],
                }
                prompt_path = _write_prompt(run_dir, agent_name, agents[agent_name], prompt, prior, step_contract)
                output_path = run_dir / f"{index:02d}-{agent_name}-attempt-{attempt + 1}.output.md"
                _run_llm(command_template, prompt_path, output_path, agent_name)
                prior = _read(output_path)
                artifact = _persist_agent_artifact(run_dir, agent_name, prior)
                if artifact:
                    artifacts.append(artifact)
                executed_steps.append(
                    {
                        "id": step.get("id"),
                        "agent": agent_name,
                        "attempt": attempt + 1,
                        "review": bool(step.get("review", True)),
                        "output": str(output_path.relative_to(run_dir)).replace("\\", "/"),
                    }
                )

                if not step.get("review", True):
                    approved = True
                    break

                review_prompt = f"Revise a saida do agente {agent_name} para a tarefa:\n{prompt}\n\nSaida:\n{prior}"
                current_agent = "reviewer"
                reviewer_prompt = _write_prompt(run_dir, "reviewer", agents["reviewer"], review_prompt, prior)
                reviewer_output = run_dir / f"{index:02d}-reviewer-attempt-{attempt + 1}.output.md"
                _run_llm(command_template, reviewer_prompt, reviewer_output, "reviewer")
                reviewer_text = _read(reviewer_output)
                approved, feedback = _reviewer_approved(reviewer_text)
                if approved:
                    break
                current_agent = agent_name

            if not approved:
                raise RuntimeError(f"Reviewer reprovou {agent_name}: {feedback}")
        _run_memory_curator(root, run_dir, command_template, agents, task, prior, artifacts, executed_steps)
        _write_run_manifest(
            run_dir,
            workflow=workflow,
            task=task,
            status="completed",
            plan=plan,
            steps=executed_steps,
            artifacts=artifacts,
        )
    except Exception as exc:
        _write_run_manifest(
            run_dir,
            workflow=workflow,
            task=task,
            status="failed",
            plan=plan,
            steps=executed_steps,
            artifacts=artifacts,
        )
        _write_failure_event(run_dir, current_agent, exc)
        print(f"[!] Bali Runtime falhou: {exc}", file=sys.stderr)
        sys.exit(1)  # Grave estado ao sys.exit(1) em vez de abortar silenciosamente (Fase 6)

    print(f"Bali Runtime concluido: {run_dir.relative_to(root)}")
    return 0

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Bali Runtime")
    parser.add_argument("--root", default=".", help="Raiz do projeto com .agent/")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("verify")
    sub.add_parser("list-agents")
    create = sub.add_parser("create-agent")
    create.add_argument("--id", required=True, help="ID do especialista, ex: spec-payments")
    create.add_argument("--scope", required=True, help="Escopo reutilizavel do especialista")
    create.add_argument("--overwrite", action="store_true")
    mem = sub.add_parser("remember")
    mem.add_argument("--kind", required=True, choices=["task", "commit", "pr", "decision", "incident"])
    mem.add_argument("--title", required=True)
    mem.add_argument("--ref", help="ID externo opcional: task, commit SHA, PR, issue ou incidente")
    mem.add_argument("--summary", required=True)
    mem.add_argument("--files")
    mem.add_argument("--tests")
    mem.add_argument("--risks")
    mem.add_argument("--decisions")
    run = sub.add_parser("run")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--workflow", choices=["operate", "greenfield"], default="operate")
    run.add_argument("--specialist", help="Especialista spec-* a ser chamado nesta execucao")
    run.add_argument("task", nargs="+")

    args = parser.parse_args(argv)
    root = _root(args.root)

    if args.command == "verify":
        problems = verify(root)
        if problems:
            for problem in problems:
                print(f"[!] {problem}", file=sys.stderr)
            return 1
        print("Bali Runtime OK")
        return 0
    if args.command == "list-agents":
        return list_agents(root)
    if args.command == "create-agent":
        return create_agent(root, args.id, args.scope, overwrite=args.overwrite)
    if args.command == "remember":
        return remember(
            root,
            args.kind,
            args.title,
            args.summary,
            ref=args.ref,
            files=args.files,
            tests=args.tests,
            risks=args.risks,
            decisions=args.decisions,
        )
    if args.command == "run":
        return run_task(
            root,
            " ".join(args.task),
            dry_run=args.dry_run,
            specialist_name=args.specialist,
            workflow=args.workflow,
        )
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
