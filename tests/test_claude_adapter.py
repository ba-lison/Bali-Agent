# -*- coding: utf-8 -*-
"""Tests for Claude Code native subagent materialization."""

from pathlib import Path

from bali_agent.adapters.claude import ClaudeAdapter


def test_claude_adapter_materializes_core_team_native_agents(temp_project_dir):
    adapter = ClaudeAdapter(temp_project_dir)

    adapter.setup()

    required_agents = [
        "orchestrator",
        "discovery",
        "prd-writer",
        "sdd-architect",
        "planner",
        "implementer",
        "qa",
        "security",
        "reviewer",
        "recruiter",
        "memory-curator",
        "docs",
    ]
    for agent_id in required_agents:
        path = temp_project_dir / ".claude" / "agents" / f"{agent_id}.md"
        assert path.is_file(), f"missing {path}"

    claude_md = (temp_project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "@.claude/agents/orchestrator.md" in claude_md
    assert "@protocols/subagents.md" in claude_md

    valid, problems = adapter.verify()
    assert valid, problems
