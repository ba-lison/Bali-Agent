# -*- coding: utf-8 -*-
"""Shell tool execution wrapper with strict safety checks and tokenization."""

import os
import shlex
import subprocess
import shutil
from pathlib import Path

from bali_agent.core.policy import ToolPolicy

def run_command_tool(command: str, policy: ToolPolicy, agent_id: str) -> str:
    """Execute command safely under risk policy guidelines."""
    allowed, cmd_or_err = policy.can_execute(agent_id, command)
    if not allowed:
        return cmd_or_err
        
    try:
        tokens = shlex.split(command)
    except Exception as e:
        return f"Erro ao fazer parse do comando: {e}"
        
    # Windows executable resolution (.cmd/bat wrappers)
    if os.name == "nt" and tokens:
        resolved = shutil.which(tokens[0])
        if resolved:
            tokens[0] = resolved
            
    try:
        res = subprocess.run(
            tokens,
            shell=False,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(policy.root_dir)
        )
        return f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    except subprocess.TimeoutExpired:
        return "Erro: O comando expirou (limite de 60 segundos)."
    except Exception as e:
        return f"Erro ao rodar comando '{command}': {e}"
