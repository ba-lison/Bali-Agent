# -*- coding: utf-8 -*-
"""Command Line Interface for the bali-agent package."""

import argparse
import os
import sys
import shutil
import json
import time
import subprocess
import datetime as _dt
from pathlib import Path
from typing import List, Optional

import bali_agent
from bali_agent.capabilities import build_capability_report
from bali_agent.core.runner import Runner
from bali_agent.core.agent_manager import CORE_TEAM, list_agents, create_agent
from bali_agent.core.memory import remember
from bali_agent.adapters import ADAPTERS

def _get_src_dir() -> Path:
    """Resolve the source directory containing agents, protocols, and templates."""
    package_dir = Path(__file__).parent
    # Check if we are in development repo or packaged install
    if (package_dir.parent / "agents").is_dir():
        return package_dir.parent
    return package_dir

def init_command(target_dir: Path) -> int:
    """Bootstrap a target project with the .agent/ structure and enforcement tools."""
    print(f"\n[+] Inicializando Bali-Agent em: {target_dir}")
    src_dir = _get_src_dir()
    agent_dir = target_dir / ".agent"
    
    # 1. Create structure
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy templates directories
    dirs_to_copy = ["agents", "protocols", "templates", "examples"]
    for d in dirs_to_copy:
        src_p = src_dir / d
        dest_p = agent_dir / d
        if src_p.is_dir():
            if dest_p.is_dir():
                shutil.rmtree(dest_p)
            shutil.copytree(src_p, dest_p)
            print(f"[x] Pasta copiada para .agent: {d}/")
            
    # 2. Setup team md files
    team_dir = agent_dir / "team"
    team_dir.mkdir(parents=True, exist_ok=True)
    
    agent_sources = {
        "orchestrator.md": src_dir / "agents" / "_spine" / "orchestrator" / "AGENT.md",
        "discovery.md": src_dir / "agents" / "discovery" / "AGENT.md",
        "prd-writer.md": src_dir / "agents" / "prd-writer" / "AGENT.md",
        "sdd-architect.md": src_dir / "agents" / "sdd-architect" / "AGENT.md",
        "planner.md": src_dir / "agents" / "_spine" / "planner" / "AGENT.md",
        "reviewer.md": src_dir / "agents" / "_spine" / "reviewer" / "AGENT.md",
        "implementer.md": src_dir / "agents" / "_specialists" / "implementer.md",
        "spec-implementer.md": src_dir / "agents" / "_specialists" / "implementer.md",
        "qa.md": src_dir / "agents" / "_specialists" / "testing.md",
        "security.md": src_dir / "agents" / "_specialists" / "security.md",
        "docs.md": src_dir / "agents" / "_specialists" / "docs.md",
    }
    generated_core_prompts = {
        "recruiter.md": "# Recruiter / Team Builder\n\nVoce e o subagente responsavel por avaliar lacunas recorrentes de competencia no projeto, propor especialistas fixos e evitar criar agentes desnecessarios.\n\n## Contrato\n\n- Crie especialista fixo apenas quando a competencia for recorrente ou estrutural no projeto.\n- Para demandas pontuais, recomende agente temporario.\n- Registre escopo, gatilhos de roteamento e motivo da criacao.\n- Nunca substitua Discovery, PRD Writer ou SDD Architect.\n",
        "memory-curator.md": "# Memory Curator\n\nVoce e o subagente responsavel por transformar resultados aprovados em memoria util do projeto.\n\n## Contrato\n\n- Atualize `.agent/working-context.md` com estado vivo, handoff e riscos ativos.\n- Registre em `.agent/memory.md` apenas decisoes, aprendizados, incidentes, commits, PRs e fatos reutilizaveis.\n- Rejeite logs brutos, segredos, tokens e dados pessoais desnecessarios.\n- Trabalhe depois do Reviewer ou em gates explicitos do Orchestrator.\n",
    }
    for filename, src_p in agent_sources.items():
        dest_p = team_dir / filename
        if src_p.is_file() and not dest_p.is_file():
            shutil.copy2(src_p, dest_p)
    for filename, content in generated_core_prompts.items():
        dest_p = team_dir / filename
        if not dest_p.is_file():
            dest_p.write_text(content, encoding="utf-8")

    # 3. Create manifest and markdown documents
    manifest = agent_dir / "subagent.config.yaml"
    if not manifest.is_file():
        created_at = _dt.datetime.now().isoformat()
        manifest.write_text(f"""# Manifesto do time Bali-Agent
versao_base: "{bali_agent.__version__}"
criado_em: "{created_at}"
runtime_authority: "bali-runtime"
subagents_policy:
  role_play_permitido: false
  fallback_obrigatorio: "bali-runtime"
skills_policy:
  auto_create_permitido: true
  store: ".agent/skills"
  audit_log: ".agent/skills/AUDIT.md"
enforcement_adapters:
  - bali-runtime
time:
  core:
    - orchestrator
    - discovery
    - prd-writer
    - sdd-architect
    - planner
    - implementer
    - qa
    - security
    - reviewer
    - recruiter
    - memory-curator
    - docs
  espinha:
    - orchestrator
    - planner
    - reviewer
  product_spine:
    - discovery
    - prd-writer
    - sdd-architect
  base:
    - discovery
    - prd-writer
    - sdd-architect
  especialistas:
  project_fixed: []
  temporary_policy:
    max_per_task: 3
    promote_after_reuse_count: 3
model_policy:
  default: host-default
  classes:
    cheap-fast:
      fallback: host-default
    balanced:
      fallback: host-default
    strong-coding:
      fallback: host-default
    strong-reasoning:
      fallback: host-default
  agents:
    orchestrator:
      preferred: strong-reasoning
      fallback: host-default
    reviewer:
      preferred: strong-reasoning
      fallback: host-default
    implementer:
      preferred: strong-coding
      fallback: host-default
""", encoding="utf-8")

    # Working context and memory
    working_context = agent_dir / "working-context.md"
    if not working_context.is_file():
        working_context.write_text(
            "# Working Context\n\n## Status Atual\nEm inicialização.\n\n## Progresso Recente\n- [x] Inicialização do framework\n",
            encoding="utf-8"
        )
        
    memory = agent_dir / "memory.md"
    if not memory.is_file():
        memory.write_text("# Memoria Curada do Projeto\n", encoding="utf-8")

    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    audit_file = skills_dir / "AUDIT.md"
    if not audit_file.is_file():
        audit_file.write_text("# Skill Audit\n\n", encoding="utf-8")
        
    task_checklist = agent_dir / "task.md"
    if not task_checklist.is_file():
        task_checklist.write_text("# Tarefa Atual\n- [ ] Executar roteamento inicial\n", encoding="utf-8")

    # 4. Setup Git Hook (Agent Shield)
    git_dir = target_dir / ".git"
    if git_dir.is_dir():
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        shell_hook = src_dir / "templates" / "git-pre-commit-shell"
        if shell_hook.is_file():
            dest_hook = hooks_dir / "pre-commit"
            shutil.copy2(shell_hook, dest_hook)
            os.chmod(dest_hook, 0o755)
            print("[x] Agent Shield: Git pre-commit hook instalado.")

    # 5. Create .gitignore inside .agent/
    gitignore = agent_dir / ".gitignore"
    gitignore.write_text("sessions/\noutput/\nruns/\nmemory.db\nmemory.db-journal\n*.key\n*.pem\n.env\n", encoding="utf-8")
    print("[x] .gitignore configurado em .agent/")
    
    # 6. Copy verify_setup.py and run.py
    shutil.copy2(src_dir / "templates" / "verify_setup.py", agent_dir / "verify_setup.py")
    os.chmod(agent_dir / "verify_setup.py", 0o755)

    runtime_dir = agent_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_dir / "templates" / "runtime" / "bali_runtime.py", runtime_dir / "bali_runtime.py")
    os.chmod(runtime_dir / "bali_runtime.py", 0o755)
    
    # Copy prevent_secrets.py to .agent/hooks/
    hooks_dest = agent_dir / "hooks"
    hooks_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_dir / "templates" / "prevent_secrets.py", hooks_dest / "prevent_secrets.py")
    os.chmod(hooks_dest / "prevent_secrets.py", 0o755)
    
    # Write a simple run.py bootstrapper in .agent/run.py
    run_py = agent_dir / "run.py"
    run_py.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, subprocess\n"
        "if __name__ == '__main__':\n"
        "    completed = subprocess.run([sys.executable, '.agent/runtime/bali_runtime.py', 'run'] + sys.argv[1:])\n"
        "    sys.exit(completed.returncode)\n",
        encoding="utf-8"
    )
    os.chmod(run_py, 0o755)
    print("[x] Bootstrappers copiados: verify_setup.py e run.py")
    
    # Setup surface adapters
    for name, adapter_cls in ADAPTERS.items():
        if name != "bali-runtime":
            try:
                adapter = adapter_cls(target_dir)
                adapter.setup()
            except Exception:
                pass
                
    print("[+] Inicializacao concluida com sucesso!")
    return 0

