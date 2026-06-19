# -*- coding: utf-8 -*-
"""Tools execution module with path traversal sandboxing and Agent Shield validation."""

import os
from pathlib import Path
from typing import Dict, Any, Union

from templates.core.security import _safe_path, execute_safe_command
from templates.core.memory import search_memory
from templates.core.handoff_bus import _handoff_bus_send, _handoff_bus_receive
from templates.core.skills import create_or_update_skill

def execute_tool(name: str, args: Dict[str, Any], root_dir: Path, current_agent: str = "orchestrator") -> str:
    """Execute the given tool with arguments and security validations."""
    root_abs = root_dir.resolve()
    
    if name == "read_file":
        path_arg = args.get("path")
        if not path_arg:
            return "Erro: parâmetro 'path' ausente."
        try:
            safe_p = _safe_path(path_arg, root_abs)
            with open(safe_p, "r", encoding="utf-8") as f:
                return f.read()
        except PermissionError as pe:
            return f"Erro de permissao: {pe}"
        except Exception as e:
            return f"Erro ao ler arquivo {path_arg}: {e}"

    elif name == "write_file":
        path_arg = args.get("path")
        content = args.get("content")
        if not path_arg or content is None:
            return "Erro: parâmetros 'path' ou 'content' ausentes."
        try:
            safe_p = _safe_path(path_arg, root_abs)
            os.makedirs(os.path.dirname(safe_p), exist_ok=True)
            with open(safe_p, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Arquivo '{path_arg}' gravado com sucesso."
        except PermissionError as pe:
            return f"Erro de permissao: {pe}"
        except Exception as e:
            return f"Erro ao gravar arquivo {path_arg}: {e}"

    elif name == "run_command":
        command = args.get("command", "")
        if not command:
            return "Erro: parâmetro 'command' ausente."
        # Safe command execution (Agent Shield and subprocess running)
        return execute_safe_command(command, root_abs)

    elif name == "request_human_approval":
        message = args.get("message")
        print(f"\n[GATE DE APROVAÇÃO HUMANA]\n{message}")
        try:
            response = input("\nSua resposta/aprovação (pressione Enter para confirmar padrão):\n> ")
            return f"Aprovação do Usuário: {response if response.strip() else 'Aprovado sem observações'}"
        except KeyboardInterrupt:
            return "Erro: Operação interrompida pelo usuário."

    elif name == "invoke_subagent":
        # Handled at loop/orchestrator level via callback or dynamic imports
        # To avoid circular dependency, we return a structural placeholder or call runner
        agent_name = args.get("agent_name")
        prompt = args.get("prompt")
        if not agent_name or not prompt:
            return "Erro: parâmetros 'agent_name' ou 'prompt' ausentes."
            
        current_depth = int(os.environ.get("BALI_SUBAGENT_DEPTH", "0"))
        if current_depth >= 2:
            return "Erro: Limite de profundidade de subagentes atingido (máximo 2 níveis de recursão)."
            
        # We import dynamically to run the agent loop
        from templates.core.agent_loop import run_agent_loop
        
        print(f"[*] Subagente '{agent_name}' invocado (depth={current_depth + 1}).")
        os.environ["BALI_SUBAGENT_DEPTH"] = str(current_depth + 1)
        try:
            return run_agent_loop(agent_name, prompt, root_dir=root_dir)
        finally:
            os.environ["BALI_SUBAGENT_DEPTH"] = str(current_depth)

    elif name == "search_memory":
        query = args.get("query", "")
        if not query:
            return "Erro: parâmetro 'query' ausente."
        return search_memory(root_abs, query)

    elif name == "send_handoff":
        to_agent = args.get("to_agent")
        message = args.get("message")
        if not to_agent or not message:
            return "Erro: parâmetros 'to_agent' ou 'message' ausentes."
            
        bus_path = root_abs / ".agent" / "output" / "handoff_bus.json"
        return _handoff_bus_send(bus_path, current_agent, to_agent, message)

    elif name == "create_skill":
        try:
            return create_or_update_skill(
                root_abs,
                args.get("skill_id", ""),
                args.get("title", ""),
                args.get("body", ""),
                args.get("reason", ""),
                current_agent,
            )
        except ValueError as exc:
            return f"Erro: {exc}"

    return f"Erro: Ferramenta '{name}' desconhecida."
