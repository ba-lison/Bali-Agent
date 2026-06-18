# -*- coding: utf-8 -*-
"""Path permission policy and validation.

Fix: replaced substring matching with os.path.realpath() normalisation
to prevent path traversal via symlinks or relative components.
"""

import os
from pathlib import Path
from typing import Union, List

# Patterns always denied regardless of agent config.
# These are matched against the normalised realpath.
DENIED_GLOBAL_PATTERNS = {".env", ".git", "secrets"}


def is_path_allowed(
    agent_id: str,
    path: Union[str, Path],
    mode: str = "read",
    denied_paths: List[str] | None = None,
    root: Union[str, Path, None] = None,
) -> bool:
    """Check if the given path is allowed for read/write by the subagent.

    Args:
        agent_id:     The agent requesting access (for future per-agent audit).
        path:         The path being accessed (may be relative or absolute).
        mode:         ``"read"`` or ``"write"`` (reserved for future granularity).
        denied_paths: Agent-specific denied path patterns from YAML config.
        root:         Optional workspace root used for resolving relative paths.

    Returns:
        True if access is allowed, False otherwise.
    """
    # Resolve to an absolute, normalised path to defeat symlinks / `..` tricks.
    if root is not None:
        resolved = os.path.realpath(os.path.join(str(root), str(path)))
    else:
        resolved = os.path.realpath(str(path))

    resolved_lower = resolved.replace("\\", "/").lower()

    # Check global blocked patterns against each component of the path.
    parts = resolved_lower.replace("\\", "/").split("/")
    for part in parts:
        for pattern in DENIED_GLOBAL_PATTERNS:
            # Match exact path component, not a substring
            if part == pattern or part.startswith(pattern + ".") or part.startswith("." + pattern):
                return False

    # Also check for .env variants in filename
    filename = parts[-1] if parts else ""
    if filename.startswith(".env"):
        return False

    # Check agent-specific denied paths (from YAML config)
    if denied_paths:
        for denied in denied_paths:
            denied_resolved = os.path.realpath(str(denied)) if os.path.isabs(denied) else denied
            denied_lower = denied_resolved.replace("\\", "/").lower().strip("/")
            # Use substring match on resolved path, but only after normalisation
            if denied_lower and denied_lower in resolved_lower:
                return False

    return True