def verify_command(root: Path) -> int:
    """Verify setup integrity."""
    from bali_agent.core.agent_manager import verify
    problems = verify(root)
    if problems:
        print("[VERIFY] Setup INCOMPLETO:")
        for p in problems:
            print(f"  [!] {p}")
        return 1
    print("[VERIFY] OK: time e adaptadores instalados corretamente.")
    return 0

def run_command(root: Path, task: str, workflow: str = "operate", specialist: Optional[str] = None, dry_run: bool = False) -> int:
    """Run execution task loop."""
    print(f"[*] Iniciando execucao da tarefa: {task}...", file=sys.stderr)
    runtime_script = root / ".agent" / "runtime" / "bali_runtime.py"
    if runtime_script.is_file():
        command = [sys.executable, str(runtime_script), "--root", str(root), "run", "--workflow", workflow]
        if dry_run:
            command.append("--dry-run")
        if specialist:
            command.extend(["--specialist", specialist])
        command.append(task)
        completed = subprocess.run(command)
        return completed.returncode

    chain = ["orchestrator", "planner", specialist or "spec-implementer", "reviewer"]
    if workflow == "greenfield":
        chain = ["orchestrator", "discovery", "prd-writer", "sdd-architect", "planner", specialist or "spec-implementer", "reviewer"]

    if dry_run:
        print("Bali Runtime dry-run")
        print(f"Workflow: {workflow}")
        print(f"Task: {task}")
        print(f"Agentes: {', '.join(chain)}")
        return 0

    runner = Runner(root)
        
    try:
        prior = ""
        for agent_id in chain:
            print(f"[*] Rodando subagente: {agent_id}...", file=sys.stderr)
            prompt = f"Instrucao: {task}\nSaida anterior:\n{prior}"
            prior = runner.run_agent(agent_id, prompt)
            
        print("\n=== VEREDICTO FINAL DA PIPELINE ===")
        print(prior)
        return 0
    except Exception as e:
        print(f"[!] Execucao falhou: {e}", file=sys.stderr)
        return 1

