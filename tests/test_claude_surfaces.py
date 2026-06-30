# -*- coding: utf-8 -*-
"""Documentation contract for Claude Code surface support."""

from pathlib import Path


def test_claude_adapter_documents_supported_surfaces_and_runtime_fallback():
    docs = [
        Path("README.md"),
        Path("AGENTS.md"),
        Path("templates/adapters/claude-code.md"),
        Path("bali_agent/templates/adapters/claude-code.md"),
        Path("docs/adapters.md"),
        Path("protocols/subagents.md"),
        Path("bali_agent/protocols/subagents.md"),
        Path("agents/_setup/AGENT.md"),
        Path("bali_agent/agents/_setup/AGENT.md"),
    ]

    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "Claude Code" in text
        assert ".claude/agents" in text
        assert "Bali Runtime" in text
        assert "subagentes" in text or "subagents" in text
        assert "Claude Code IDE" not in text
