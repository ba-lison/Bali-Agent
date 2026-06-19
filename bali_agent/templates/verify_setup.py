#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador deterministico do setup do time Bali-Agent.

Roda dentro de um projeto APOS o "Setup do time" e confirma que o time e os
adaptadores de enforcement foram realmente instalados.

Uso: python .agent/verify_setup.py   (rodar na raiz do projeto)
"""
import os
import sys
import json

try:
    import yaml
except ImportError:
    yaml = None

MIN_PYTHON = (3, 11)


def verify(project_root):
    """Retorna uma lista de problemas (strings). Lista vazia = setup OK."""
    problems = []
    agent_dir = os.path.join(project_root, ".agent")

    if sys.version_info < MIN_PYTHON:
        current = ".".join(str(part) for part in sys.version_info[:3])
        problems.append(f"Python 3.11+ requerido; versao atual: {current}")

    manifest = os.path.join(agent_dir, "subagent.config.yaml")
    if not os.path.isfile(manifest):
        problems.append("Manifesto ausente: .agent/subagent.config.yaml")
        return problems  # sem manifesto nao da pra continuar

    data = None
    if yaml is not None:
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            problems.append(f"Manifesto invalido (YAML): {e}")

    team_dir = os.path.join(agent_dir, "team")
    spine_members = ("orchestrator.md", "planner.md", "reviewer.md")
    base_members = ("discovery.md", "prd-writer.md", "sdd-architect.md")
    for member in ("orchestrator.md", "planner.md", "reviewer.md"):
        if not os.path.isfile(os.path.join(team_dir, member)):
            problems.append(f"Membro da espinha ausente: .agent/team/{member}")
    for member in base_members:
        if not os.path.isfile(os.path.join(team_dir, member)):
            problems.append(f"Agente base ausente: .agent/team/{member}")

    specs = []
    if os.path.isdir(team_dir):
        specs = [f for f in os.listdir(team_dir)
                 if f.startswith("spec-") and f.endswith(".md")]
        if not specs:
            problems.append("Nenhum especialista gerado: .agent/team/spec-*.md")

    if not os.path.isfile(os.path.join(agent_dir, "working-context.md")):
        problems.append("Memoria de trabalho ausente: .agent/working-context.md")
    if not os.path.isfile(os.path.join(agent_dir, "memory.md")):
        problems.append("Memoria curada ausente: .agent/memory.md")

    runtime_path = os.path.join(agent_dir, "runtime", "bali_runtime.py")
    if not os.path.isfile(runtime_path):
        problems.append("Bali Runtime ausente: .agent/runtime/bali_runtime.py")

    adapters_dir = os.path.join(agent_dir, "adapters")
    for adapter_file in (
        "antigravity.md",
        "claude-code.md",
        "codex.md",
        "cursor.md",
        "ollama.md",
        "opencode.md",
    ):
        if not os.path.isfile(os.path.join(adapters_dir, adapter_file)):
            problems.append(f"Adapter universal ausente: .agent/adapters/{adapter_file}")

    if isinstance(data, dict):
        policy = data.get("subagents_policy") or {}
        if policy.get("role_play_permitido") is not False:
            problems.append("Politica invalida: subagents_policy.role_play_permitido deve ser false")
        fallback = str(policy.get("fallback_obrigatorio") or "")
        if "bali-runtime" not in fallback:
            problems.append("Politica invalida: fallback_obrigatorio deve exigir adapter nativo ou bali-runtime")

    if not os.path.isfile(os.path.join(agent_dir, "run.py")):
        problems.append("Engine de runtime ausente: .agent/run.py")

    adapters = data.get("enforcement_adapters") or [] if isinstance(data, dict) else []
    if isinstance(data, dict):
        if not adapters:
            problems.append("Manifesto invalido: enforcement_adapters deve declarar pelo menos bali-runtime")
        elif "bali-runtime" not in adapters:
            problems.append("Manifesto invalido: enforcement_adapters deve incluir bali-runtime")
    checks = {
        "bali-runtime": [runtime_path],
        "claude-code": [
            os.path.join(project_root, ".claude", "settings.json"),
            os.path.join(agent_dir, "hooks", "claude_hook.py"),
        ],
        "codex": [os.path.join(project_root, ".codex", "config.toml")],
        "opencode": [os.path.join(project_root, ".opencode", "agents")],
        "cursor": [os.path.join(project_root, ".cursor", "rules", "bali-agent.mdc")],
        "antigravity": [
            os.path.join(project_root, ".antigravity", "skills", "bali-agent", "SKILL.md"),
            os.path.join(project_root, ".agents", "skills", "bali-agent", "SKILL.md"),
        ],
    }
    for adapter in adapters:
        for path in checks.get(adapter, []):
            if not os.path.exists(path):
                rel = os.path.relpath(path, project_root)
                problems.append(f"Adaptador '{adapter}' incompleto: falta {rel}")
        if adapter == "claude-code":
            if not (
                os.path.isfile(os.path.join(project_root, "CLAUDE.md"))
                or os.path.isfile(os.path.join(project_root, ".claude", "CLAUDE.md"))
            ):
                problems.append("Claude Code sem instrucoes persistentes: falta CLAUDE.md ou .claude/CLAUDE.md")
            settings_path = os.path.join(project_root, ".claude", "settings.json")
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                hooks = settings.get("hooks") or {}
                if "SessionStart" not in hooks or "UserPromptSubmit" not in hooks:
                    problems.append("Claude Code sem hooks Bali-Agent: faltam SessionStart/UserPromptSubmit em .claude/settings.json")
            except Exception as e:
                problems.append(f"Claude Code settings invalido: {e}")
            native_dir = os.path.join(project_root, ".claude", "agents")
            for member in list(spine_members) + list(base_members) + specs:
                path = os.path.join(native_dir, member)
                if not os.path.isfile(path):
                    rel = os.path.relpath(path, project_root)
                    problems.append(f"Subagente nativo Claude Code ausente: {rel}")
        if adapter == "codex":
            native_dir = os.path.join(project_root, ".codex", "agents")
            for member in list(spine_members) + list(base_members) + specs:
                stem = os.path.splitext(member)[0]
                path = os.path.join(native_dir, f"{stem}.toml")
                if not os.path.isfile(path):
                    rel = os.path.relpath(path, project_root)
                    problems.append(f"Subagente nativo Codex ausente: {rel}")
        if adapter == "opencode":
            opencode_config = os.path.join(project_root, "opencode.json")
            if not os.path.isfile(opencode_config):
                problems.append("OpenCode sem config de instrucoes: falta opencode.json")
            else:
                try:
                    with open(opencode_config, "r", encoding="utf-8") as f:
                        opencode_data = json.load(f)
                    instructions = opencode_data.get("instructions") or []
                    for required in ("AGENTS.md", ".agent/protocols/subagents.md", ".agent/protocols/routing.md"):
                        if required not in instructions:
                            problems.append(f"OpenCode sem instrucao obrigatoria em opencode.json: {required}")
                except Exception as e:
                    problems.append(f"OpenCode config invalido: {e}")
            native_dir = os.path.join(project_root, ".opencode", "agents")
            for member in list(spine_members) + list(base_members) + specs:
                path = os.path.join(native_dir, member)
                if not os.path.isfile(path):
                    rel = os.path.relpath(path, project_root)
                    problems.append(f"Subagente nativo OpenCode ausente: {rel}")

    return problems


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    problems = verify(root)
    if problems:
        print("[VERIFY-SETUP] Setup INCOMPLETO:")
        for p in problems:
            print(f"  [!] {p}")
        sys.exit(1)
    print("[VERIFY-SETUP] OK: time e adaptadores instalados corretamente.")
    sys.exit(0)


if __name__ == "__main__":
    main()
