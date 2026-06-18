#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bali-Agent Runtime Engine (Subagent Bridge).
Allows execution of Orchestrator loop with real tool calling and isolated subagents.

Usage:
  python .agent/run.py "instrução do usuário"
"""
import os
import sys
import json
import yaml
import urllib.request
import urllib.error
import subprocess

# Log helper printing to stderr to preserve stdout for final output
def log(msg):
    print(f"[*] {msg}", file=sys.stderr, flush=True)

def log_error(msg):
    print(f"[!] Erro: {msg}", file=sys.stderr, flush=True)

# Exposes available tools to the Orchestrator and specialists
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
    }
]

def load_config():
    config_path = os.path.join(".agent", "subagent.config.yaml")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        log_error(f"Falha ao carregar manifesto do time: {e}")
        return {}

def load_working_context():
    context_path = os.path.join(".agent", "working-context.md")
    if not os.path.exists(context_path):
        return ""
    try:
        with open(context_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log_error(f"Falha ao ler working-context.md: {e}")
        return ""

def load_agent_prompt(agent_name):
    search_paths = [
        os.path.join(".agent", "team", f"{agent_name}.md"),
        os.path.join(".agent", "team", f"spec-{agent_name}.md"),
        os.path.join("agents", "_spine", agent_name, "AGENT.md"),
        os.path.join("agents", agent_name, "AGENT.md"),
    ]
    team_dir = os.path.join(".agent", "team")
    if os.path.isdir(team_dir):
        for f in os.listdir(team_dir):
            if f.startswith(f"spec-{agent_name}") and f.endswith(".md"):
                search_paths.insert(0, os.path.join(team_dir, f))

    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return f"Você é o subagente especialista '{agent_name}'. Execute a tarefa com qualidade máxima."

def execute_tool(name, args):
    log(f"Executando ferramenta: {name} com argumentos: {json.dumps(args)}")
    if name == "read_file":
        path = args.get("path")
        if not path:
            return "Erro: parâmetro 'path' ausente."
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Erro ao ler arquivo {path}: {e}"

    elif name == "write_file":
        path = args.get("path")
        content = args.get("content")
        if not path or content is None:
            return "Erro: parâmetros 'path' ou 'content' ausentes."
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Arquivo '{path}' gravado com sucesso."
        except Exception as e:
            return f"Erro ao gravar arquivo {path}: {e}"

    elif name == "run_command":
        command = args.get("command", "")
        if not command:
            return "Erro: parâmetro 'command' ausente."
            
        # Agent Shield - Segurança Ativa na Execução do Loop
        dangerous_keywords = ["rm ", "del ", "format ", "curl ", "wget ", "sh ", "bash ", "powershell "]
        safe_prefixes = ("pytest", "python", "npm", "pip", "cargo", "go", "git status", "git diff", "git log", "dir", "ls", "echo")
        
        is_dangerous = any(kw in command.lower() for kw in dangerous_keywords)
        is_safe = command.strip().startswith(safe_prefixes)
        
        if is_dangerous or not is_safe:
            log(f"Alerta de Segurança: Comando '{command}' considerado potencialmente perigoso ou não-padrão.")
            approval_msg = f"O agente solicitou a execução do seguinte comando considerado sensível/não-padrão:\n  > {command}\n\nVocê autoriza a execução? (S/N)"
            print(f"\n[AGENT SHIELD - EXECUÇÃO SENSÍVEL]\n{approval_msg}")
            try:
                response = input("> ").strip().lower()
                if response not in ["s", "sim", "y", "yes"]:
                    return "Erro: Execução do comando rejeitada pelo usuário por motivos de segurança."
            except KeyboardInterrupt:
                return "Erro: Execução do comando cancelada pelo usuário."
                
        try:
            res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            output = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
            return output
        except Exception as e:
            return f"Erro ao rodar comando '{command}': {e}"

    elif name == "request_human_approval":
        message = args.get("message")
        print(f"\n[GATE DE APROVAÇÃO HUMANA]\n{message}")
        try:
            response = input("\nSua resposta/aprovação (pressione Enter para confirmar padrão):\n> ")
            return f"Aprovação do Usuário: {response if response.strip() else 'Aprovado sem observações'}"
        except KeyboardInterrupt:
            return "Erro: Operação interrompida pelo usuário."

    elif name == "invoke_subagent":
        agent_name = args.get("agent_name")
        prompt = args.get("prompt")
        if not agent_name or not prompt:
            return "Erro: parâmetros 'agent_name' ou 'prompt' ausentes."
        
        log(f"Subagente '{agent_name}' invocado. Iniciando loop de execução isolado...")
        return run_agent_loop(agent_name, prompt)

    elif name == "search_memory":
        query = args.get("query", "").lower()
        if not query:
            return "Erro: parâmetro 'query' ausente."
        
        memory_path = os.path.join(".agent", "memory.md")
        if not os.path.exists(memory_path):
            return "Nenhuma memória histórica gravada ainda."
            
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            entries = content.split("## ")
            matching_entries = []
            for entry in entries:
                if not entry.strip():
                    continue
                if query in entry.lower():
                    matching_entries.append("## " + entry.strip())
                    
            if not matching_entries:
                return f"Nenhuma entrada histórica encontrada na busca por: '{query}'"
                
            return "\n\n".join(matching_entries)
        except Exception as e:
            return f"Erro ao acessar memória: {e}"

    return f"Erro: Ferramenta '{name}' desconhecida."

def run_agent_loop(agent_name, prompt, max_loops=5):
    agent_prompt = load_agent_prompt(agent_name)
    system_prompt = f"{agent_prompt}\n\nVocê é o especialista '{agent_name}'. Execute a tarefa usando as ferramentas disponíveis."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    loop_count = 0
    while loop_count < max_loops:
        loop_count += 1
        log(f"Subagente '{agent_name}' - Iteração {loop_count}...")
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
                    
                    if tool_name == "invoke_subagent":
                        tool_output = "Erro: Subagentes não podem invocar outros subagentes diretamente."
                    else:
                        try:
                            tool_args = json.loads(function_info["arguments"])
                        except Exception:
                            tool_args = {}
                        tool_output = execute_tool(tool_name, tool_args)
                        
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
                    
                    if tool_name == "invoke_subagent":
                        tool_output = "Erro: Subagentes não podem invocar outros subagentes."
                    else:
                        tool_output = execute_tool(tool_name, tool_args)
                        
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

def save_context_auto(user_instruction, history_messages):
    log("Salvando memória de trabalho de forma automatizada...")
    working_context = load_working_context()
    if not working_context:
        return
        
    history_text = ""
    for m in history_messages[-6:]:
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, list):
            txt = ""
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    txt += block.get("text", "")
            content = txt
        if role and content:
            history_text += f"{role.upper()}: {content}\n"

    system_prompt = (
        "Você é a engine de persistência do Bali-Agent. Sua única tarefa é atualizar o arquivo `.agent/working-context.md` "
        "com base nas ações e decisões tomadas no histórico recente da sessão.\n\n"
        "Retorne APENAS o conteúdo completo do arquivo `.agent/working-context.md` atualizado no formato Markdown. "
        "Não adicione comentários, explicações ou tags adicionais (como ```markdown). O arquivo deve ser editado de forma incremental, "
        "atualizando a Milestone se necessário, a Data de Atualização, o Progresso Recente (marcando [x]) e bugs conhecidos."
    )
    
    prompt = (
        f"Histórico Recente:\n{history_text}\n\n"
        f"Conteúdo Atual do working-context.md:\n{working_context}"
    )
    
    sub_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    response = call_llm_api(sub_messages)
    updated_content = None
    if response and "choices" in response:
        updated_content = response["choices"][0]["message"]["content"]
    elif response and "content" in response:
        updated_content = response["content"][0]["text"]
        
    if updated_content:
        cleaned = updated_content.strip()
        if cleaned.startswith("```markdown"):
            cleaned = cleaned[11:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            context_path = os.path.join(".agent", "working-context.md")
            with open(context_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
            log("working-context.md atualizado com sucesso.")
        except Exception as e:
            log_error(f"Falha ao persistir working-context.md: {e}")

def call_llm_api(messages, tools=None):
    provider = os.environ.get("BALI_LLM_PROVIDER", "ollama").lower()
    model = os.environ.get("BALI_LLM_MODEL")
    api_key = os.environ.get("BALI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GEMINI_API_KEY")
    endpoint = os.environ.get("BALI_LLM_ENDPOINT")

    if provider == "openai":
        url = endpoint or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key or ''}"
        }
        payload = {
            "model": model or "gpt-4o",
            "messages": messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

    elif provider == "anthropic":
        url = endpoint or "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key or "",
            "anthropic-version": "2023-06-01"
        }
        
        system_content = ""
        anthropic_messages = []
        for m in messages:
            if m["role"] == "system":
                system_content = m["content"]
            else:
                anthropic_messages.append({"role": m["role"], "content": m["content"]})

        payload = {
            "model": model or "claude-3-5-sonnet-20241022",
            "messages": anthropic_messages,
            "max_tokens": 4000
        }
        if system_content:
            payload["system"] = system_content
            
        if tools:
            anthropic_tools = []
            for t in tools:
                func = t["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func["parameters"]
                })
            payload["tools"] = anthropic_tools

    elif provider == "gemini":
        url = endpoint or f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key={api_key or ''}"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or "gemini-1.5-pro",
            "messages": messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

    else:  # default: ollama
        url = endpoint or "http://localhost:11434/v1/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or "llama3",
            "messages": messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        log_error(f"Erro de HTTP na chamada de API: {e.code} - {e.reason}\nBody: {error_body}")
        return None
    except Exception as e:
        log_error(f"Erro de conexão na chamada de API: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python .agent/run.py \"instrução do usuário\"")
        sys.exit(1)
        
    user_instruction = sys.argv[1]
    
    log("Iniciando Bali-Agent Runtime Bridge...")
    config = load_config()
    working_context = load_working_context()
    
    orchestrator_prompt = load_agent_prompt("orchestrator")
    
    system_prompt = f"{orchestrator_prompt}\n\n=== CONTEXTO DO PROJETO ===\n"
    system_prompt += f"Configuração do Time:\n{json.dumps(config, indent=2)}\n\n"
    if working_context:
        system_prompt += f"Memória de Trabalho Recente:\n{working_context}\n"
    system_prompt += "===========================\n"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_instruction}
    ]
    
    loop_count = 0
    max_loops = 15
    has_changes = False
    
    while loop_count < max_loops:
        loop_count += 1
        log(f"Executando iteração {loop_count} do Orchestrator...")
        
        response = call_llm_api(messages, tools=TOOLS)
        if not response:
            log_error("Falha ao receber resposta do Orchestrator LLM. Encerrando.")
            sys.exit(1)
            
        if "choices" in response:
            choice = response["choices"][0]
            message = choice["message"]
            content = message.get("content")
            tool_calls = message.get("tool_calls")
            
            messages.append(message)
            
            if content and not tool_calls:
                print("\n=== RESPOSTA DO ORCHESTRATOR ===")
                print(content)
                break
                
            if tool_calls:
                has_changes = True
                for tool_call in tool_calls:
                    function_info = tool_call["function"]
                    tool_name = function_info["name"]
                    try:
                        tool_args = json.loads(function_info["arguments"])
                    except Exception:
                        tool_args = {}
                    
                    tool_output = execute_tool(tool_name, tool_args)
                    
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
                print("\n=== RESPOSTA DO ORCHESTRATOR ===")
                print(text_content)
                break
                
            if tool_requests:
                has_changes = True
                tool_results = []
                for tool_req in tool_requests:
                    tool_name = tool_req["name"]
                    tool_args = tool_req["input"]
                    tool_call_id = tool_req["id"]
                    
                    tool_output = execute_tool(tool_name, tool_args)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": str(tool_output)
                    })
                
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
        else:
            log_error(f"Formato de resposta inesperado do LLM: {json.dumps(response)}")
            sys.exit(1)
            
    if loop_count >= max_loops:
        log_error("Atingido o limite de iterações do Orchestrator para evitar loops.")
        sys.exit(1)
        
    if has_changes:
        save_context_auto(user_instruction, messages)

if __name__ == "__main__":
    main()
