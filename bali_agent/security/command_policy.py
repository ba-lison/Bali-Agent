# -*- coding: utf-8 -*-
"""Command classification policy and validation.

Security model: allowlist by SUBCOMMAND, not just by executable.
Executables like `python`, `npm`, `pip`, `go`, `cargo` can execute
arbitrary code even with shell=False — they must be restricted at the
subcommand level.

Risk levels:
  R2 — Safe test/read-only command (auto-approved)
  R3 — Config/build command (logged, may require human gate)
  R4 — Dangerous / explicitly blocked (always denied)
"""

import shlex
import re
from typing import Tuple

# ---------------------------------------------------------------------------
# Explicitly blocked executables — never allowed under any circumstance.
# ---------------------------------------------------------------------------
BLOCKED_EXECUTABLES = {
    "rm", "del", "format", "curl", "wget",
    "sh", "bash", "zsh", "fish", "cmd", "powershell",
    "nc", "netcat", "ncat",
}

# ---------------------------------------------------------------------------
# Subcommand allowlists per executable.
# Format: {executable: {allowed_subcommand_set}}
# Empty set means the executable itself is blocked entirely.
# ---------------------------------------------------------------------------
SUBCOMMAND_ALLOWLIST: dict[str, set[str]] = {
    # Python — only module invocations, never -c (arbitrary code)
    "python": {"pytest", "mypy", "build", "coverage", "black", "ruff", "isort"},
    "python3": {"pytest", "mypy", "build", "coverage", "black", "ruff", "isort"},

    # npm — only lifecycle scripts, never exec/install (supply-chain risk)
    "npm": {"test", "run"},

    # pip — completely blocked (supply-chain risk)
    # (no entry → falls to R4)

    # cargo — test/check/build only, never run (arbitrary binary execution)
    "cargo": {"test", "check", "build"},

    # go — test/build/vet only, never run (arbitrary execution)
    "go": {"test", "build", "vet", "fmt"},

    # git — read-only subcommands only
    "git": {"status", "diff", "log", "show", "ls-files"},

    # Safe read-only shell builtins
    "echo": None,   # None = no subcommand check, always R2
    "ls":   None,
    "dir":  None,
    "cat":  None,
    "head": None,
    "tail": None,
    "pwd":  None,

    # Test runners (invoked directly, no subcommand needed)
    "pytest": None,
    "mypy":   None,
}

# Subcommands that are explicitly high-risk even for allowed executables.
# Even if the executable is in SUBCOMMAND_ALLOWLIST, these are always R4.
BLOCKED_SUBCOMMANDS: dict[str, set[str]] = {
    "python":  {"-c", "-m", "pip"},          # -m pip is pip install
    "python3": {"-c", "-m"},
    "npm":     {"exec", "install", "i", "ci", "publish", "link", "unlink"},
    "cargo":   {"run", "install", "publish"},
    "go":      {"run", "install", "get"},
    "git":     {"push", "commit", "rebase", "reset", "clean", "checkout"},
}

# Chaining operators that bypass shell=False protections when embedded in args
_CHAINING_OPS = {";", "&&", "||", "|", "&", "`", "$("}


def classify_command(command: str) -> Tuple[str, bool]:
    """Classify a command string into a risk class and return allow/deny.

    Args:
        command: Raw command string to evaluate.

    Returns:
        Tuple of (risk_class, is_allowed) where risk_class is one of
        R2, R3, R4 and is_allowed is True only if the command passes all checks.
    """
    try:
        tokens = shlex.split(command)
    except Exception:
        return "R4", False

    if not tokens:
        return "R0", False

    # Normalise executable name (strip path and .exe suffix on Windows)
    exec_raw = tokens[0]
    exec_name = re.split(r"[/\\]", exec_raw)[-1].lower().strip()
    if exec_name.endswith(".exe"):
        exec_name = exec_name[:-4]

    # --- Hard block: explicitly dangerous executables ---
    if exec_name in BLOCKED_EXECUTABLES:
        return "R4", False

    # --- Hard block: chaining operators in any token ---
    for tok in tokens:
        for op in _CHAINING_OPS:
            if op in tok:
                return "R4", False

    # --- Unknown executable → deny ---
    if exec_name not in SUBCOMMAND_ALLOWLIST:
        return "R4", False

    # --- Executables with no subcommand restriction (echo, ls, etc.) ---
    allowed_subs = SUBCOMMAND_ALLOWLIST[exec_name]
    if allowed_subs is None:
        return "R2", True

    # --- Subcommand check ---
    if len(tokens) < 2:
        # Executable called bare with no subcommand
        return "R4", False

    subcommand = tokens[1].lower().strip()

    # Check blocked subcommands first (takes priority)
    blocked_for_exec = BLOCKED_SUBCOMMANDS.get(exec_name, set())
    if subcommand in blocked_for_exec:
        return "R4", False

    # Check if subcommand is in allowlist
    if subcommand not in allowed_subs:
        return "R4", False

    # git read-only → R3, others → R2
    if exec_name == "git":
        return "R3", True

    # npm run / npm test with extra args → R3 (build scripts can be risky)
    if exec_name == "npm":
        return "R3", True

    return "R2", True
