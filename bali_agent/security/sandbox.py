# -*- coding: utf-8 -*-
"""Path sandboxing and traversal prevention utilities."""

import os
from pathlib import Path
from typing import Union

def _safe_path(requested: Union[str, Path], root: Union[str, Path]) -> str:
    """Resolve absolute path and prevent traversal outside the root directory."""
    root_abs = os.path.realpath(str(root))
    requested_abs = os.path.realpath(os.path.join(root_abs, str(requested)))
    
    if not requested_abs.startswith(root_abs):
        raise PermissionError(f"Path traversal bloqueado: {requested}")
    return requested_abs
