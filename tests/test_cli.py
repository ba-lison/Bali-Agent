# -*- coding: utf-8 -*-
"""Unit tests for the CLI commands."""

import pytest
import shutil
import tempfile
import sys
from pathlib import Path
from bali_agent.cli import init_command, verify_command

def test_cli_init_command():
    temp_dir = tempfile.mkdtemp()
    proj_path = Path(temp_dir)
    
    try:
        # Run init command
        res = init_command(proj_path)
        assert res == 0
        
        # Verify folders exist
        assert (proj_path / ".agent").is_dir()
        assert (proj_path / ".agent" / "subagent.config.yaml").is_file()
        assert (proj_path / ".agent" / "team" / "orchestrator.md").is_file()
        assert (proj_path / ".agent" / "runtime" / "bali_runtime.py").is_file()
        assert (proj_path / ".agent" / "verify_setup.py").is_file()
        assert (proj_path / ".agent" / "run.py").is_file()
        assert (proj_path / ".agent" / ".gitignore").is_file()

        run_text = (proj_path / ".agent" / "run.py").read_text(encoding="utf-8")
        assert ".agent/runtime/bali_runtime.py" in run_text

        manifest_text = (proj_path / ".agent" / "subagent.config.yaml").read_text(encoding="utf-8")
        assert 'runtime_authority: "bali-runtime"' in manifest_text
        assert "skills_policy:" in manifest_text
        assert 'store: ".agent/skills"' in manifest_text
        assert 'audit_log: ".agent/skills/AUDIT.md"' in manifest_text
        assert (proj_path / ".agent" / "skills" / "AUDIT.md").is_file()
        
        # Verify verifying setup works
        v_res = verify_command(proj_path)
        assert v_res == 0
    finally:
        shutil.rmtree(temp_dir)

def test_cli_run_delegates_to_installed_runtime(temp_project_dir, monkeypatch):
    import bali_agent.cli as cli

    runtime = temp_project_dir / ".agent" / "runtime" / "bali_runtime.py"
    runtime.write_text("# runtime", encoding="utf-8")
    calls = []

    class Completed:
        returncode = 0

    class BombRunner:
        def __init__(self, root):
            self.root = root

        def run_agent(self, agent_id, prompt):
            raise AssertionError("bali run should delegate to installed Bali Runtime")

    def fake_run(command, *args, **kwargs):
        calls.append(command)
        return Completed()

    monkeypatch.setattr(cli, "Runner", BombRunner)
    monkeypatch.setattr(cli, "subprocess", type("Subprocess", (), {"run": fake_run}), raising=False)

    res = cli.run_command(temp_project_dir, "Corrigir logins", workflow="operate", specialist="spec-implementer")

    assert res == 0
    assert calls
    assert calls[0] == [
        sys.executable,
        str(runtime),
        "run",
        "--workflow",
        "operate",
        "--specialist",
        "spec-implementer",
        "Corrigir logins",
    ]
