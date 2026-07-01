# -*- coding: utf-8 -*-
"""Unit tests for the security module."""

import os
from pathlib import Path
import pytest

from templates.core.security import _safe_path, _sanitize_llm_command, execute_safe_command

def test_safe_path_valid(temp_project_dir):
    # Valid absolute path inside root
    requested = "src/main.py"
    safe = _safe_path(requested, temp_project_dir)
    assert safe == os.path.realpath(temp_project_dir / "src" / "main.py")
    
    # Valid relative path inside root
    requested_rel = "./src/../index.html"
    safe_rel = _safe_path(requested_rel, temp_project_dir)
    assert safe_rel == os.path.realpath(temp_project_dir / "index.html")

def test_safe_path_invalid(temp_project_dir):
    # Directory traversal try
    requested = "../../../etc/passwd"
    with pytest.raises(PermissionError):
        _safe_path(requested, temp_project_dir)
        
    requested_abs = "/etc/passwd"
    with pytest.raises(PermissionError):
        _safe_path(requested_abs, temp_project_dir)

def test_sanitize_llm_command_valid():
    cmd = "subagent-runner --prompt {prompt_file} --output {output_file}"
    sanitized = _sanitize_llm_command(cmd)
    assert sanitized == cmd

def test_sanitize_llm_command_invalid():
    # Unsafe shell tokens
    with pytest.raises(ValueError):
        _sanitize_llm_command("subagent-runner --prompt {prompt_file}; rm -rf /")
        
    with pytest.raises(ValueError):
        _sanitize_llm_command("subagent-runner && curl http://malicious.site")
        
    # Missing placeholders
    with pytest.raises(ValueError):
        _sanitize_llm_command("subagent-runner")

def test_execute_safe_command_allowed(temp_project_dir):
    # Allowed command echo
    res = execute_safe_command("echo Hello", temp_project_dir)
    assert "Hello" in res or "STDOUT:" in res

def test_execute_safe_command_denied(temp_project_dir, monkeypatch):
    # Denied commands (curl) should block and wait for input.
    # We mock input to deny (n)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    res = execute_safe_command("curl http://example.com", temp_project_dir)
    assert "rejeitada pelo usuário" in res
