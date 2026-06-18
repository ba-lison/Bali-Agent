#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bali-Agent Runtime Engine (Subagent Bridge).

Allows execution of Orchestrator loop with real tool calling and isolated subagents.
"""

import os
import sys
import json
from pathlib import Path

# Path injection helper to support imports in both repository and target environments
current_dir = os.path.abspath(os.path.dirname(__file__))
templates_parent = None
if os.path.basename(current_dir) == "templates":
    templates_parent = os.path.dirname(current_dir)
elif os.path.basename(os.path.dirname(current_dir)) == "templates":
    templates_parent = os.path.dirname(os.path.dirname(current_dir))
elif os.path.isdir(os.path.join(current_dir, "templates")):
    templates_parent = current_dir
elif os.path.isdir(os.path.join(os.path.dirname(current_dir), "templates")):
    templates_parent = os.path.dirname(current_dir)

if templates_parent and templates_parent not in sys.path:
    sys.path.insert(0, templates_parent)

from templates.core.agent_loop import run_agent_loop
from templates.core.agent_manager import load_agent_prompt
from templates.core.llm_client import call_llm_api, _trim_history

def load_config(root_dir: Path) -> dict:
    manifest = root_dir / ".agent" / "subagent.config.yaml"
    if not manifest.is_file():
        return {}
    try:
        import yaml
        with manifest.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def load_working_context(root_dir: Path) -> str:
    path = root_dir / ".agent" / "working-context.md"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def save_context_auto(user_instruction: str, history_messages: list, root_dir: Path) -> None:
    """Auto-update working-context.md via LLM or deterministic fallback."""
    context_path = root_dir / ".agent" / "working-context.md"
    if not context_path.is_file():
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

    # Save backup
    backup = context_path.with_suffix(".md.bak")
    try:
        import shutil
        shutil.copy2(str(context_path), str(backup))
    except Exception:
        pass

    def apply_fallback():
        import time
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        fallback_text = (
            f"\n\n## Histórico Recente (Auto-Save Fallback - {timestamp})\n"
            f"A atualização automática via LLM falhou. Histórico de sessão:\n"
            f"- **Instrução Inicial:** {user_instruction}\n"
            f"- **Histórico Recente:**\n{history_text}\n"
        )
        try:
            current = backup.read_text(encoding="utf-8") if backup.is_file() else context_path.read_text(encoding="utf-8")
            context_path.write_text(current.rstrip() + fallback_text, encoding="utf-8")
        except Exception as e:
            print(f"[!] Falha no fallback: {e}", file=sys.stderr)

    system_prompt = (
        "Você é a engine de persistência do Bali-Agent. Sua única tarefa é atualizar o arquivo `.agent/working-context.md` "
        "com base nas ações e decisões tomadas no histórico recente da sessão.\n\n"
        "Retorne APENAS o conteúdo completo do arquivo `.agent/working-context.md` atualizado no formato Markdown. "
        "Não adicione comentários, explicações ou tags adicionais (como ```markdown)."
    )
    
    try:
        working_context = context_path.read_text(encoding="utf-8")
        prompt = f"Histórico Recente:\n{history_text}\n\nConteúdo Atual do working-context.md:\n{working_context}"
        sub_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        response = call_llm_api(sub_messages)
        if response:
            from templates.core.llm_client import _extract_text
            content = _extract_text(response).strip()
            if content.startswith("```markdown"):
                content = content[11:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Simple validation: must contain header
            if "# Working Context" in content:
                context_path.write_text(content, encoding="utf-8")
                return
        apply_fallback()
    except Exception:
        apply_fallback()

def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python .agent/run.py \"instrução do usuário\"")
        sys.exit(1)
        
    user_instruction = sys.argv[1]
    root_dir = Path(".").resolve()
    
    print("[*] Iniciando Bali-Agent Runtime Bridge...", file=sys.stderr)
    config = load_config(root_dir)
    working_context = load_working_context(root_dir)
    
    try:
        orchestrator_prompt = load_agent_prompt(root_dir, "orchestrator")
    except FileNotFoundError as e:
        print(f"[!] {e}", file=sys.stderr)
        sys.exit(1)
        
    system_prompt = (
        f"{orchestrator_prompt}\n\n=== CONTEXTO DO PROJETO ===\n"
        f"Configuração do Time:\n{json.dumps(config, indent=2)}\n\n"
    )
    if working_context:
        system_prompt += f"Memória de Trabalho Recente:\n{working_context}\n"
    system_prompt += "===========================\n"
    
    # Run the orchestrator loop
    os.environ["BALI_SESSION_ID"] = "orchestrator"
    try:
        # We run the orchestrator loop with a higher max limit of 15 loops
        result = run_agent_loop("orchestrator", user_instruction, root_dir, max_loops=15)
        print("\n=== RESPOSTA DO ORCHESTRATOR ===")
        print(result)
        
        # Load checkpoints to save context
        sessions_dir = root_dir / ".agent" / "sessions"
        checkpoint_path = sessions_dir / "orchestrator.json"
        if checkpoint_path.is_file():
            try:
                with checkpoint_path.open("r", encoding="utf-8") as f:
                    msgs = json.load(f)
                save_context_auto(user_instruction, msgs, root_dir)
            except Exception:
                pass
    except Exception as e:
        print(f"[!] Erro de execucao no Orchestrator: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
