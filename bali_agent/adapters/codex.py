# -*- coding: utf-8 -*-
"""Codex adapter implementation."""

from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter
from bali_agent.core.agent_manager import CORE_TEAM, _mirror_native_agent

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
            agents_dir = codex_dir / "agents"
            if not agents_dir.is_dir():
                problems.append("Falta diretorio .codex/agents/")
            else:
                for agent_id in CORE_TEAM:
                    if not (agents_dir / f"{agent_id}.toml").is_file():
                        problems.append(f"Falta subagente Codex: .codex/agents/{agent_id}.toml")
                
        return len(problems) == 0, problems

    def setup(self) -> None:
        codex_dir = self.target_dir / ".codex"
        codex_dir.mkdir(parents=True, exist_ok=True)
        config = codex_dir / "config.toml"
        if not config.is_file():
            config.write_text("[agents]\nmax_threads = 1\nmax_depth = 1\n", encoding="utf-8")
        agents_dir = codex_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        team_dir = self.target_dir / ".agent" / "team"
        for agent_id in CORE_TEAM:
            source = team_dir / f"{agent_id}.md"
            if source.is_file():
                _mirror_native_agent(self.target_dir, source, "codex")

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": {"value": True, "status": "materialized"},
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": False,
            "background_agents": False
        }
