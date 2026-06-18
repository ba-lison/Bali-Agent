# -*- coding: utf-8 -*-
"""Antigravity adapter implementation."""

from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

class AntigravityAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("antigravity", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        skill_path = self.target_dir / ".antigravity" / "skills" / "bali-agent" / "SKILL.md"
        if not skill_path.is_file():
            problems.append("Falta a skill do Antigravity: .antigravity/skills/bali-agent/SKILL.md")
        return len(problems) == 0, problems

    def setup(self) -> None:
        skill_dir = self.target_dir / ".antigravity" / "skills" / "bali-agent"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            skill_path.write_text(
                "---\nname: bali-agent\ndescription: Orquestra o time de subagentes reais do Bali-Agent.\n---\n\n"
                "# Antigravity Skill\nUse subagentes reais sempre.\n",
                encoding="utf-8"
            )

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": True,
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": True,
            "background_agents": True
        }
