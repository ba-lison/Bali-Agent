# -*- coding: utf-8 -*-
"""Path sandboxing and traversal prevention utilities.

Fix: replaced startswith() with os.path.commonpath() to prevent
sibling-directory prefix attacks (e.g. /tmp/proj vs /tmp/project-evil).
"""

import os
from pathlib import Path
from typing import Union


def _safe_path(requested: Union[str, Path], root: Union[str, Path]) -> str:
    """Resolve absolute path and prevent traversal outside the root directory.

    Uses os.path.commonpath() instead of startswith() to correctly reject
    sibling directories that share a path prefix with the root.

    Args:
        requested: The path requested by the agent (relative or absolute).
        root: The workspace root directory boundary.

    Returns:
        The resolved absolute path as a string.

    Raises:
        PermissionError: If the resolved path escapes the root boundary.
    """
    root_abs = os.path.realpath(str(root))
    requested_abs = os.path.realpath(os.path.join(root_abs, str(requested)))

    # commonpath correctly handles sibling-prefix attacks:
    #   root_abs    = /tmp/proj
    #   requested   = /tmp/project-evil/file.txt   → commonpath = /tmp ≠ root_abs → blocked
    try:
        common = os.path.commonpath([root_abs, requested_abs])
    except ValueError:
        # On Windows, different drives produce a ValueError
        raise PermissionError(f"Path traversal bloqueado (drives diferentes): {requested}")

    if common != root_abs:
        raise PermissionError(
            f"Path traversal bloqueado: '{requested}' está fora do workspace '{root_abs}'"
        )

    return requested_abs
