# -*- coding: utf-8 -*-
"""Cursor adapter implementation."""

from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

class CursorAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("cursor", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        rule_path = self.target_dir / ".cursor" / "rules" / "bali-agent.mdc"
        if not rule_path.is_file():
            problems.append("Falta a regra MDC do Cursor: .cursor/rules/bali-agent.mdc")
        return len(problems) == 0, problems

    def setup(self) -> None:
        rules_dir = self.target_dir / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        rule_path = rules_dir / "bali-agent.mdc"
        if not rule_path.is_file():
            rule_path.write_text(
                "---\ndescription: Regras gerais de orquestracao do Bali-Agent\nglobs: *\n---\n\n"
                "# Regras Bali-Agent\nOpere sempre com subagentes reais.\n",
                encoding="utf-8"
            )

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": False,
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": False,
            "background_agents": False
        }
