# -*- coding: utf-8 -*-
"""Security utilities for path sandboxing, command sanitization, and Agent Shield."""

import os
import shlex
import subprocess
import shutil
import re
from pathlib import Path
from typing import List, Union

def _safe_path(requested: Union[str, Path], root: Union[str, Path]) -> str:
    """Resolve an absolute path and prevent path traversal outside the root directory."""
    root_abs = os.path.realpath(str(root))
    requested_abs = os.path.realpath(os.path.join(root_abs, str(requested)))
    
    # Check if requested path starts with root path
    if not requested_abs.startswith(root_abs):
        raise PermissionError(f"Path traversal bloqueado: {requested}")
    return requested_abs

def _sanitize_llm_command(cmd_template: str) -> str:
    """Validate that BALI_LLM_COMMAND contains only expected placeholders and is safe."""
    if not cmd_template:
        raise ValueError("BALI_LLM_COMMAND nao pode ser vazio")
        
    if "{prompt_file}" not in cmd_template or "{output_file}" not in cmd_template:
        raise ValueError("BALI_LLM_COMMAND deve conter {prompt_file} e {output_file}")
        
    # Unsafe shell injection characters check
    unsafe_patterns = [r"\$\(", r"`", r";", r"&&", r"\|\|"]
    for pattern in unsafe_patterns:
        if re.search(pattern, cmd_template):
            raise ValueError(f"BALI_LLM_COMMAND contem metacaracteres inseguros: {cmd_template}")
            
    return cmd_template

def execute_safe_command(command: str, root_dir: Union[str, Path] = ".") -> str:
    """Tokenize and execute a command safely, handling executable resolution on Windows."""
    try:
        tokens = shlex.split(command)
    except Exception as e:
        return f"Erro ao fazer parse do comando: {e}"
        
    if not tokens:
        return "Erro: comando vazio."
        
    # Safe list of executables that do not require explicit verification
    safe_executables = {"pytest", "python", "npm", "pip", "cargo", "go", "git", "dir", "ls", "echo"}
    dangerous_cmds = {"rm", "del", "format", "curl", "wget", "sh", "bash", "powershell"}
    
    # Agent Shield - checks
    is_dangerous = False
    
    def check_dangerous_token(tok: str) -> bool:
        tk = tok.lower().strip()
        words = re.split(r'[/\\]', tk)
        base_cmd = words[-1]
        if base_cmd.endswith(".exe"):
            base_cmd = base_cmd[:-4]
        subwords = re.split(r'[-_.]', base_cmd)
        for sw in subwords:
            if sw in dangerous_cmds:
                return True
        return False

    for tok in tokens:
        if check_dangerous_token(tok):
            is_dangerous = True
            break
            
    chaining_ops = {";", "&&", "||", "|", "&"}
    has_chaining = False
    for tok in tokens:
        if any(op in tok for op in chaining_ops):
            has_chaining = True
            break
            
    subcommands = []
    current = []
    for tok in tokens:
        contains_op = any(op in tok for op in chaining_ops)
        if contains_op:
            parts = re.split(r'(&&|\|\||[;|&])', tok)
            for part in parts:
                if not part:
                    continue
                if part in chaining_ops:
                    if current:
                        subcommands.append(current)
                        current = []
                else:
                    current.append(part)
        else:
            if tok in chaining_ops:
                if current:
                    subcommands.append(current)
                    current = []
            else:
                current.append(tok)
    if current:
        subcommands.append(current)
        
    validation_passed = True
    if not subcommands:
        validation_passed = False
        
    for sub in subcommands:
        if not sub:
            validation_passed = False
            break
        exec_name = sub[0].lower().strip()
        if exec_name.endswith(".exe"):
            exec_name = exec_name[:-4]
        exec_name = re.split(r'[/\\]', exec_name)[-1]
        
        if exec_name not in safe_executables:
            validation_passed = False
            break
            
        if exec_name == "git":
            if len(sub) < 2 or sub[1].lower().strip() not in {"status", "diff", "log"}:
                validation_passed = False
                break
                
    is_safe = validation_passed and not is_dangerous
    
    if not is_safe:
        # Request human intervention/approval if not running in headless mode or tests
        print(f"\n[AGENT SHIELD - EXECUCAO SENSIVEL]\nO agente quer rodar: {command}\nVocê autoriza? (S/N)")
        try:
            response = input("> ").strip().lower()
            if response not in ["s", "sim", "y", "yes"]:
                return "Erro: Execução do comando rejeitada pelo usuário por motivos de segurança."
        except KeyboardInterrupt:
            return "Erro: Execução do comando cancelada pelo usuário."
            
    # Resolve Windows cmd/bat wrappers (e.g. npm -> npm.cmd) when shell=False
    if os.name == "nt" and tokens:
        resolved_exec = shutil.which(tokens[0])
        if resolved_exec:
            tokens[0] = resolved_exec
            
    try:
        # Run securely with shell=False, capturing output and enforcing timeout of 60 seconds
        res = subprocess.run(
            tokens,
            shell=False,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(root_dir)
        )
        return f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    except subprocess.TimeoutExpired:
        return "Erro: O comando expirou (limite de 60 segundos)."
    except Exception as e:
        return f"Erro ao rodar comando '{command}': {e}"
