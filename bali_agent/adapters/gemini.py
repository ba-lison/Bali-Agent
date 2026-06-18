# -*- coding: utf-8 -*-
"""Gemini CLI adapter implementation."""

import json
from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

class GeminiAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("gemini", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        settings = self.target_dir / ".gemini" / "settings.json"
        if not settings.is_file():
            problems.append("Falta configuracoes Gemini: .gemini/settings.json")
        return len(problems) == 0, problems

    def setup(self) -> None:
        gemini_dir = self.target_dir / ".gemini"
        gemini_dir.mkdir(parents=True, exist_ok=True)
        settings = gemini_dir / "settings.json"
        if not settings.is_file():
            default_settings = {
                "context": {
                    "fileName": ["AGENTS.md", "GEMINI.md"]
                }
            }
            with settings.open("w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=2, ensure_ascii=False)

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": False,
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": False,
            "background_agents": False
        }