def inspect_runs(root: Path) -> int:
    """Inspect execution trace files and manifests."""
    runtime_dir = root / ".agent" / "output" / "runtime"
    legacy_dir = root / ".agent" / "runs"
    run_dirs = []
    for candidate in (runtime_dir, legacy_dir):
        if candidate.is_dir():
            run_dirs.extend(path for path in candidate.iterdir() if path.is_dir())

    if not run_dirs:
        print("Nenhuma execucao registrada ainda.")
        return 0

    for run_folder in sorted(run_dirs, reverse=True):
        manifest = run_folder / "run_manifest.json"
        legacy_manifest = run_folder / "context_manifest.json"
        dry_run = run_folder / "dry-run.txt"
        trace = run_folder / "trace.jsonl"
        print(f"\nRun ID: {run_folder.name}")
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                agents = [step.get("agent") for step in data.get("steps", []) if step.get("agent")]
                artifacts = data.get("artifacts") or []
                print(f"  Workflow: {data.get('workflow')} | Status: {data.get('status')}")
                print(f"  Tarefa: {data.get('task')}")
                if agents:
                    print(f"  Agentes: {', '.join(agents)}")
                if artifacts:
                    print(f"  Artefatos: {', '.join(artifacts)}")
            except Exception as exc:
                print(f"  [!] Manifesto invalido: {exc}")
        elif legacy_manifest.is_file():
            try:
                with legacy_manifest.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"  Agente: {data.get('agent')} | Redactions: {data.get('redactions')} | Tokens: {data.get('estimated_tokens_used')}")
            except Exception:
                pass
        elif dry_run.is_file():
            lines = dry_run.read_text(encoding="utf-8").splitlines()
            fields = {}
            agents = []
            in_chain = False
            for line in lines:
                if line == "Chain:":
                    in_chain = True
                    continue
                if in_chain and ". " in line:
                    _, agent = line.split(". ", 1)
                    if agent:
                        agents.append(agent)
                    continue
                if ": " in line:
                    key, value = line.split(": ", 1)
                    fields[key] = value
            print("  Tipo: dry-run")
            if fields.get("Workflow"):
                print(f"  Workflow: {fields['Workflow']}")
            if fields.get("Task"):
                print(f"  Tarefa: {fields['Task']}")
            if agents:
                print(f"  Agentes: {', '.join(agents)}")
        if trace.is_file():
            try:
                lines = trace.read_text(encoding="utf-8").splitlines()
                print(f"  Total Eventos: {len(lines)}")
            except Exception:
                pass
    return 0

def _availability_label(available: bool, detail: str = "") -> str:
    status = "available" if available else "unavailable"
    return f"{status} ({detail})" if detail else status


