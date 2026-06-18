# -*- coding: utf-8 -*-
"""Ollama/Local CLI adapter implementation."""

import os
from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

class OllamaAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("ollama", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        if not os.environ.get("BALI_LLM_COMMAND") and not os.environ.get("BALI_LLM_PROVIDER"):
            problems.append("Defina a variavel de ambiente BALI_LLM_COMMAND ou BALI_LLM_PROVIDER para usar o runtime local.")
        return len(problems) == 0, problems

    def setup(self) -> None:
        pass

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": False,
            "pre_tool_hooks": False,
            "post_tool_hooks": False,
            "session_hooks": False,
            "permissions": False,
            "background_agents": False
        }
