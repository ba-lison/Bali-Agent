# -*- coding: utf-8 -*-
"""Unit tests for the CLI commands."""

import pytest
import shutil
import tempfile
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
        assert (proj_path / ".agent" / "verify_setup.py").is_file()
        assert (proj_path / ".agent" / "run.py").is_file()
        assert (proj_path / ".agent" / ".gitignore").is_file()
        
        # Verify verifying setup works
        v_res = verify_command(proj_path)
        assert v_res == 0
    finally:
        shutil.rmtree(temp_dir)
