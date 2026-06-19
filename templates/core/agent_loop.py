# -*- coding: utf-8 -*-
"""Subagent Loop execution engine with state checkpointing."""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

from templates.core.agent_manager import load_agent_prompt
from templates.core.llm_client import call_llm_api
from templates.core.tools import execute_tool

# Expose TOOLS schema so the LLM is aware of available actions
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "invoke_subagent",
            "description": "Executa uma tarefa isolada usando um subagente especialista (ex: planner, reviewer, spec-frontend). O subagente roda em um contexto limpo com seu próprio prompt de identidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Nome do agente ou especialista a invocar (ex: 'planner', 'reviewer', 'frontend', 'backend', 'database')."
                    },
                    "prompt": {
                        "type": "string",
                        "description": "A instrução específica e atômica para o subagente executar."
                    }
                },
                "required": ["agent_name", "prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lê o conteúdo de um arquivo do repositório.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho relativo do arquivo no projeto."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Grava ou atualiza um arquivo no repositório.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Caminho relativo do arquivo no projeto."
                    },
                    "content": {
                        "type": "string",
                        "description": "Conteúdo textual completo a ser gravado no arquivo."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executa um comando de terminal no host local (ex: npm test, pytest) para validação.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "O comando de terminal a ser executado."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_approval",
            "description": "Pausa a execução para pedir aprovação, feedback ou resposta do usuário em um Gate de aprovação humana.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "A mensagem ou pergunta a ser exibida para o usuário."
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Busca entradas relevantes na memória histórica (memory.md) usando palavras-chave, retornando apenas os blocos correspondentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Palavra-chave ou termo de busca para localizar na memória histórica."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_skill",
            "description": "Cria ou atualiza uma skill local do projeto em .agent/skills/ com trilha de auditoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_id": {
                        "type": "string",
                        "description": "Identificador da skill em minusculas, numeros e hifens."
                    },
                    "title": {
                        "type": "string",
                        "description": "Titulo humano da skill."
                    },
                    "body": {
                        "type": "string",
                        "description": "Instrucoes completas da skill."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Motivo auditavel para criar ou atualizar a skill."
                    }
                },
                "required": ["skill_id", "title", "body", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_handoff",
            "description": "Envia uma mensagem estruturada para outro subagente via HandoffBus. Use quando precisar coordenar ou transferir contexto entre subagentes sem precisar de uma nova invocação completa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_agent": {
                        "type": "string",
                        "description": "Nome do agente destinatário (ex: 'reviewer', 'planner', 'spec-frontend')."
                    },
                    "message": {
                        "type": "string",
                        "description": "Conteúdo da mensagem ou contexto a transferir."
                    }
                },
                "required": ["to_agent", "message"]
            }
        }
    }
]

def run_agent_loop(agent_name: str, prompt: str, root_dir: Path, max_loops: int = 5) -> str:
    """Execute the subagent lifecycle in a controlled loop, validating tool results and saving progress."""
    root_abs = root_dir.resolve()
    try:
        agent_prompt = load_agent_prompt(root_abs, agent_name)
    except FileNotFoundError:
        agent_prompt = f"Você é o subagente especialista '{agent_name}'. Execute a tarefa com qualidade máxima."
        
    system_prompt = f"{agent_prompt}\n\nVocê é o especialista '{agent_name}'. Execute a tarefa usando as ferramentas disponíveis."
    
    session_id = os.environ.get("BALI_SESSION_ID", agent_name)
    sessions_dir = root_abs / ".agent" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = sessions_dir / f"{session_id}.json"
    
    def save_checkpoint(msgs: List[Dict[str, Any]]) -> None:
        try:
            tmp_path = checkpoint_path.with_suffix(".json.tmp")
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(msgs, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, checkpoint_path)
        except Exception as e:
            print(f"[!] Erro ao salvar checkpoint: {e}", file=sys.stderr)

    class CheckpointList(list):
        def append(self, item):
            super().append(item)
            save_checkpoint(self)
        def extend(self, iterable):
            super().extend(iterable)
            save_checkpoint(self)

    if checkpoint_path.is_file():
        try:
            with checkpoint_path.open("r", encoding="utf-8") as f:
                messages = CheckpointList(json.load(f))
        except Exception as e:
            print(f"[!] Erro ao carregar checkpoint: {e}", file=sys.stderr)
            messages = CheckpointList([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ])
            save_checkpoint(messages)
    else:
        messages = CheckpointList([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ])
        save_checkpoint(messages)
        
    loop_count = 0
    while loop_count < max_loops:
        loop_count += 1
        print(f"[*] Subagente '{agent_name}' - Iteracao {loop_count}...", file=sys.stderr)
        
        response = call_llm_api(messages, tools=TOOLS)
        if not response:
            return "Erro: Falha na chamada de API do subagente."
            
        if "choices" in response:
            choice = response["choices"][0]
            message = choice["message"]
            content = message.get("content")
            tool_calls = message.get("tool_calls")
            
            messages.append(message)
            
            if content and not tool_calls:
                return content
                
            if tool_calls:
                for tool_call in tool_calls:
                    function_info = tool_call["function"]
                    tool_name = function_info["name"]
                    
                    try:
                        tool_args = json.loads(function_info["arguments"])
                    except Exception:
                        tool_args = {}
                        
                    tool_output = execute_tool(tool_name, tool_args, root_abs, current_agent=agent_name)
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": str(tool_output)
                    })
                    
        elif "content" in response:
            content_blocks = response["content"]
            text_content = ""
            tool_requests = []
            
            for block in content_blocks:
                if block["type"] == "text":
                    text_content += block["text"]
                elif block["type"] == "tool_use":
                    tool_requests.append(block)
                    
            messages.append({
                "role": "assistant",
                "content": content_blocks
            })
            
            if text_content and not tool_requests:
                return text_content
                
            if tool_requests:
                tool_results = []
                for tool_req in tool_requests:
                    tool_name = tool_req["name"]
                    tool_args = tool_req["input"]
                    tool_call_id = tool_req["id"]
                    
                    tool_output = execute_tool(tool_name, tool_args, root_abs, current_agent=agent_name)
                        
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": str(tool_output)
                    })
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
    return f"Erro: Limite de loops do subagente '{agent_name}' atingido."
