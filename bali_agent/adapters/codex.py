# -*- coding: utf-8 -*-
"""Codex adapter implementation."""

from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

class CodexAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("codex", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        codex_dir = self.target_dir / ".codex"
        
        if not codex_dir.is_dir():
            problems.append("Pasta .codex ausente")
        else:
            config = codex_dir / "config.toml"
            if not config.is_file():
                problems.append("Falta arquivo .codex/config.toml")
                
        return len(problems) == 0, problems

    def setup(self) -> None:
        codex_dir = self.target_dir / ".codex"
        codex_dir.mkdir(parents=True, exist_ok=True)
        config = codex_dir / "config.toml"
        if not config.is_file():
            config.write_text("[agents]\nmax_threads = 1\nmax_depth = 1\n", encoding="utf-8")

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": True,
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": False,
            "background_agents": False
        }
