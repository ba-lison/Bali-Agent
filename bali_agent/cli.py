# -*- coding: utf-8 -*-
"""Command Line Interface for the bali-agent package."""

import argparse
import os
import sys
import shutil
import json
import time
import datetime as _dt
from pathlib import Path
from typing import List, Optional

import bali_agent
from bali_agent.core.runner import Runner
from bali_agent.core.agent_manager import list_agents, create_agent
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
    
    agent_sources = [
        ("orchestrator.md", src_dir / "agents" / "_spine" / "orchestrator" / "AGENT.md"),
        ("discovery.md", src_dir / "agents" / "discovery" / "AGENT.md"),
        ("prd-writer.md", src_dir / "agents" / "prd-writer" / "AGENT.md"),
        ("sdd-architect.md", src_dir / "agents" / "sdd-architect" / "AGENT.md"),
        ("planner.md", src_dir / "agents" / "_spine" / "planner" / "AGENT.md"),
        ("reviewer.md", src_dir / "agents" / "_spine" / "reviewer" / "AGENT.md"),
        ("spec-implementer.md", src_dir / "agents" / "_specialists" / "implementer.md"),
    ]
    for filename, src_p in agent_sources:
        dest_p = team_dir / filename
        if src_p.is_file() and not dest_p.is_file():
            shutil.copy2(src_p, dest_p)

    # 3. Create manifest and markdown documents
    manifest = agent_dir / "subagent.config.yaml"
    if not manifest.is_file():
        created_at = _dt.datetime.now().isoformat()
        manifest.write_text(f"""# Manifesto do time Bali-Agent
versao_base: "{bali_agent.__version__}"
criado_em: "{created_at}"
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
      escopo: "Especialista geral"
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
        "    completed = subprocess.run(['bali', 'run'] + sys.argv[1:])\n"
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

def run_command(root: Path, task: str, workflow: str = "operate", specialist: Optional[str] = None) -> int:
    """Run execution task loop."""
    print(f"[*] Iniciando execucao da tarefa: {task}...", file=sys.stderr)
    runner = Runner(root)
    
    # Build chain
    chain = ["orchestrator", "planner", specialist or "spec-implementer", "reviewer"]
    if workflow == "greenfield":
        chain = ["orchestrator", "discovery", "prd-writer", "sdd-architect", "planner", specialist or "spec-implementer", "reviewer"]
        
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
    runs_dir = root / ".agent" / "runs"
    if not runs_dir.is_dir():
        print("Nenhuma execucao registrada ainda.")
        return 0
        
    for run_folder in sorted(runs_dir.iterdir(), reverse=True):
        if run_folder.is_dir():
            manifest = run_folder / "context_manifest.json"
            trace = run_folder / "trace.jsonl"
            print(f"\nRun ID: {run_folder.name}")
            if manifest.is_file():
                try:
                    with manifest.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    print(f"  Agente: {data.get('agent')} | Redactions: {data.get('redactions')} | Tokens: {data.get('estimated_tokens_used')}")
                except Exception:
                    pass
            if trace.is_file():
                try:
                    lines = trace.read_text(encoding="utf-8").splitlines()
                    print(f"  Total Eventos: {len(lines)}")
                except Exception:
                    pass
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
            workflow=args.workflow, specialist=args.specialist
        ))
    elif args.command == "inspect-runs":
        sys.exit(inspect_runs(root))
    elif args.command == "verify-adapter":
        sys.exit(verify_adapter(root, args.name))

if __name__ == "__main__":
    main()
