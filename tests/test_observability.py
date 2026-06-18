# -*- coding: utf-8 -*-
"""Unit tests for execution tracing and logging."""

import pytest
import json
from pathlib import Path
from bali_agent.core.event_log import EventLogger

def test_observability_event_logging(temp_project_dir):
    logger = EventLogger(temp_project_dir, "test-run-456")
    
    # Log different events
    logger.log_event("agent_start", {"agent": "orchestrator"})
    logger.log_tool_call("read_file", {"path": "main.py"}, "File content...")
    logger.log_approval("Run dangerous cmd?", "approved")
    logger.save_final_diff("diff --git a/main.py b/main.py...")
    logger.save_reviewer_report("# Reviewer report\nAll good.")
    
    # Assert trace file exists and contains events
    trace_path = temp_project_dir / ".agent" / "runs" / "test-run-456" / "trace.jsonl"
    assert trace_path.is_file()
    
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    
    event_start = json.loads(lines[0])
    assert event_start["event_type"] == "agent_start"
    
    # Assert json collections are valid
    tool_calls = temp_project_dir / ".agent" / "runs" / "test-run-456" / "tool_calls.json"
    assert tool_calls.is_file()
    
    approvals = temp_project_dir / ".agent" / "runs" / "test-run-456" / "approvals.json"
    assert approvals.is_file()
    
    # Assert other artifacts
    assert (temp_project_dir / ".agent" / "runs" / "test-run-456" / "final_diff.patch").is_file()
    assert (temp_project_dir / ".agent" / "runs" / "test-run-456" / "reviewer_report.md").is_file()
