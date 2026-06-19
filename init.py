#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initializer script for Bali-Agent.

Copies agents, protocols, templates, and configures enforcement adapters.
"""

import os
import sys
import shutil
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

try:
    import readline  # type: ignore
except ImportError:
    pass

def print_banner() -> None:
    banner = """
======================================================================
  [BALI-AGENT AI] -- TIME DE AGENTES HÍBRIDOS (V2.1)
======================================================================
  Orquestração de engenharia moderna baseada em agentes autônomos.
  LLM-Agnostic | Security-First | Human-in-the-Loop
======================================================================
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        print("[BALI-AGENT AI] -- TIME DE AGENTES HÍBRIDOS (V2.1)")

def get_target_directory() -> str:
    print("Este script inicializa o Bali-Agent AI no diretório do seu projeto.")
    print("Os agentes, guias e adaptadores serão copiados para a pasta .agent/")
    print("-" * 70)
    
    while True:
        try:
            target = input("Digite o caminho absoluto para o diretório de destino:\n> ").strip()
            if not target:
                print("O caminho não pode ser vazio. Tente novamente.")
                continue
            
            target = os.path.abspath(target)
            return target
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário.")
            sys.exit(0)

def _copy_if_missing(src_path: str, dest_path: str) -> bool:
    if os.path.exists(dest_path):
        return False
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(src_path, dest_path)
    return True

def _write_if_missing(path: str, content: str) -> bool:
    if os.path.exists(path):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def install_pull_request_template(src_dir: str, target_dir: str) -> None:
    src = os.path.join(src_dir, "templates", "pull_request_template.md")
    if not os.path.exists(src):
        return

    github_dir = os.path.join(target_dir, ".github")
    dest = os.path.join(github_dir, "pull_request_template.md")
    ref_dest = os.path.join(github_dir, "pull_request_template.bali-agent.md")

    try:
        if _copy_if_missing(src, dest):
            print("[x] Template de PR instalado: .github/pull_request_template.md")
        elif _copy_if_missing(src, ref_dest):
            print("[!] .github/pull_request_template.md ja existe e NAO foi sobrescrito.")
            print("    Referencia Bali-Agent salva em .github/pull_request_template.bali-agent.md")
    except Exception as e:
        print(f"[!] Erro ao instalar template de PR: {e}")

def _claude_instruction_body(imports: List[str]) -> str:
    lines = [
        "# Claude Code - Bali-Agent Project Instructions",
        "",
        "Claude Code le CLAUDE.md, nao AGENTS.md. Este arquivo importa a governanca",
        "canonica do projeto para que Claude Code receba as mesmas regras dos outros agentes.",
        "",
        "## Imports",
        "",
    ]
    lines.extend(imports)
    lines.extend([
        "",
        "## Bali-Agent Enforcement",
        "",
        "- O objetivo master e subagentes reais sempre.",
        "- Nao substitua Orchestrator, Planner, especialistas e Reviewer por role-play no mesmo contexto.",
        "- Use `.claude/agents/*.md` quando disponivel; se faltar isolamento, use `python .agent/runtime/bali_runtime.py run \"<tarefa>\"`.",
        "- O hook em `.claude/settings.json` reinjeta estado vivo em `SessionStart` e `UserPromptSubmit`.",
        "",
    ])
    return "\n".join(lines)

