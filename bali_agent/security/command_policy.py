# -*- coding: utf-8 -*-
"""Command classification policy and validation."""

import shlex
import re
from typing import Tuple

SAFE_EXECUTABLES = {"pytest", "python", "npm", "pip", "cargo", "go", "git", "dir", "ls", "echo"}
DANGEROUS_CMDS = {"rm", "del", "format", "curl", "wget", "sh", "bash", "powershell"}

def classify_command(command: str) -> Tuple[str, bool]:
    """Classify command risk level and return (risk_class, is_allowed).
    
    Risk Levels:
    - R2: Safe test/build command.
    - R3: Config, package installs, git simple operations.
    - R4: Destructive or network-oriented commands.
    """
    try:
        tokens = shlex.split(command)
    except Exception:
        return "R4", False
        
    if not tokens:
        return "R0", False
        
    exec_name = tokens[0].lower().strip()
    if exec_name.endswith(".exe"):
        exec_name = exec_name[:-4]
    exec_name = re.split(r'[/\\]', exec_name)[-1]
    
    # Check if executable is dangerous
    if exec_name in DANGEROUS_CMDS:
        return "R4", False
        
    # Check tokens for other dangerous words or redirect chainings
    for tok in tokens[1:]:
        t_clean = tok.lower().strip()
        if any(d in t_clean for d in DANGEROUS_CMDS):
            return "R4", False
            
    # Check chaining operators
    chaining_ops = {";", "&&", "||", "|", "&"}
    if any(any(op in tok for op in chaining_ops) for tok in tokens):
        return "R4", False
        
    if exec_name in SAFE_EXECUTABLES:
        if exec_name == "git":
            if len(tokens) >= 2 and tokens[1].lower().strip() in {"status", "diff", "log"}:
                return "R3", True
            return "R4", False
        return "R2", True
        
    return "R4", False
