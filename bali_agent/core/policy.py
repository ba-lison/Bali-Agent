# -*- coding: utf-8 -*-
"""ToolPolicy engine orchestrating all tool authorizations, risk levels, and redactions."""

import os
from pathlib import Path
from typing import List, Optional, Union, Tuple

from bali_agent.security.sandbox import _safe_path
from bali_agent.security.path_policy import is_path_allowed
from bali_agent.security.command_policy import classify_command
from bali_agent.security.secret_scanner import scan_content_for_secrets

class ToolPolicy:
    def __init__(self, root_dir: Union[str, Path]):
        self.root_dir = Path(root_dir).resolve()
        
    def can_read(self, agent_id: str, path: Union[str, Path], denied_paths: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Check if reading the file is permitted."""
        try:
            safe_p = _safe_path(path, self.root_dir)
            rel_p = os.path.relpath(safe_p, self.root_dir)
            if not is_path_allowed(agent_id, rel_p, mode="read", denied_paths=denied_paths):
                return False, f"Acesso negado: leitura do caminho '{path}' nao permitida por politica."
            return True, safe_p
        except PermissionError:
            return False, f"Acesso negado: tentativa de path traversal fora do workspace."
            
    def can_write(self, agent_id: str, path: Union[str, Path], content: str, denied_paths: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Check if writing/updating the file is permitted and safe."""
        try:
            safe_p = _safe_path(path, self.root_dir)
            rel_p = os.path.relpath(safe_p, self.root_dir)
            if not is_path_allowed(agent_id, rel_p, mode="write", denied_paths=denied_paths):
                return False, f"Acesso negado: escrita no caminho '{path}' nao permitida por politica."
                
            # Scan content for secret leak attempts
            secret_hit = scan_content_for_secrets(content)
            if secret_hit:
                return False, f"Acesso negado: gravacao abortada devido a presenca de dados sensiveis ({secret_hit})."
                
            return True, safe_p
        except PermissionError:
            return False, f"Acesso negado: tentativa de path traversal fora do workspace."
            
    def can_execute(self, agent_id: str, command: str) -> Tuple[bool, str]:
        """Validate the command against risk classes."""
        risk_class, allowed = classify_command(command)
        if not allowed:
            return False, f"Acesso negado: comando '{command}' possui classe de risco inadequada ({risk_class})."
        return True, command

    def requires_approval(self, agent_id: str, action: str, detail: str) -> bool:
        """Determine if an action requires explicit human confirmation."""
        # Risk class 3 or 4, or critical files modifications require human approval
        if action == "run_command":
            _, allowed = classify_command(detail)
            return not allowed  # requires approval if not automatically allowed
        elif action in {"write_file", "delete_file"}:
            # Check if writing to sensitive files
            p_lower = detail.lower()
            critical_keywords = ["config", "package.json", "manifest", "setup", "requirements.txt", "pyproject.toml"]
            if any(k in p_lower for k in critical_keywords):
                return True
        return False
        
    def redact(self, agent_id: str, content: str) -> str:
        """Redact sensitive fields from content blocks returned to the LLM."""
        if not content:
            return ""
        # Redact common key prefixes
        from bali_agent.security.secret_scanner import SECRET_PATTERNS
        redacted = content
        for name, pattern in SECRET_PATTERNS.items():
            redacted = pattern.sub(f"[REDACTED {name.upper()}]", redacted)
        return redacted
