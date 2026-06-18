#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json

def extract_critical_sections(content):
    lines = content.splitlines()
    sections = []
    
    current_header = None
    current_level = 0
    current_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if current_header is not None or current_lines:
                sections.append((current_header, current_level, current_lines))
            
            level = 0
            for char in stripped:
                if char == '#':
                    level += 1
                else:
                    break
            header_name = stripped[level:].strip()
            current_header = header_name
            current_level = level
            current_lines = [line]
        else:
            current_lines.append(line)
            
    if current_header is not None or current_lines:
        sections.append((current_header, current_level, current_lines))
        
    extracted = []
    
    for header, level, slines in sections:
        if header is None:
            content_str = "\n".join(slines).strip()
            if content_str:
                extracted.append(content_str)
            continue
            
        lower_header = header.lower()
        is_target = False
        
        if level == 1 or "working context" in lower_header:
            is_target = True
        elif "status atual" in lower_header or "milestone" in lower_header:
            is_target = True
        elif "stack tecnol" in lower_header:
            is_target = True
        elif "progresso recente" in lower_header or "recent progress" in lower_header:
            is_target = True
        elif "bugs conhecidos" in lower_header or "known bugs" in lower_header:
            is_target = True
            
        if is_target:
            extracted.append("\n".join(slines).strip())
            
    return "\n\n".join(extracted).strip()

def main():
    # Tenta obter a memória de trabalho para injetar o estado atual
    payload = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
    except Exception:
        payload = {}

    project_root = (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    working_context = os.path.join(project_root, ".agent", "working-context.md")
    context_content = ""
    
    if os.path.exists(working_context):
        try:
            with open(working_context, "r", encoding="utf-8") as f:
                content = f.read()
            
            dynamic_content = extract_critical_sections(content)
            if dynamic_content:
                context_content = dynamic_content
            else:
                # fallback
                lines = content.splitlines()
                context_content = "\n".join(lines[:25])
        except Exception:
            try:
                with open(working_context, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    context_content = "".join(lines[:25])
            except Exception:
                pass

    instincts = """
=== SYSTEM REMINDER: TIME BALI-AGENT ===
Você opera permanentemente como o time Bali-Agent. Siga os instintos abaixo:
1. MEMÓRIA: Leia .agent/working-context.md e task.md para estado vivo/tarefa atual; use .agent/memory.md para histórico curado de decisões, commits, PRs e incidentes.
2. OBJETIVO MASTER: Use subagentes reais sempre. Role-play de vários papéis no mesmo contexto não é modo válido.
3. ORQUESTRAÇÃO: Mudanças de código/arquitetura passam pelo Orchestrator e Planner. Nunca trabalhe sozinho.
4. ESPECIALISTAS: Delegue tarefas para o especialista técnico em .agent/team/spec-*.md ou .claude/agents/*.md.
5. QUALIDADE: Toda entrega passa pelo Reviewer (.agent/team/reviewer.md) para checks de segurança e testes.
6. ANTILOOP: Build/teste falhou 3 vezes com o mesmo erro? Pare, registre o erro/arquivos envolvidos e peça ajuda no chat. Não descarte alterações automaticamente.
=========================================
"""
    print(instincts)
    if context_content:
        print("=== STATUS ATUAL DO PROJETO (MEMÓRIA) ===")
        print(context_content)
        print("=" * 40 + "\n")

if __name__ == "__main__":
    main()