def install_claude_project_instructions(target_dir: str, agent_dir: str) -> None:
    claude_dir = os.path.join(target_dir, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    root_claude = os.path.join(target_dir, "CLAUDE.md")
    scoped_claude = os.path.join(claude_dir, "CLAUDE.md")
    ref_claude = os.path.join(claude_dir, "CLAUDE.bali-agent.md")
    bootstrap = os.path.join(agent_dir, "bootstrap-AGENTS.md")

    if not os.path.exists(root_claude):
        imports = ["@AGENTS.md"]
        if os.path.exists(bootstrap):
            imports.append("@.agent/bootstrap-AGENTS.md")
        _write_text(root_claude, _claude_instruction_body(imports))
        print("[x] CLAUDE.md instalado para Claude Code com import de AGENTS.md")
        return

    imports = ["@../AGENTS.md"]
    if os.path.exists(bootstrap):
        imports.append("@../.agent/bootstrap-AGENTS.md")
    content = _claude_instruction_body(imports)
    if not os.path.exists(scoped_claude):
        _write_text(scoped_claude, content)
        print("[x] CLAUDE.md existente preservado. Regras Bali salvas em .claude/CLAUDE.md")
    elif not os.path.exists(ref_claude):
        _write_text(ref_claude, content)
        print("[!] .claude/CLAUDE.md ja existe e NAO foi sobrescrito.")
        print("    Referencia Bali-Agent salva em .claude/CLAUDE.bali-agent.md")

def install_opencode_project_config(target_dir: str) -> None:
    config_path = os.path.join(target_dir, "opencode.json")
    ref_path = os.path.join(target_dir, "opencode.bali-agent.json")
    required = [
        "AGENTS.md",
        ".agent/protocols/subagents.md",
        ".agent/protocols/routing.md",
        ".agent/protocols/memory.md",
        ".agent/working-context.md",
    ]

    try:
        data = _load_json_object(config_path)
        data.setdefault("$schema", "https://opencode.ai/config.json")
        instructions = data.get("instructions")
        if not isinstance(instructions, list):
            instructions = []
        for item in required:
            _append_unique(instructions, item)
        data["instructions"] = instructions
        _write_text(config_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print("[x] Config OpenCode instalada/mesclada: opencode.json")
    except Exception as e:
        fallback = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": required,
        }
        _write_text(ref_path, json.dumps(fallback, indent=2, ensure_ascii=False) + "\n")
        print(f"[!] Erro ao mesclar opencode.json: {e}")
        print("[!] Referencia Bali-Agent salva em opencode.bali-agent.json")

def _default_manifest(target_dir: str) -> str:
    project_name = os.path.basename(os.path.abspath(target_dir)) or "projeto"
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return f"""# Manifesto do time Bali-Agent.
# Objetivo Master: subagentes reais sempre; role-play/simulação não é modo válido.
versao_base: "2.1.0"
projeto: {project_name}
modo: operate
criado_em: "{created_at}"
stack_detectada:
  - linguagem: desconhecida
    framework: desconhecido
    sinais: []
nao_mexer: []
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
      escopo: "Especialista geral inicial. O Setup Agent deve substituir ou complementar com especialistas reais da stack detectada."
subagents_policy:
  objetivo_master: "materializar subagentes reais em todo ambiente"
  role_play_permitido: false
  fallback_obrigatorio: "adapter-nativo-ou-bali-runtime"
enforcement_adapters:
  - bali-runtime
  - claude-code
  - codex
  - opencode
  - cursor
  - antigravity
  - ollama
"""

def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)

def _load_json_object(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}

def _append_unique(items: List[Any], value: Any) -> None:
    if value not in items:
        items.append(value)

