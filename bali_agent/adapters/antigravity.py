# -*- coding: utf-8 -*-
"""Antigravity adapter — suporta Antigravity 2.0 (desktop app), Antigravity IDE e Antigravity CLI (agy).

Antigravity 2.0 (desktop app, VS Code fork com Editor + Manager views):
  - Skills de workspace em .antigravity/skills/<skill>/SKILL.md
  - Manager view: orquestracao nativa de multiplos agentes em paralelo
  - define_subagent + background subagents nativos

Antigravity CLI (agy, ex-Gemini CLI, terminal-first):
  - Skills de workspace em .agents/skills/<skill>/SKILL.md
  - Skills globais em ~/.gemini/skills/<skill>/SKILL.md

Este adapter escreve em AMBOS os paths para compatibilidade maxima.
"""

from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

# Caminhos de skills suportados
SKILL_PATHS = [
    ".antigravity/skills/bali-agent/SKILL.md",   # Antigravity 2.0 desktop app + IDE
    ".agents/skills/bali-agent/SKILL.md",         # Antigravity CLI (agy) — workspace
]

GLOBAL_SKILL_PATH = "~/.gemini/skills/bali-agent/SKILL.md"  # Antigravity CLI — global

SKILL_CONTENT_HEADER = (
    "---\n"
    "name: bali-agent\n"
    "description: Orquestra o time de subagentes reais do Bali-Agent. "
    "Topologia hub-and-spoke. Use para qualquer tarefa de engenharia de software.\n"
    "---\n\n"
)


class AntigravityAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("antigravity", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        # Verifica se pelo menos um dos paths de skill existe
        skill_found = False
        for rel_path in SKILL_PATHS:
            skill_path = self.target_dir / rel_path
            if skill_path.is_file():
                skill_found = True
                break
        if not skill_found:
            problems.append(
                "Falta a skill do Antigravity. Nenhum arquivo encontrado em: "
                + ", ".join(SKILL_PATHS)
            )
        return len(problems) == 0, problems

    def setup(self) -> None:
        # Escreve em todos os paths de skill para compatibilidade maxima
        for rel_path in SKILL_PATHS:
            skill_path = self.target_dir / rel_path
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            if not skill_path.is_file():
                skill_path.write_text(
                    SKILL_CONTENT_HEADER
                    + "# Antigravity Skill\n"
                    + "Use subagentes reais sempre.\n",
                    encoding="utf-8"
                )

    def get_capabilities(self) -> dict:
        """Return adapter capabilities.

        O Antigravity CLI (agy) suporta:
          - native_subagents: define_subagent + background agents
          - permissions: sandbox nativo de terminal
          - background_agents: subagentes paralelos em background
        """
        return {
            "native_subagents":  {"value": True,  "status": "verified"},
            "pre_tool_hooks":    {"value": False, "status": "verified"},
            "post_tool_hooks":   {"value": False, "status": "verified"},
            "session_hooks":     {"value": False, "status": "verified"},
            "permissions":       {"value": True,  "status": "declared"},
            "background_agents": {"value": True,  "status": "declared"},
        }
