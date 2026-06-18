#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador deterministico do setup do time Bali-Agent.

Roda dentro de um projeto APOS o "Setup do time" e confirma que o time e os
adaptadores de enforcement foram realmente instalados.

Uso: python .agent/verify_setup.py   (rodar na raiz do projeto)
"""
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


def verify(project_root):
    """Retorna uma lista de problemas (strings). Lista vazia = setup OK."""
    problems = []
    agent_dir = os.path.join(project_root, ".agent")

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
    for member in ("orchestrator.md", "planner.md", "reviewer.md"):
        if not os.path.isfile(os.path.join(team_dir, member)):
            problems.append(f"Membro da espinha ausente: .agent/team/{member}")

    if os.path.isdir(team_dir):
        specs = [f for f in os.listdir(team_dir)
                 if f.startswith("spec-") and f.endswith(".md")]
        if not specs:
            problems.append("Nenhum especialista gerado: .agent/team/spec-*.md")

    if not os.path.isfile(os.path.join(agent_dir, "working-context.md")):
        problems.append("Memoria de trabalho ausente: .agent/working-context.md")

    if not os.path.isfile(os.path.join(agent_dir, "run.py")):
        problems.append("Engine de runtime ausente: .agent/run.py")

    adapters = data.get("enforcement_adapters") or [] if isinstance(data, dict) else []
    checks = {
        "claude-code": [
            os.path.join(project_root, ".claude", "settings.json"),
            os.path.join(agent_dir, "hooks", "claude_hook.py"),
        ],
        "cursor": [os.path.join(project_root, ".cursor", "rules", "subagent.mdc")],
        "gemini": [os.path.join(project_root, ".gemini", "settings.json")],
    }
    for adapter in adapters:
        for path in checks.get(adapter, []):
            if not os.path.exists(path):
                rel = os.path.relpath(path, project_root)
                problems.append(f"Adaptador '{adapter}' incompleto: falta {rel}")

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