def merge_claude_settings(src_settings: str, dest_settings: str) -> None:
    desired = _load_json_object(src_settings)
    desired_hooks = desired.get("hooks") or {}
    if not isinstance(desired_hooks, dict):
        desired_hooks = {}

    data = _load_json_object(dest_settings)
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}

    for event, entries in desired_hooks.items():
        if not isinstance(entries, list):
            continue
        current = hooks.get(event)
        if not isinstance(current, list):
            current = []
        known = {_json_key(entry) for entry in current}
        for entry in entries:
            key = _json_key(entry)
            if key not in known:
                current.append(entry)
                known.add(key)
        hooks[event] = current

    data["hooks"] = hooks
    _write_text(dest_settings, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

def _toml_multiline(value: str) -> str:
    return '"""' + value.replace('"""', '\\"\\"\\"') + '"""'

def _team_agent_files(agent_dir: str) -> List[str]:
    team_dir = os.path.join(agent_dir, "team")
    if not os.path.isdir(team_dir):
        return []
    return [
        os.path.join(team_dir, filename)
        for filename in sorted(os.listdir(team_dir))
        if filename.endswith(".md")
    ]

def _agent_description(agent_id: str) -> str:
    if agent_id == "orchestrator":
        return "Orquestra qualquer pedido e cria subagentes quando faltar especialidade."
    if agent_id == "discovery":
        return "Conduz entrevista, requisitos e contexto de negocio para greenfield/brownfield."
    if agent_id == "prd-writer":
        return "Transforma Discovery em PRD claro, acionavel e validavel."
    if agent_id == "sdd-architect":
        return "Transforma PRD aprovado em SDD tecnico com arquitetura e trade-offs."
    if agent_id == "planner":
        return "Decompoe trabalho nao-trivial em plano executavel por subagentes."
    if agent_id == "reviewer":
        return "Revisa entregas antes da conclusao, focando bugs, riscos e testes."
    return f"Especialista Bali-Agent reutilizavel: {agent_id}."

def materialize_real_subagents(src_dir: str, target_dir: str, agent_dir: str) -> None:
    team_dir = os.path.join(agent_dir, "team")
    os.makedirs(team_dir, exist_ok=True)

    agent_sources = [
        ("orchestrator.md", os.path.join(src_dir, "agents", "_spine", "orchestrator", "AGENT.md")),
        ("discovery.md", os.path.join(src_dir, "agents", "discovery", "AGENT.md")),
        ("prd-writer.md", os.path.join(src_dir, "agents", "prd-writer", "AGENT.md")),
        ("sdd-architect.md", os.path.join(src_dir, "agents", "sdd-architect", "AGENT.md")),
        ("planner.md", os.path.join(src_dir, "agents", "_spine", "planner", "AGENT.md")),
        ("reviewer.md", os.path.join(src_dir, "agents", "_spine", "reviewer", "AGENT.md")),
        ("spec-implementer.md", os.path.join(src_dir, "agents", "_specialists", "implementer.md")),
    ]

    created = []
    for filename, src_path in agent_sources:
        dest_path = os.path.join(team_dir, filename)
        if os.path.exists(src_path) and _copy_if_missing(src_path, dest_path):
            created.append(filename)

    manifest_path = os.path.join(agent_dir, "subagent.config.yaml")
    manifest_created = _write_if_missing(manifest_path, _default_manifest(target_dir))

    claude_agents_dir = os.path.join(target_dir, ".claude", "agents")
    os.makedirs(claude_agents_dir, exist_ok=True)
    mirrored = []
    for filename, _ in agent_sources:
        src_path = os.path.join(team_dir, filename)
        dest_path = os.path.join(claude_agents_dir, filename)
        if os.path.exists(src_path) and _copy_if_missing(src_path, dest_path):
            mirrored.append(filename)

    if created:
        print(f"[x] Subagentes reais criados em .agent/team/: {', '.join(created)}")
    if manifest_created:
        print("[x] Manifesto criado: .agent/subagent.config.yaml")
    if mirrored:
        print(f"[x] Subagentes nativos Claude Code espelhados em .claude/agents/: {', '.join(mirrored)}")

def install_codex_native_agents(target_dir: str, agent_dir: str) -> None:
    codex_dir = os.path.join(target_dir, ".codex")
    agents_dir = os.path.join(codex_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)

    config_path = os.path.join(codex_dir, "config.toml")
    if not os.path.exists(config_path):
        _write_text(config_path, "[agents]\nmax_threads = 6\nmax_depth = 1\n")

    installed = []
    for agent_path in _team_agent_files(agent_dir):
        agent_id = os.path.splitext(os.path.basename(agent_path))[0]
        dest = os.path.join(agents_dir, f"{agent_id}.toml")
        body = _read_text(agent_path)
        content = "\n".join([
            f'name = "{agent_id}"',
            f'description = "{_agent_description(agent_id)}"',
            f"developer_instructions = {_toml_multiline(body)}",
            "",
        ])
        if _write_if_missing(dest, content):
            installed.append(os.path.basename(dest))
    if installed:
        print(f"[x] Subagentes nativos Codex instalados em .codex/agents/: {', '.join(installed)}")

def install_opencode_native_agents(target_dir: str, agent_dir: str) -> None:
    agents_dir = os.path.join(target_dir, ".opencode", "agents")
    os.makedirs(agents_dir, exist_ok=True)
    install_opencode_project_config(target_dir)
    installed = []
    for agent_path in _team_agent_files(agent_dir):
        agent_id = os.path.splitext(os.path.basename(agent_path))[0]
        dest = os.path.join(agents_dir, f"{agent_id}.md")
        body = _read_text(agent_path)
        content = "\n".join([
            "---",
            f"description: {_agent_description(agent_id)}",
            "mode: subagent",
            "---",
            "",
            body,
            "",
        ])
        if _write_if_missing(dest, content):
            installed.append(os.path.basename(dest))
    if installed:
        print(f"[x] Subagentes nativos OpenCode instalados em .opencode/agents/: {', '.join(installed)}")

def install_cursor_adapter(src_dir: str, target_dir: str) -> None:
    rules_dir = os.path.join(target_dir, ".cursor", "rules")
    os.makedirs(rules_dir, exist_ok=True)
    src = os.path.join(src_dir, "templates", "cursor-rule.mdc")
    dest = os.path.join(rules_dir, "bali-agent.mdc")
    if os.path.exists(src) and _copy_if_missing(src, dest):
        print("[x] Adapter Cursor instalado: .cursor/rules/bali-agent.mdc")

def install_antigravity_skill(target_dir: str) -> None:
    # Suporta Antigravity IDE (legado) e Antigravity CLI (agy)
    skill_paths = [
        (".antigravity/skills/bali-agent/SKILL.md", "Antigravity IDE"),
        (".agents/skills/bali-agent/SKILL.md", "Antigravity CLI (agy)"),
    ]
    content = """---
name: bali-agent
description: Materializa o time Bali-Agent com subagentes reais; usa define_subagent/background subagents quando disponiveis e Bali Runtime como fallback.
---

# Bali-Agent para Antigravity

Sempre opere com subagentes reais:

1. Leia `AGENTS.md`, `.agent/subagent.config.yaml` e `.agent/protocols/subagents.md`.
2. Para cada arquivo em `.agent/team/*.md`, defina um subagente Antigravity equivalente quando a ferramenta disponibilizar `define_subagent`.
3. Execute Orchestrator, Planner, especialista e Reviewer como subagentes/threads separados.
4. Se a superficie atual nao permitir subagentes isolados, use `python .agent/runtime/bali_runtime.py run "<tarefa>"`.
5. Se faltar especialista, use `python .agent/runtime/bali_runtime.py create-agent --id spec-<nome> --scope "<escopo>"` e entao invoque o novo subagente.
"""
    for rel_path, label in skill_paths:
        dest = os.path.join(target_dir, rel_path)
        if _write_if_missing(dest, content):
            print(f"[x] Skill Antigravity instalada ({label}): {rel_path}")

def install_native_surface_adapters(src_dir: str, target_dir: str, agent_dir: str) -> None:
    install_codex_native_agents(target_dir, agent_dir)
    install_opencode_native_agents(target_dir, agent_dir)
    install_cursor_adapter(src_dir, target_dir)
    install_antigravity_skill(target_dir)

def install_runtime_and_adapters(src_dir: str, agent_dir: str) -> None:
    runtime_src = os.path.join(src_dir, "templates", "runtime", "bali_runtime.py")
    runtime_dest = os.path.join(agent_dir, "runtime", "bali_runtime.py")
    if os.path.exists(runtime_src):
        os.makedirs(os.path.dirname(runtime_dest), exist_ok=True)
        shutil.copy2(runtime_src, runtime_dest)
        os.chmod(runtime_dest, 0o755)
        print("[x] Bali Runtime instalado/atualizado: .agent/runtime/bali_runtime.py")

    adapters_src = os.path.join(src_dir, "templates", "adapters")
    adapters_dest = os.path.join(agent_dir, "adapters")
    if os.path.isdir(adapters_src):
        os.makedirs(adapters_dest, exist_ok=True)
        installed = []
        for filename in sorted(os.listdir(adapters_src)):
            if not filename.endswith(".md"):
                continue
            src_path = os.path.join(adapters_src, filename)
            dest_path = os.path.join(adapters_dest, filename)
            shutil.copy2(src_path, dest_path)
            installed.append(filename)
        if installed:
            print(f"[x] Adapters universais instalados/atualizados em .agent/adapters/: {', '.join(installed)}")

def initialize_project(src_dir: str, target_dir: str) -> bool:
    print(f"\n[+] Iniciando cópia para: {target_dir}")
    
    agent_dir = os.path.join(target_dir, ".agent")
    
    # Check if already initialized
    manifest_path = os.path.join(agent_dir, "subagent.config.yaml")
    if os.path.exists(manifest_path):
        print(f"[!] Aviso: Bali-Agent já está inicializado neste projeto.")
        is_interactive = sys.stdin.isatty() and not os.environ.get("PYTEST_CURRENT_TEST")
        if is_interactive:
            try:
                confirm = input("Deseja sobrescrever e atualizar a base do framework? (S/N)\n> ").strip().lower()
                if confirm not in ["s", "sim", "y", "yes"]:
                    print("Operação cancelada pelo usuário.")
                    return False
            except KeyboardInterrupt:
                print("\nOperação cancelada.")
                return False
        else:
            print("[*] Sobrescrevendo a base automaticamente (modo não-interativo).")

    os.makedirs(agent_dir, exist_ok=True)
            
    # Subdirectories to copy recursively to .agent/
    dirs_to_copy = ["agents", "protocols", "templates", "examples"]
    
    for item in dirs_to_copy:
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(agent_dir, item)
        
        if not os.path.exists(src_path):
            print(f"[!] Aviso: Fonte não encontrada: {src_path}")
            continue
            
        try:
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            print(f"[x] Pasta copiada para .agent: {item}/")
        except Exception as e:
            print(f"[!] Erro ao copiar pasta {item}: {e}")

    try:
        materialize_real_subagents(src_dir, target_dir, agent_dir)
    except Exception as e:
        print(f"[!] Erro ao materializar subagentes reais: {e}")

    try:
        install_runtime_and_adapters(src_dir, agent_dir)
    except Exception as e:
        print(f"[!] Erro ao instalar Bali Runtime/adapters: {e}")

    try:
        install_native_surface_adapters(src_dir, target_dir, agent_dir)
    except Exception as e:
        print(f"[!] Erro ao instalar adaptadores nativos das ferramentas: {e}")

    install_pull_request_template(src_dir, target_dir)

    # Core files to place in root
    files_to_copy = [("AGENTS.md", "AGENTS.md"), ("README.md", "README.md")]
    
    for src_file, dest_file in files_to_copy:
        src_path = os.path.join(src_dir, src_file)
        dest_path = os.path.join(target_dir, dest_file)
        if os.path.exists(src_path):
            try:
                if os.path.exists(dest_path):
                    if dest_file == "AGENTS.md":
                        bootstrap_dest = os.path.join(agent_dir, "bootstrap-AGENTS.md")
                        shutil.copy2(src_path, bootstrap_dest)
                        print(f"[x] AGENTS.md existente preservado. Referencia salva em .agent/bootstrap-AGENTS.md")
                    else:
                        print(f"[x] README.md existente preservado na raiz.")
                else:
                    shutil.copy2(src_path, dest_path)
                    print(f"[x] Arquivo copiado para raiz: {dest_file}")
            except Exception as e:
                print(f"[!] Erro ao copiar {dest_file}: {e}")

    install_claude_project_instructions(target_dir, agent_dir)
            
    # Copy template instances
    dest_working_context = os.path.join(agent_dir, "working-context.md")
    if not os.path.exists(dest_working_context):
        src_working_context = os.path.join(src_dir, "templates", "working-context.md")
        if os.path.exists(src_working_context):
            shutil.copy2(src_working_context, dest_working_context)
            print("[x] Memória de trabalho criada: .agent/working-context.md")

    dest_memory = os.path.join(agent_dir, "memory.md")
    if not os.path.exists(dest_memory):
        src_memory = os.path.join(src_dir, "templates", "memory.md")
        if os.path.exists(src_memory):
            shutil.copy2(src_memory, dest_memory)
            print("[x] Memoria curada criada: .agent/memory.md")

    dest_task = os.path.join(agent_dir, "task.md")
    if not os.path.exists(dest_task):
        src_task = os.path.join(src_dir, "templates", "task.md")
        if os.path.exists(src_task):
            shutil.copy2(src_task, dest_task)
            print("[x] Checklist de tarefa criado: .agent/task.md")

    # Copy hooks
    hooks_dir = os.path.join(agent_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    
    src_prevent_secrets = os.path.join(src_dir, "templates", "prevent_secrets.py")
    dest_prevent_secrets = os.path.join(hooks_dir, "prevent_secrets.py")
    if os.path.exists(src_prevent_secrets):
        shutil.copy2(src_prevent_secrets, dest_prevent_secrets)
        os.chmod(dest_prevent_secrets, 0o755)
        print("[x] Hook prevent_secrets.py copiado para .agent/hooks/")

    src_claude_hook = os.path.join(src_dir, "templates", "claude_hook.py")
    dest_claude_hook = os.path.join(hooks_dir, "claude_hook.py")
    if os.path.exists(src_claude_hook):
        shutil.copy2(src_claude_hook, dest_claude_hook)
        os.chmod(dest_claude_hook, 0o755)
        print("[x] Hook claude_hook.py copiado para .agent/hooks/")

    src_claude_settings = os.path.join(src_dir, "templates", "claude-settings.json")
    if os.path.exists(src_claude_settings):
        claude_dir = os.path.join(target_dir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        dest_claude_settings = os.path.join(claude_dir, "settings.json")
        try:
            merge_claude_settings(src_claude_settings, dest_claude_settings)
            print("[x] Settings Claude Code mesclado.")
        except Exception:
            ref_settings = os.path.join(claude_dir, "settings.bali-agent.json")
            shutil.copy2(src_claude_settings, ref_settings)

    src_verify = os.path.join(src_dir, "templates", "verify_setup.py")
    dest_verify = os.path.join(agent_dir, "verify_setup.py")
    if os.path.exists(src_verify):
        shutil.copy2(src_verify, dest_verify)
        os.chmod(dest_verify, 0o755)
        print("[x] Verificador de setup copiado para .agent/verify_setup.py")

    src_run = os.path.join(src_dir, "templates", "run.py")
    dest_run = os.path.join(agent_dir, "run.py")
    if os.path.exists(src_run):
        shutil.copy2(src_run, dest_run)
        os.chmod(dest_run, 0o755)
        print("[x] Engine de runtime copiado para .agent/run.py")

    # Setup Git pre-commit hook (Agent Shield) if target is a git repository
    git_dir = os.path.join(target_dir, ".git")
    if os.path.isdir(git_dir):
        git_hooks = os.path.join(git_dir, "hooks")
        os.makedirs(git_hooks, exist_ok=True)
        src_shell_hook = os.path.join(src_dir, "templates", "git-pre-commit-shell")
        dest_shell_hook = os.path.join(git_hooks, "pre-commit")
        if os.path.exists(src_shell_hook):
            shutil.copy2(src_shell_hook, dest_shell_hook)
            os.chmod(dest_shell_hook, 0o755)
            print("[x] Agent Shield: Git pre-commit hook instalado.")

    # Write .agent/.gitignore to ignore local execution artifacts
    agent_gitignore = os.path.join(agent_dir, ".gitignore")
    gitignore_content = """# Ignorar outputs e sessoes locais do runtime Bali-Agent
sessions/
output/
memory.db
memory.db-journal
*.key
*.pem
.env
"""
    _write_text(agent_gitignore, gitignore_content)
    print("[x] .gitignore criado em .agent/.gitignore")

    output_dir = os.path.join(agent_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    gitkeep = os.path.join(output_dir, ".gitkeep")
    if not os.path.exists(gitkeep):
        _write_text(gitkeep, "")
    print("[x] Pasta de outputs configurada: .agent/output/")
    
    return True

def print_success_instructions(target_dir: str) -> None:
    try:
        print("\n" + "=" * 70)
        print("SUCCESS: BALI-AGENT AI INICIALIZADO COM SUCESSO!")
        print("=" * 70)
        print(f"\nDiretório: {target_dir}\n")
        print("Próximos passos para começar:")
        print("1. Abra o diretório do seu projeto na sua IDE favorita.")
        print("2. Digite a seguinte mensagem no chat do assistente:")
        print("   > Setup do time")
        print("=" * 70 + "\n")
    except UnicodeEncodeError:
        print(f"\nBali-Agent AI inicializado com sucesso em {target_dir}")

def main() -> None:
    src_dir = os.path.dirname(os.path.abspath(__file__))
    print_banner()
    target_dir = get_target_directory()
    
    print(f"\nVocê confirma a inicialização em: {target_dir}? (S/N)")
    try:
        confirm = input("> ").strip().lower()
        if confirm not in ["s", "sim", "y", "yes"]:
            print("Operação cancelada.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        sys.exit(0)
        
    initialize_project(src_dir, target_dir)
    print_success_instructions(target_dir)

if __name__ == "__main__":
    main()
