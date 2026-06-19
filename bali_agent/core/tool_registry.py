# -*- coding: utf-8 -*-
"""Tool Registry managing functional definitions and parameters for LLM tooling.

Security fix: get_allowed_schemas() now defaults to DENY-ALL when
allowed_tools is empty. Agents that need every tool must explicitly
declare allowed_tools: ["*"] in their YAML frontmatter.
"""

from typing import List, Dict, Any

TOOLS_SCHEMA: List[Dict[str, Any]] = [
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
            "description": "Executa um comando de terminal no host local para validação.",
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
            "name": "invoke_subagent",
            "description": "Executa uma tarefa isolada usando um subagente especialista. O subagente roda em um contexto limpo com seu próprio prompt de identidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Nome do agente ou especialista a invocar."
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
            "description": "Envia uma mensagem estruturada para outro subagente via HandoffBus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_agent": {
                        "type": "string",
                        "description": "Nome do agente destinatário."
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

# Index for fast name lookup
_SCHEMA_BY_NAME: Dict[str, Dict[str, Any]] = {
    t["function"]["name"]: t for t in TOOLS_SCHEMA
}

# Sentinel value: agent YAML frontmatter must declare allowed_tools: ["*"]
# to receive all tools. An empty list means ZERO tools (default-deny).
_WILDCARD = "*"


def get_allowed_schemas(allowed_tools: List[str]) -> List[Dict[str, Any]]:
    """Return tool schemas filtered by agent permissions.

    Security contract (default-deny):
      - ``[]``    → empty list  (agent declared no tools — gets nothing)
      - ``["*"]`` → all tools   (agent explicitly opted in to full access)
      - ``["read_file", "search_memory"]`` → only those two schemas

    This prevents agents without an explicit ``allowed_tools`` declaration
    from silently receiving every registered tool.

    Args:
        allowed_tools: List of tool names declared in the agent's YAML config.

    Returns:
        List of JSON-schema dicts to pass to the LLM tool-call API.
    """
    if not allowed_tools:
        # Default-deny: no declaration → no tools
        return []

    if _WILDCARD in allowed_tools:
        # Explicit wildcard: grant all registered tools
        return list(TOOLS_SCHEMA)

    # Explicit list: return only declared tools that exist in the registry
    return [_SCHEMA_BY_NAME[name] for name in allowed_tools if name in _SCHEMA_BY_NAME]
