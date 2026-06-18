# -*- coding: utf-8 -*-
"""Filesystem tool execution wrapper with safety constraints."""

import os
from pathlib import Path
from typing import Dict, Any, Tuple

from bali_agent.core.policy import ToolPolicy

def read_file_tool(path: str, policy: ToolPolicy, agent_id: str, denied_paths: list) -> str:
    """Read file content safely under workspace rules."""
    allowed, safe_p_or_err = policy.can_read(agent_id, path, denied_paths)
    if not allowed:
        return safe_p_or_err
    try:
        with open(safe_p_or_err, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler arquivo {path}: {e}"

def write_file_tool(path: str, content: str, policy: ToolPolicy, agent_id: str, denied_paths: list) -> str:
    """Write file content safely under workspace rules and secret scanning."""
    allowed, safe_p_or_err = policy.can_write(agent_id, path, content, denied_paths)
    if not allowed:
        return safe_p_or_err
    try:
        os.makedirs(os.path.dirname(safe_p_or_err), exist_ok=True)
        with open(safe_p_or_err, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Arquivo '{path}' gravado com sucesso."
    except Exception as e:
        return f"Erro ao gravar arquivo {path}: {e}"
