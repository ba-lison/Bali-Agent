# -*- coding: utf-8 -*-
"""Tool Registry managing functional definitions and parameters for LLM tooling."""

from typing import List, Dict, Any

TOOLS_SCHEMA = [
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
            "name": "send_handoff",
            "description": "Envia uma mensagem estruturada para outro subagente via HandoffBus. Use quando precisar coordenar ou transferir contexto entre subagentes sem precisar de uma nova invocação completa.",
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

def get_allowed_schemas(allowed_tools: List[str]) -> List[Dict[str, Any]]:
    """Return schema structures filtered by agent permissions."""
    if not allowed_tools:
        return TOOLS_SCHEMA
    return [t for t in TOOLS_SCHEMA if t["function"]["name"] in allowed_tools]
