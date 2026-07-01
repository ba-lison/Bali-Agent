# -*- coding: utf-8 -*-
"""LLM Client module with sliding window, retries, and output truncation."""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import List, Optional, Union

MAX_HISTORY_CHARS = 80000  # ~20k tokens
MAX_PRIOR_CHARS = 12000

def _truncate_prior(text: str) -> str:
    """Truncate prior agent outputs to fit within LLM context limits."""
    if not text:
        return ""
    if len(text) <= MAX_PRIOR_CHARS:
        return text
    return text[:MAX_PRIOR_CHARS] + "\n\n...[output truncado para caber no contexto]..."

def _extract_text(response: dict) -> str:
    """Helper to extract text content from various LLM response formats."""
    if not response:
        return ""
    if "choices" in response:
        return response["choices"][0]["message"].get("content", "")
    elif "content" in response:
        content_blocks = response["content"]
        text = ""
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text += block.get("text", "")
        return text
    return ""

def _trim_history(messages: List[dict]) -> List[dict]:
    """Compress older history via summarization if total character count exceeds limit."""
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            text = ""
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")
            content = text
        total += len(str(content or ""))
        
    if total < MAX_HISTORY_CHARS:
        return messages

    # Keep system prompt and last 6 messages, summarize the middle
    system_messages = [m for m in messages if m.get("role") == "system"]
    # Messages in the middle exclude system prompts and last 6 messages
    non_system = [m for m in messages if m.get("role") != "system"]
    if len(non_system) <= 6:
        return messages
        
    tail = non_system[-6:]
    middle = non_system[:-6]
    
    middle_texts = []
    for m in middle:
        role = m.get("role", "user").upper()
        content = m.get("content", "")
        if isinstance(content, list):
            text = ""
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")
            content = text
        if content:
            middle_texts.append(f"{role}: {content}")
            
    if not middle_texts:
        return messages

    summary_prompt = "Sumarize em 200 palavras as seguintes interacoes anteriores:\n\n" + " | ".join(middle_texts)
    
    # We call the LLM API using only system prompts + user summary request
    summary_messages = []
    if system_messages:
        summary_messages.append(system_messages[0])
    summary_messages.append({"role": "user", "content": summary_prompt})
    
    try:
        summary_response = call_llm_api(summary_messages)
        summary_text = _extract_text(summary_response)
        if not summary_text:
            summary_text = "(Erro ao gerar resumo de contexto anterior)"
    except Exception as e:
        summary_text = f"(Erro ao gerar resumo de contexto anterior: {e})"
        
    compressed_message = {
        "role": "assistant",
        "content": f"[Resumo de contexto anterior]: {summary_text}"
    }
    
    return system_messages + [compressed_message] + tail

def call_llm_api(messages: List[dict], tools: Optional[List[dict]] = None) -> Optional[dict]:
    """Call the configured LLM API with built-in exponential backoff retries for failures."""
    provider = os.environ.get("BALI_SUBAGENT_PROVIDER", "local").lower()
    model = os.environ.get("BALI_SUBAGENT_MODEL")
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

    else:  # default: local OpenAI-compatible runner
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

    max_attempts = 5
    delay = 2
    
    for attempt in range(1, max_attempts + 1):
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            print(f"[!] Erro de HTTP na chamada de API (Tentativa {attempt}/{max_attempts}): {e.code} - {e.reason}\nBody: {error_body}", file=sys.stderr)
            
            # Retry only on transient errors (429 or 5xx)
            if e.code == 429 or e.code == 503 or (500 <= e.code < 600):
                if attempt < max_attempts:
                    print(f"[*] Aguardando {delay} segundos antes de tentar novamente...", file=sys.stderr)
                    time.sleep(delay)
                    delay *= 2
                    continue
                else:
                    raise e
            else:
                raise e
        except Exception as e:
            print(f"[!] Erro de conexao na chamada de API (Tentativa {attempt}/{max_attempts}): {e}", file=sys.stderr)
            if attempt < max_attempts:
                print(f"[*] Aguardando {delay} segundos antes de tentar novamente...", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
                continue
            else:
                raise e
    return None
