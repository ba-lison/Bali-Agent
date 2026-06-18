# -*- coding: utf-8 -*-
"""Observability module generating structured trace logs and run artifacts."""

import os
import json
import datetime as _dt
from pathlib import Path
from typing import Dict, Any

class EventLogger:
    def __init__(self, root_dir: Path, run_id: str):
        self.root_dir = root_dir
        self.run_id = run_id
        self.run_folder = root_dir / ".agent" / "runs" / run_id
        self.run_folder.mkdir(parents=True, exist_ok=True)
        
        self.trace_path = self.run_folder / "trace.jsonl"
        self.tool_calls_path = self.run_folder / "tool_calls.json"
        self.handoffs_path = self.run_folder / "handoffs.json"
        self.approvals_path = self.run_folder / "approvals.json"
        
    def _append_to_file(self, path: Path, data: Any) -> None:
        """Helper to append structured records securely."""
        try:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _append_to_json_list(self, path: Path, entry: Any) -> None:
        """Helper to load a JSON array, append, and rewrite atomically."""
        data = []
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []
        data.append(entry)
        
        tmp = path.with_suffix(".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception:
            if tmp.is_file():
                try:
                    tmp.unlink()
                except Exception:
                    pass

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Append a trace event to trace.jsonl."""
        entry = {
            "timestamp": _dt.datetime.now().isoformat(),
            "event_type": event_type,
            "payload": payload
        }
        self._append_to_file(self.trace_path, entry)
        
    def log_tool_call(self, tool_name: str, args: Dict[str, Any], output: str) -> None:
        """Save tool executions to tool_calls.json."""
        entry = {
            "timestamp": _dt.datetime.now().isoformat(),
            "tool": tool_name,
            "arguments": args,
            "output_preview": str(output)[:1000]
        }
        self._append_to_json_list(self.tool_calls_path, entry)
        self.log_event("tool_call", entry)
        
    def log_handoff(self, from_agent: str, to_agent: str, message: str) -> None:
        """Save subagent coordinate handoffs to handoffs.json."""
        entry = {
            "timestamp": _dt.datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "message_preview": str(message)[:1000]
        }
        self._append_to_json_list(self.handoffs_path, entry)
        self.log_event("handoff", entry)
        
    def log_approval(self, message: str, response: str) -> None:
        """Save human approval gates responses to approvals.json."""
        entry = {
            "timestamp": _dt.datetime.now().isoformat(),
            "message": message,
            "response": response
        }
        self._append_to_json_list(self.approvals_path, entry)
        self.log_event("human_approval", entry)
        
    def save_final_diff(self, diff_content: str) -> None:
        """Write git-compatible diff patches of file updates."""
        try:
            (self.run_folder / "final_diff.patch").write_text(diff_content, encoding="utf-8")
        except Exception:
            pass
            
    def save_reviewer_report(self, report_content: str) -> None:
        """Save structured markdown reports of reviewer validations."""
        try:
            (self.run_folder / "reviewer_report.md").write_text(report_content, encoding="utf-8")
        except Exception:
            pass
