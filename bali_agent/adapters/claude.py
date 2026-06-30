# -*- coding: utf-8 -*-
"""Claude Code adapter implementation."""

import os
import json
from pathlib import Path
from typing import Tuple, List

from bali_agent.adapters.base import BaseAdapter
from bali_agent.core.agent_manager import CORE_TEAM


def _default_agent_prompt(agent_id: str) -> str:
    title = agent_id.replace("-", " ").title()
    return (
        f"# {title}\n\n"
        "Voce e um subagente real do time Bali-Agent.\n\n"
        "## Contrato\n\n"
        "- Receba contexto minimo do Orchestrator.\n"
        "- Execute somente o escopo delegado.\n"
        "- Entregue resultado estruturado para o proximo gate.\n"
        "- Nao faca role-play de outros agentes no mesmo contexto.\n"
    )

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

        agents_dir = self.target_dir / ".claude" / "agents"
        if not agents_dir.is_dir():
            problems.append("Falta o diretorio de subagentes: .claude/agents/")
        else:
            for agent_id in CORE_TEAM:
                if not (agents_dir / f"{agent_id}.md").is_file():
                    problems.append(f"Falta subagente Claude Code: .claude/agents/{agent_id}.md")

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
            agent_imports = "\n".join(f"@.claude/agents/{agent_id}.md" for agent_id in CORE_TEAM)
            claude_md.write_text(
                "# Claude Code - Bali-Agent Project Instructions\n\n"
                "@AGENTS.md\n\n"
                "# Protocolos criticos\n"
                "@protocols/subagents.md\n"
                "@protocols/routing.md\n"
                "@protocols/memory.md\n"
                "@protocols/handoff.md\n\n"
                "# Subagentes nativos\n"
                f"{agent_imports}\n",
                encoding="utf-8"
            )

        agents_dir = claude_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        team_dir = self.target_dir / ".agent" / "team"
        for agent_id in CORE_TEAM:
            source = team_dir / f"{agent_id}.md"
            body = source.read_text(encoding="utf-8") if source.is_file() else _default_agent_prompt(agent_id)
            dest = agents_dir / f"{agent_id}.md"
            if not dest.is_file():
                dest.write_text(body, encoding="utf-8")

    def get_capabilities(self) -> dict:
        """Return adapter capabilities with verification status.

        capability_status values:
          - "verified"  : Checked at runtime by verify() method.
          - "declared"  : Documented by Claude Code but not verified by bali verify.
        """
        return {
            "native_subagents":   {"value": True,  "status": "verified"},
            "pre_tool_hooks":     {"value": True,  "status": "verified"},   # checked via settings.json hooks
            "post_tool_hooks":    {"value": True,  "status": "declared"},   # hook format varies by CC version
            "session_hooks":      {"value": True,  "status": "verified"},   # SessionStart/UserPromptSubmit in verify()
            "permissions":        {"value": True,  "status": "declared"},   # permissions model not inspectable at verify time
            "background_agents":  {"value": True,  "status": "declared"},   # requires active CC session to confirm
        }
