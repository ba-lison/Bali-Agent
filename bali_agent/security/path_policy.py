# -*- coding: utf-8 -*-
"""Path permission policy and validation."""

import os
from pathlib import Path
from typing import Union, List

DENIED_GLOBAL_PATTERNS = {".env", ".git", "secrets"}

def is_path_allowed(agent_id: str, path: Union[str, Path], mode: str = "read", denied_paths: List[str] = None) -> bool:
    """Check if the given path is allowed for read/write by the subagent."""
    path_str = str(path).replace("\\", "/").lower()
    
    # Check global blocked patterns first
    for pattern in DENIED_GLOBAL_PATTERNS:
        if f"/{pattern}" in f"/{path_str}" or path_str.startswith(pattern):
            return False
            
    # Check agent-specific denied paths (from YAML config)
    if denied_paths:
        for denied in denied_paths:
            denied_clean = denied.replace("\\", "/").lower().strip("/")
            if denied_clean in path_str:
                return False
                
    return True
