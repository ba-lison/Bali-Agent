# -*- coding: utf-8 -*-
"""Unit tests for the ToolPolicy engine."""

import pytest
from pathlib import Path
from bali_agent.core.policy import ToolPolicy

def test_policy_risk_classification():
    policy = ToolPolicy(Path("."))
    
    from bali_agent.security.command_policy import classify_command
    level, allowed = classify_command("pytest tests/")
    assert allowed
    assert level == "R2"
    
    level, allowed = classify_command("rm -rf /")
    assert not allowed
    assert level == "R4"
    
    # Also verify the policy wrapper behaves correctly
    allowed, cmd = policy.can_execute("orchestrator", "pytest tests/")
    assert allowed
    assert cmd == "pytest tests/"
    
    allowed, err = policy.can_execute("orchestrator", "rm -rf /")
    assert not allowed
    assert "risco" in err or "risk_class" in err

def test_policy_path_sandboxing(temp_project_dir):
    policy = ToolPolicy(temp_project_dir)
    
    # Allowed read within root
    allowed, path = policy.can_read("orchestrator", "working-context.md")
    assert allowed
    
    # Traversal blocked
    allowed, err = policy.can_read("orchestrator", "../../../etc/passwd")
    assert not allowed
    assert "traversal" in err

def test_policy_path_policy_exclusions(temp_project_dir):
    policy = ToolPolicy(temp_project_dir)
    
    # Block reading secrets or .env files
    allowed, err = policy.can_read("orchestrator", ".env")
    assert not allowed
    assert "Acesso negado" in err
    
    allowed, err = policy.can_read("orchestrator", "secrets/db.key")
    assert not allowed
    assert "Acesso negado" in err

def test_policy_redaction():
    policy = ToolPolicy(Path("."))
    content = "My key is sk-1234567890abcdef1234567890abcdef and secret is sk_test_yourstripetokenherefortest123"
    redacted = policy.redact("orchestrator", content)
    assert "[REDACTED OPENAI / ANTHROPIC API KEY]" in redacted
    assert "[REDACTED STRIPE TOKEN]" in redacted
