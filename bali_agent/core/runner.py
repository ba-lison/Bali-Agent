# -*- coding: utf-8 -*-
"""Runner module orchestrating the execution loop of isolated agents.

Security fixes applied:
- can_spawn_agents is now enforced before any invoke_subagent call.
- Reviewer gate is fail-closed: missing or invalid JSON verdict raises ValueError.
"""

import os
import json
import time
import datetime as _dt
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional

from bali_agent.core.agent import Agent
from bali_agent.core.policy import ToolPolicy
from bali_agent.core.context import ContextPacker
from bali_agent.core.session import SessionManager
from bali_agent.core.handoff import HandoffBus
from bali_agent.core.event_log import EventLogger
from bali_agent.core.tool_registry import get_allowed_schemas
from bali_agent.core.llm_client import call_llm_api

# Import tools
from bali_agent.tools.filesystem import read_file_tool, write_file_tool
from bali_agent.tools.shell import run_command_tool
from bali_agent.tools.git import git_tool
from bali_agent.tools.approval import request_human_approval_tool
from bali_agent.templates.core.skills import create_or_update_skill

class Runner:
    def __init__(self, root_dir: Path, run_id: Optional[str] = None):
        self.root_dir = root_dir.resolve()
        self.run_id = run_id or _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.policy = ToolPolicy(self.root_dir)
        self.context_packer = ContextPacker(self.root_dir)
        self.session_manager = SessionManager(self.root_dir)
        self.handoff_bus = HandoffBus(self.root_dir)
        self.logger = EventLogger(self.root_dir, self.run_id)

    def execute_tool(self, name: str, args: Dict[str, Any], agent: Agent) -> str:
        """Verify policy constraints and execute the given tool."""
        # Check permissions first
        if agent.allowed_tools and name not in agent.allowed_tools:
            return f"Erro: A ferramenta '{name}' nao esta autorizada para o agente '{agent.id}'."
            
        self.logger.log_event("tool_authorization_request", {"tool": name, "agent": agent.id})
        
        # Risk / Approval checks
        detail = ""
        if name == "write_file":
            detail = args.get("path", "")
        elif name == "run_command":
            detail = args.get("command", "")
            
        if self.policy.requires_approval(agent.id, name, detail):
            msg = f"Acao sensivel detectada ({name}: {detail}). Confirmar execucao? (S/N)"
            ans = request_human_approval_tool(msg)
            self.logger.log_approval(msg, ans)
            if "Aprovado" not in ans:
                return "Erro: Acao sensivel rejeitada pelo operador."

        # Executions
        output = ""
        if name == "read_file":
            output = read_file_tool(args.get("path", ""), self.policy, agent.id, agent.denied_paths)
            # Redact secrets
            output = self.policy.redact(agent.id, output)
        elif name == "write_file":
            output = write_file_tool(args.get("path", ""), args.get("content", ""), self.policy, agent.id, agent.denied_paths)
        elif name == "run_command":
            output = run_command_tool(args.get("command", ""), self.policy, agent.id)
        elif name == "git":
            output = git_tool(args.get("action", ""), self.policy, agent.id, args.get("args", []))
        elif name == "request_human_approval":
            output = request_human_approval_tool(args.get("message", ""))
            self.logger.log_approval(args.get("message", ""), output)
        elif name == "search_memory":
            from bali_agent.core.memory import search_memory
            output = search_memory(self.root_dir, args.get("query", ""))
        elif name == "send_handoff":
            output = self.handoff_bus.send(agent.id, args.get("to_agent", ""), args.get("message", ""))
            self.logger.log_handoff(agent.id, args.get("to_agent", ""), args.get("message", ""))
        elif name == "create_skill":
            try:
                output = create_or_update_skill(
                    self.root_dir,
                    args.get("skill_id", ""),
                    args.get("title", ""),
                    args.get("body", ""),
                    args.get("reason", ""),
                    agent.id,
                )
            except ValueError as exc:
                output = f"Erro: {exc}"
        elif name == "invoke_subagent":
            # Security: enforce can_spawn_agents flag from agent manifest
            if not agent.can_spawn_agents:
                return (
                    f"Erro: O agente '{agent.id}' nao esta autorizado a invocar subagentes "
                    "(can_spawn_agents: false no manifesto)."
                )

            sub_name = args.get("agent_name", "")
            sub_prompt = args.get("prompt", "")

            current_depth = int(os.environ.get("BALI_SUBAGENT_DEPTH", "0"))
            if current_depth >= 2:
                return "Erro: Profundidade maxima de subagentes excedida (2)."

            os.environ["BALI_SUBAGENT_DEPTH"] = str(current_depth + 1)
            try:
                # Recursive execution in isolated context
                output = self.run_agent(sub_name, sub_prompt)
            finally:
                os.environ["BALI_SUBAGENT_DEPTH"] = str(current_depth)
        else:
            output = f"Erro: Ferramenta '{name}' nao registrada."
            
        self.logger.log_tool_call(name, args, output)
        return output

    def run_agent(self, agent_id: str, prompt: str) -> str:
        """Run an agent session loop securely."""
        # 1. Load agent specs
        agent_path = self.root_dir / ".agent" / "team" / f"{agent_id}.md"
        if not agent_path.is_file():
            agent_path = self.root_dir / ".agent" / "team" / f"spec-{agent_id}.md"
            
        if not agent_path.is_file():
            # Try to build default specialist config
            config = {"role": f"spec-{agent_id}", "max_iterations": 5, "max_tokens": 12000}
            agent = Agent(agent_id, f"Voce e o subagente especialista {agent_id}.", config)
        else:
            agent = Agent.load_from_file(agent_path)
            
        system_prompt = f"{agent.prompt}\n\nVoce e o especialista '{agent.id}'."
        
        # 2. Load or initialize session
        session_id = f"{self.run_id}-{agent.id}"
        messages = self.session_manager.load_session(session_id)
        if not messages:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            self.session_manager.save_session(session_id, messages)

        loop_count = 0
        max_loops = agent.max_iterations
        
        self.logger.log_event("agent_start", {"agent": agent.id, "prompt": prompt})

        while loop_count < max_loops:
            loop_count += 1
            
            # Pack context (Sliding window and manifests)
            packed_messages, manifest = self.context_packer.pack_context(
                agent.id, messages, agent.max_tokens, self.run_id
            )
            
            schemas = get_allowed_schemas(agent.allowed_tools)
            
            response = call_llm_api(packed_messages, tools=schemas)
            if not response:
                return "Erro: Falha na chamada de API do LLM."
                
            content_text = ""
            tool_calls = []
            
            # Handle OpenAI-compatible response format
            if "choices" in response:
                choice = response["choices"][0]
                message = choice["message"]
                content_text = message.get("content") or ""
                tool_calls = message.get("tool_calls") or []
                messages.append(message)
                self.session_manager.save_session(session_id, messages)
                
            # Handle Anthropic-compatible format
            elif "content" in response:
                content_blocks = response["content"]
                tool_requests = []
                for block in content_blocks:
                    if block["type"] == "text":
                        content_text += block["text"]
                    elif block["type"] == "tool_use":
                        tool_requests.append(block)
                messages.append({"role": "assistant", "content": content_blocks})
                self.session_manager.save_session(session_id, messages)
                
                # Transform to standard structure
                for tr in tool_requests:
                    tool_calls.append({
                        "id": tr["id"],
                        "function": {"name": tr["name"], "arguments": json.dumps(tr["input"])}
                    })

            self.logger.log_event("agent_response", {"agent": agent.id, "content": content_text, "tool_calls": tool_calls})

            # 3. Reviewer gate — FAIL-CLOSED
            # If this is the reviewer agent, a valid JSON verdict is MANDATORY.
            # Any deviation (missing JSON, invalid schema, no 'approved' key) is
            # treated as a hard failure to prevent silent pass-throughs.
            if agent.id == "reviewer" and content_text:
                # Always persist the raw report for audit
                self.logger.save_reviewer_report(content_text)

                # Extract the outermost JSON object from the response.
                # A simple {.*?} regex fails on nested objects — use brace counting.
                json_start = content_text.find("{")
                if json_start == -1:
                    raise ValueError(
                        "Reviewer gate falhou: nenhum bloco JSON encontrado na resposta. "
                        "O Reviewer DEVE retornar um objeto JSON com 'approved: true/false'."
                    )

                depth = 0
                json_end = -1
                for i, ch in enumerate(content_text[json_start:], start=json_start):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            json_end = i + 1
                            break

                if json_end == -1:
                    raise ValueError(
                        "Reviewer gate falhou: nenhum bloco JSON encontrado na resposta. "
                        "O Reviewer DEVE retornar um objeto JSON com 'approved: true/false'."
                    )

                json_str = content_text[json_start:json_end]
                try:
                    verdict = json.loads(json_str)
                except json.JSONDecodeError as jde:
                    raise ValueError(
                        f"Reviewer gate falhou: JSON invalido — {jde}. "
                        "O Reviewer DEVE retornar JSON valido com 'approved: true/false'."
                    ) from jde

                # Schema validation: 'approved' key is mandatory
                if "approved" not in verdict:
                    raise ValueError(
                        "Reviewer gate falhou: campo 'approved' ausente no JSON do Reviewer. "
                        f"Campos encontrados: {list(verdict.keys())}"
                    )

                if not isinstance(verdict["approved"], bool):
                    raise ValueError(
                        f"Reviewer gate falhou: 'approved' deve ser boolean, "
                        f"recebido: {type(verdict['approved']).__name__}"
                    )

                if not verdict["approved"]:
                    blockers = verdict.get("blockers", [])
                    blockers_desc = ", ".join(
                        b.get("reason", str(b)) for b in blockers
                    ) if blockers else "(sem detalhes)"
                    raise ValueError(
                        f"Tarefa reprovada pelo Reviewer. Motivos: {blockers_desc}"
                    )

            if content_text and not tool_calls:
                self.logger.log_event("agent_stop", {"agent": agent.id, "content": content_text})
                return content_text
                
            if tool_calls:
                for tc in tool_calls:
                    func = tc["function"]
                    t_name = func["name"]
                    try:
                        t_args = json.loads(func["arguments"])
                    except Exception:
                        t_args = {}
                        
                    output = self.execute_tool(t_name, t_args, agent)
                    
                    # Append result to session
                    if "choices" in response:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": t_name,
                            "content": output
                        })
                    else:
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tc["id"],
                                    "content": output
                                }
                            ]
                        })
                    self.session_manager.save_session(session_id, messages)
                    
        return f"Erro: Limite de loop do subagente '{agent.id}' excedido."

def run_agent_loop(agent_id: str, prompt: str, root_dir: Path, max_loops: int = 5) -> str:
    """Helper method providing run compatibility with other components."""
    runner = Runner(root_dir)
    return runner.run_agent(agent_id, prompt)
