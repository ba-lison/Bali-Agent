# -*- coding: utf-8 -*-
"""OpenCode adapter implementation."""

import json
from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter
from bali_agent.core.agent_manager import CORE_TEAM, _mirror_native_agent

class OpenCodeAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("opencode", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        config = self.target_dir / "opencode.json"
        
        if not config.is_file():
            problems.append("Falta arquivo config: opencode.json")
        else:
            try:
                with config.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                instructions = data.get("instructions", [])
                for required in ("AGENTS.md", ".agent/protocols/subagents.md", ".agent/protocols/routing.md"):
                    if required not in instructions:
                        problems.append(f"OpenCode sem instrucao obrigatoria: {required}")
                agents_dir = self.target_dir / ".opencode" / "agents"
                if not agents_dir.is_dir():
                    problems.append("Falta diretorio .opencode/agents/")
                else:
                    for agent_id in CORE_TEAM:
                        if not (agents_dir / f"{agent_id}.md").is_file():
                            problems.append(f"Falta subagente OpenCode: .opencode/agents/{agent_id}.md")
            except Exception as e:
                problems.append(f"Configuracao opencode.json invalida: {e}")
                
        return len(problems) == 0, problems

    def setup(self) -> None:
        config = self.target_dir / "opencode.json"
        required = [
            "AGENTS.md",
            ".agent/protocols/subagents.md",
            ".agent/protocols/routing.md",
            ".agent/protocols/memory.md",
            ".agent/working-context.md",
        ]
        default_config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": required
        }
        if not config.is_file():
            with config.open("w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        agents_dir = self.target_dir / ".opencode" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        team_dir = self.target_dir / ".agent" / "team"
        for agent_id in CORE_TEAM:
            source = team_dir / f"{agent_id}.md"
            if source.is_file():
                _mirror_native_agent(self.target_dir, source, "opencode")

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": {"value": True, "status": "materialized"},
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": False,
            "background_agents": False
        }