def _not_delivered_label(item_id: str) -> str:
    labels = {
        "runtime.parallel_execution": "not implemented",
        "host.universal_native_isolation": "not guaranteed",
        "model.mandatory_multi_model": "not implemented",
    }
    return labels.get(item_id, "not implemented")

def capability_report(root: Path, as_json: bool = False, strict: bool = False) -> int:
    """Print an operational capability report without enforcing a setup gate by default."""
    report = build_capability_report(root)

    if as_json:
        print(json.dumps(
            {section: [item.to_dict() for item in items] for section, items in report.items()},
            indent=2,
            ensure_ascii=False,
        ))
    else:
        print("Bali Capability Report")
        print(f"Root: {root}")
        print("")
        print("[Delivered]")
        for item in report["delivered"]:
            print(f"- {item.title}: {_availability_label(item.available, item.detail)}")
        print("")
        print("[Contract-dependent]")
        for item in report["contract_dependent"]:
            print(f"- {item.title}: {_availability_label(item.available, item.detail)}")
        print("")
        print("[Host-dependent]")
        for item in report["host_dependent"]:
            print(f"- {item.title}: {_availability_label(item.available, item.detail)}")
        print("")
        print("[Not delivered]")
        for item in report["not_delivered"]:
            print(f"- {item.title}: {_not_delivered_label(item.id)} ({item.detail})")

    if strict:
        unavailable_delivered = [item for item in report["delivered"] if not item.available]
        not_delivered = list(report["not_delivered"])
        return 1 if unavailable_delivered or not_delivered else 0
    return 0

def verify_adapter(root: Path, name: str) -> int:
    """Verify a specific surface adapter configuration."""
    if name not in ADAPTERS:
        print(f"Adapter desconhecido: {name}. Escolha um de: {', '.join(ADAPTERS.keys())}")
        return 2
        
    adapter = ADAPTERS[name](root)
    valid, problems = adapter.verify()
    capabilities = adapter.get_capabilities()
    
    print(f"\nAdapter: {name}")
    print(f"Capacidades: {capabilities}")
    if valid:
        print("Status: VALIDADO OK")
        return 0
    else:
        print("Status: INCOMPLETO")
        for p in problems:
            print(f"  [!] {p}")
        return 1

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Bali-Agent CLI")
    parser.add_argument("--root", default=".", help="Diretório raiz do projeto")
    sub = parser.add_subparsers(dest="command", required=True)
    
    sub.add_parser("init")
    sub.add_parser("verify")
    sub.add_parser("list-agents")
    sub.add_parser("inspect-runs")
    capability = sub.add_parser("capability-report")
    capability.add_argument("--json", action="store_true", dest="as_json")
    capability.add_argument("--strict", action="store_true")
    
    create = sub.add_parser("create-agent")
    create.add_argument("--id", required=True)
    create.add_argument("--scope", required=True)
    create.add_argument("--overwrite", action="store_true")
    
    mem = sub.add_parser("remember")
    mem.add_argument("--kind", required=True, choices=["task", "commit", "pr", "decision", "incident"])
    mem.add_argument("--title", required=True)
    mem.add_argument("--ref")
    mem.add_argument("--summary", required=True)
    mem.add_argument("--files")
    mem.add_argument("--tests")
    mem.add_argument("--risks")
    mem.add_argument("--decisions")
    
    run = sub.add_parser("run")
    run.add_argument("--workflow", choices=["operate", "greenfield"], default="operate")
    run.add_argument("--specialist")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("task", nargs="+")
    
    v_adapter = sub.add_parser("verify-adapter")
    v_adapter.add_argument("name")
    
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    
    if args.command == "init":
        sys.exit(init_command(root))
    elif args.command == "verify":
        sys.exit(verify_command(root))
    elif args.command == "list-agents":
        sys.exit(list_agents(root))
    elif args.command == "create-agent":
        sys.exit(create_agent(root, args.id, args.scope, overwrite=args.overwrite))
    elif args.command == "remember":
        sys.exit(remember(
            root, args.kind, args.title, args.summary,
            ref=args.ref, files=args.files, tests=args.tests,
            risks=args.risks, decisions=args.decisions
        ))
    elif args.command == "run":
        sys.exit(run_command(
            root, " ".join(args.task),
            workflow=args.workflow, specialist=args.specialist, dry_run=args.dry_run
        ))
    elif args.command == "inspect-runs":
        sys.exit(inspect_runs(root))
    elif args.command == "capability-report":
        sys.exit(capability_report(root, as_json=args.as_json, strict=args.strict))
    elif args.command == "verify-adapter":
        sys.exit(verify_adapter(root, args.name))

if __name__ == "__main__":
    main()
