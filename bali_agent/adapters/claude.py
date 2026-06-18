# -*- coding: utf-8 -*-
"""Claude Code adapter implementation."""

import os
import json
from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter

class ClaudeAdapter(BaseAdapter):
    def __init__(self, target_dir: Path):
        super().__init__("claude-code", target_dir)

    def verify(self) -> Tuple[bool, List[str]]:
        problems = []
        
        # Check settings.json
        settings_path = self.target_dir / ".claude" / "settings.json"
        if not settings_path.is_file():
            problems.append("Falta o arquivo de configuracoes: .claude/settings.json")
        else:
            try:
                with settings_path.open("r", encoding="utf-8") as f:
                    settings = json.load(f)
                hooks = settings.get("hooks", {})
                if "SessionStart" not in hooks or "UserPromptSubmit" not in hooks:
                    problems.append("Claude Code sem hooks: faltam SessionStart/UserPromptSubmit em settings.json")
            except Exception as e:
                problems.append(f"Configuracao .claude/settings.json invalida: {e}")

        # Check CLAUDE.md
        claude_md = self.target_dir / "CLAUDE.md"
        if not claude_md.is_file():
            problems.append("Falta o arquivo de instrucoes: CLAUDE.md")

        return len(problems) == 0, problems

    def setup(self) -> None:
        claude_dir = self.target_dir / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        
        # Write default settings with hooks
        settings_path = claude_dir / "settings.json"
        default_settings = {
            "hooks": {
                "SessionStart": ["python", ".agent/hooks/claude_hook.py"],
                "UserPromptSubmit": ["python", ".agent/hooks/claude_hook.py"]
            }
        }
        if not settings_path.is_file():
            with settings_path.open("w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=2, ensure_ascii=False)
                
        # Write CLAUDE.md
        claude_md = self.target_dir / "CLAUDE.md"
        if not claude_md.is_file():
            claude_md.write_text(
                "# Claude Code - Bali-Agent Project Instructions\n\n"
                "Imports: @AGENTS.md\n",
                encoding="utf-8"
            )

    def get_capabilities(self) -> dict:
        return {
            "native_subagents": True,
            "pre_tool_hooks": True,
            "post_tool_hooks": True,
            "session_hooks": True,
            "permissions": True,
            "background_agents": True
        }
