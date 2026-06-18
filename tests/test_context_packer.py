# -*- coding: utf-8 -*-
"""Unit tests for the ContextPacker."""

import pytest
from pathlib import Path
from bali_agent.core.context import ContextPacker

def test_context_packer_manifest_and_redaction(temp_project_dir):
    # Create the index.py file to allow context packer to resolve it
    (temp_project_dir / "index.py").write_text("# dummy file content", encoding="utf-8")
    
    packer = ContextPacker(temp_project_dir)
    
    messages = [
        {"role": "system", "content": "Keep it safe."},
        {"role": "user", "content": "My secret key is sk-1234567890abcdef1234567890abcdef in the index.py file."}
    ]
    
    # Pack context and assert redactions count and manifest contents
    packed, manifest = packer.pack_context(
        agent_id="planner",
        messages=messages,
        max_tokens=12000,
        run_id="test-run-123"
    )
    
    assert manifest["redactions"] == 1
    assert manifest["token_budget"] == 12000
    assert "[REDACTED OPENAI / ANTHROPIC API KEY]" in packed[1]["content"]
    assert "index.py" in manifest["included_files"]
    
    # Manifest JSON was saved
    saved_manifest = temp_project_dir / ".agent" / "runs" / "test-run-123" / "context_manifest.json"
    assert saved_manifest.is_file()
