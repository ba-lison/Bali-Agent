#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bali Runtime: fallback universal para subagentes reais.

Este runtime existe para ambientes sem subagentes nativos. Ele executa cada
agente como uma etapa isolada, com prompt e output próprios. Qualquer LLM/CLI
pode ser plugado via BALI_LLM_COMMAND.
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

def _parse_routing_plan(text: str) -> dict:
    plan = _extract_json_object(text)
    classification = plan.get("classification")
    if classification not in {"trivial", "small", "medium", "large"}:
        raise ValueError("routing plan deve declarar classification: trivial, small, medium ou large")

    if classification != "trivial":
        steps = plan.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError("routing plan nao-trivial deve declarar steps")
        for step in steps:
            if not isinstance(step, dict) or not step.get("agent"):
                raise ValueError("routing plan step deve declarar agent")

    plan.setdefault("max_retries", 3)
    plan.setdefault("steps", [])
    return plan

def _reviewer_approved(text: str) -> tuple[bool, str]:
    verdict = _extract_json_object(text)
    if "approved" not in verdict or not isinstance(verdict["approved"], bool):
        raise ValueError("Reviewer deve retornar JSON com approved boolean")
    blockers = verdict.get("blockers", [])
    if blockers:
        feedback = "; ".join(item.get("reason", str(item)) for item in blockers)
    else:
        feedback = verdict.get("summary", "")
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

def _write_prompt(run_dir: Path, agent_name: str, agent_path: Path, task: str, prior_output: str) -> Path:
    prompt_path = run_dir / f"{agent_name}.prompt.md"
    body = [
        f"# Bali Runtime Agent: {agent_name}",
        "",
        "## Agent Definition",
        _read(agent_path),
        "",
        "## Task",
        task,
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

    if not dry_run and os.environ.get("BALI_LLM_PROVIDER"):
        run_script = root / ".agent" / "templates" / "run.py"
        if not run_script.is_file():
            run_script = root / "templates" / "run.py"
        if run_script.is_file():
            print("[*] BALI_LLM_PROVIDER detectado. Roteando para o motor agêntico...", file=sys.stderr)
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

    command_template = os.environ.get("BALI_LLM_COMMAND")
    if not command_template:
        print(
            "[!] BALI_LLM_COMMAND nao configurado. Defina um comando de LLM com "
            "{prompt_file}, {output_file} e {agent}, ou rode com --dry-run.",
            file=sys.stderr,
        )
        return 2

    prior = ""
    try:
        orchestrator_prompt = _write_prompt(run_dir, "orchestrator", agents["orchestrator"], task, prior)
        orchestrator_output = run_dir / "orchestrator.output.md"
        _run_llm(command_template, orchestrator_prompt, orchestrator_output, "orchestrator")
        orchestrator_text = _read(orchestrator_output)
        plan = _parse_routing_plan(orchestrator_text)
        agents = _materialize_plan_specialists(root, run_dir, agents, plan)

        if plan["classification"] == "trivial":
            print(orchestrator_text)
            print(f"Bali Runtime concluido: {run_dir.relative_to(root)}")
            return 0

        max_retries = int(plan.get("max_retries", 3))
        for index, step in enumerate(plan["steps"], start=1):
            agent_name = step["agent"]
            if agent_name not in agents:
                raise ValueError(f"Agente do plano ausente: .agent/team/{agent_name}.md")

            step_prompt = step.get("prompt") or task
            feedback = ""
            approved = False
            for attempt in range(max_retries + 1):
                prompt = step_prompt
                if feedback:
                    prompt += f"\n\nFeedback do Reviewer para corrigir:\n{feedback}"
                prompt_path = _write_prompt(run_dir, agent_name, agents[agent_name], prompt, prior)
                output_path = run_dir / f"{index:02d}-{agent_name}-attempt-{attempt + 1}.output.md"
                _run_llm(command_template, prompt_path, output_path, agent_name)
                prior = _read(output_path)

                if not step.get("review", True):
                    approved = True
                    break

                review_prompt = f"Revise a saida do agente {agent_name} para a tarefa:\n{prompt}\n\nSaida:\n{prior}"
                reviewer_prompt = _write_prompt(run_dir, "reviewer", agents["reviewer"], review_prompt, prior)
                reviewer_output = run_dir / f"{index:02d}-reviewer-attempt-{attempt + 1}.output.md"
                _run_llm(command_template, reviewer_prompt, reviewer_output, "reviewer")
                reviewer_text = _read(reviewer_output)
                approved, feedback = _reviewer_approved(reviewer_text)
                if approved:
                    break

            if not approved:
                raise RuntimeError(f"Reviewer reprovou {agent_name}: {feedback}")
    except Exception as exc:
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
