#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def main():
    # Tenta obter a memória de trabalho para injetar o estado atual
    working_context = os.path.join(".agent", "working-context.md")
    context_content = ""
    
    if os.path.exists(working_context):
        try:
            with open(working_context, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Pega as primeiras 25 linhas (resumo do status e stack) para economizar tokens
                context_content = "".join(lines[:25])
        except Exception:
            pass

    instincts = """
=== SYSTEM REMINDER: TIME BALI-AGENT ===
Você opera permanentemente como o time Bali-Agent. Siga os instintos abaixo:
1. MEMÓRIA: Leia .agent/working-context.md e task.md para o status/decisões sem re-indexar o código.
2. ORQUESTRAÇÃO: Mudanças de código/arquitetura passam pelo Orchestrator e Planner. Nunca trabalhe sozinho.
3. ESPECIALISTAS: Delegue tarefas para o especialista técnico em .agent/team/spec-*.md.
4. QUALIDADE: Toda entrega passa pelo Reviewer (.agent/team/reviewer.md) para checks de segurança e testes.
5. ANTILOOP: Build/teste falhou 3 vezes com o mesmo erro? Pare, reverta os arquivos e peça ajuda no chat.
=========================================
"""
    print(instincts)
    if context_content:
        print("=== STATUS ATUAL DO PROJETO (MEMÓRIA) ===")
        print(context_content)
        print("=" * 40 + "\n")

if __name__ == "__main__":
    main()
