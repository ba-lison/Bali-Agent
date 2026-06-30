# -*- coding: utf-8 -*-
"""Agent Manager module for verifying configurations, listing, and creating subagents."""

import os
import re
import sys
import datetime as _dt
from pathlib import Path
from typing import List, Dict, Optional, Union

CORE_TEAM = (
    "orchestrator",
    "discovery",
    "prd-writer",
    "sdd-architect",
    "planner",
    "implementer",
    "qa",
    "security",
    "reviewer",
    "recruiter",
    "memory-curator",
    "docs",
)
SPINE = ("orchestrator", "planner", "reviewer")
BASE_AGENTS = ("discovery", "prd-writer", "sdd-architect")
SPEC_ID_RE = re.compile(r"^spec-[a-z0-9][a-z0-9-]*$")

def _agent_dir(root: Path) -> Path:
    return root / ".agent" / "team"

def _runtime_dir(root: Path) -> Path:
    return root / ".agent" / "runtime"

def _memory_path(root: Path) -> Path:
    return root / ".agent" / "memory.md"

def _agent_files(root: Path) -> Dict[str, Path]:
    team = _agent_dir(root)
    if not team.is_dir():
        return {}
    agents = {}
    for path in sorted(team.glob("*.md")):
        agents[path.stem] = path
    return agents

def _escape_yaml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')

def verify(root: Path) -> List[str]:
    """Verify the completeness and validity of the Bali-Agent installation."""
    problems = []
    agent_root = root / ".agent"
    if not agent_root.is_dir():
        problems.append("Pasta .agent ausente")
        return problems

    manifest = agent_root / "subagent.config.yaml"
    if not manifest.is_file():
        problems.append("Manifesto ausente: .agent/subagent.config.yaml")
    else:
        try:
            manifest_text = manifest.read_text(encoding="utf-8")
            if "role_play_permitido: false" not in manifest_text:
                problems.append("Manifesto deve conter subagents_policy.role_play_permitido: false")
            if "bali-runtime" not in manifest_text:
                problems.append("Manifesto deve exigir fallback com bali-runtime")
            if "enforcement_adapters:" not in manifest_text:
                problems.append("Manifesto deve declarar enforcement_adapters")
            for required_key in ("product_spine:", "project_fixed:", "temporary_policy:", "model_policy:"):
                if required_key not in manifest_text:
                    problems.append(f"Manifesto deve declarar {required_key.rstrip(':')}")
        except Exception as e:
            problems.append(f"Erro ao ler manifesto: {e}")

    agents = _agent_files(root)
    for name in CORE_TEAM:
        if name not in agents:
            problems.append(f"Subagente core obrigatorio ausente: .agent/team/{name}.md")
            
    if not _memory_path(root).is_file():
        problems.append("Memoria curada ausente: .agent/memory.md")

    return problems

def list_agents(root: Path) -> int:
    """List all agents registered in the team directory."""
    problems = verify(root)
    if problems:
        # Do not fail list_agents completely if there are minor verification warnings
        blocking = [p for p in problems if not p.startswith("Nenhum especialista real")]
        if blocking:
            for problem in blocking:
                print(f"[!] {problem}", file=sys.stderr)
            return 1
    for name, path in _agent_files(root).items():
        print(f"{name}\t{path.relative_to(root)}")
    return 0

def _append_specialist_to_manifest(root: Path, agent_id: str, scope: str) -> bool:
    manifest = root / ".agent" / "subagent.config.yaml"
    if not manifest.is_file():
        return False

    text = manifest.read_text(encoding="utf-8")
    if f"id: {agent_id}" in text or f'id: "{agent_id}"' in text:
        return False

    block = (
        f"    - id: {agent_id}\n"
        f"      arquivo: .agent/team/{agent_id}.md\n"
        f"      escopo: \"{_escape_yaml(scope)}\"\n"
    )
    marker = "  especialistas:\n"
    marker_at = text.find(marker)
    if marker_at == -1:
        addition = (
            "\ntime:\n"
            "  especialistas:\n"
            f"{block}"
        )
        manifest.write_text(text.rstrip() + "\n" + addition, encoding="utf-8")
        return True

    insert_start = marker_at + len(marker)
    next_top_level = re.search(r"(?m)^\S", text[insert_start:])
    insert_at = len(text) if next_top_level is None else insert_start + next_top_level.start()
    updated = text[:insert_at].rstrip() + "\n" + block + text[insert_at:]
    manifest.write_text(updated, encoding="utf-8")
    return True

