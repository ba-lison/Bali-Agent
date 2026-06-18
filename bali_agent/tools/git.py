# -*- coding: utf-8 -*-
"""Git tool execution wrapper."""

import subprocess
from pathlib import Path
from bali_agent.core.policy import ToolPolicy

def git_tool(action: str, policy: ToolPolicy, agent_id: str, args: list = None) -> str:
    """Execute simple git actions (status, diff, log) safely."""
    cmd = f"git {action}"
    if args:
        cmd += " " + " ".join(args)
        
    allowed, cmd_or_err = policy.can_execute(agent_id, cmd)
    if not allowed:
        return cmd_or_err
        
    tokens = ["git", action]
    if args:
        tokens.extend(args)
        
    try:
        res = subprocess.run(
            tokens,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(policy.root_dir)
        )
        return res.stdout
    except Exception as e:
        return f"Erro ao executar git: {e}"