def _mirror_native_agent(root: Path, agent_path: Path, adapter_type: str) -> bool:
    """Helper to mirror the agent md definition to native directories if present."""
    if adapter_type == "claude":
        native_dir = root / ".claude" / "agents"
        if not native_dir.is_dir():
            return False
        dest = native_dir / agent_path.name
        dest.write_text(agent_path.read_text(encoding="utf-8"), encoding="utf-8")
        return True
    elif adapter_type == "codex":
        native_dir = root / ".codex" / "agents"
        if not native_dir.is_dir():
            return False
        agent_id = agent_path.stem
        body = agent_path.read_text(encoding="utf-8")
        safe_body = body.replace('"""', '\\"\\"\\"')
        content = "\n".join([
            f'name = "{agent_id}"',
            f'description = "Especialista Bali-Agent: {agent_id}"',
            f'developer_instructions = """{safe_body}"""',
            "",
        ])
        dest = native_dir / f"{agent_id}.toml"
        dest.write_text(content, encoding="utf-8")
        return True
    elif adapter_type == "opencode":
        native_dir = root / ".opencode" / "agents"
        if not native_dir.is_dir():
            return False
        agent_id = agent_path.stem
        body = agent_path.read_text(encoding="utf-8")
        content = "\n".join([
            "---",
            f"description: Especialista Bali-Agent: {agent_id}",
            "mode: subagent",
            "---",
            "",
            body,
            "",
        ])
        dest = native_dir / f"{agent_id}.md"
        dest.write_text(content, encoding="utf-8")
        return True
    return False

def create_agent(root: Path, agent_id: str, scope: str, overwrite: bool = False) -> int:
    """Create a new specialist agent, updating configs and native mirrors."""
    problems = verify(root)
    blocking = [p for p in problems if not p.startswith("Nenhum especialista real")]
    if blocking:
        for problem in blocking:
            print(f"[!] {problem}", file=sys.stderr)
        return 1

    if not SPEC_ID_RE.match(agent_id):
        print("[!] id invalido. Use o formato spec-nome-do-especialista.", file=sys.stderr)
        return 2

    agent_path = _agent_dir(root) / f"{agent_id}.md"
    if agent_path.exists() and not overwrite:
        print(f"[!] Subagente ja existe: {agent_path.relative_to(root)}", file=sys.stderr)
        return 2

    body = f"""---
id: {agent_id}
tipo: especialista
created_by: bali-runtime
---

# {agent_id}

Voce e um subagente especialista real do time Bali-Agent.

## Escopo

{scope}

## Contrato

- Execute apenas tarefas dentro deste escopo.
- Registre achados, decisoes e arquivos tocados de forma objetiva.
- Nao substitua Orchestrator, Planner ou Reviewer no mesmo contexto.
- Ao concluir, entregue resultado para o Reviewer como agente separado.
"""
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text(body, encoding="utf-8")
    
    _append_specialist_to_manifest(root, agent_id, scope)
    
    mirrors = []
    if _mirror_native_agent(root, agent_path, "claude"):
        mirrors.append(".claude/agents")
    if _mirror_native_agent(root, agent_path, "codex"):
        mirrors.append(".codex/agents")
    if _mirror_native_agent(root, agent_path, "opencode"):
        mirrors.append(".opencode/agents")
        
    log_file = root / ".agent" / "output" / "subagents-created.md"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    line = f"- {stamp} `{agent_id}`: {scope}\n"
    if not log_file.exists():
        log_file.write_text("# Subagentes Criados Dinamicamente\n\n", encoding="utf-8")
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line)

    print(f"Subagente criado: {agent_path.relative_to(root)}")
    for mirror in mirrors:
        print(f"Espelho nativo atualizado: {mirror}")
    print("Registro atualizado: .agent/output/subagents-created.md")
    return 0

def load_agent_prompt(root: Path, agent_name: str) -> str:
    """Load the AGENT.md or MD prompt for a given agent name. Raise FileNotFoundError if missing."""
    search_paths = [
        root / ".agent" / "team" / f"{agent_name}.md",
        root / ".agent" / "team" / f"spec-{agent_name}.md",
    ]
    team_dir = root / ".agent" / "team"
    if team_dir.is_dir():
        for f in os.listdir(str(team_dir)):
            if f.startswith(f"spec-{agent_name}") and f.endswith(".md"):
                search_paths.insert(0, team_dir / f)

    for path in search_paths:
        if path.is_file():
            return path.read_text(encoding="utf-8")
            
    raise FileNotFoundError(f"Instrucoes/Prompt para subagente '{agent_name}' nao encontradas.")
