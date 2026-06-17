#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def main():
    # Caminho para o AGENTS.md na raiz do projeto do usuário
    # Como o hook roda na raiz do projeto do usuário, o AGENTS.md deve estar na raiz.
    agents_md = "AGENTS.md"
    
    if not os.path.exists(agents_md):
        return
        
    try:
        with open(agents_md, "r", encoding="utf-8") as f:
            content = f.read()
            
        print("\n=== SYSTEM REMINDER: CONSTITUIÇÃO BALI-SUBAGENT ===")
        print("Você está operando como parte do time Bali-Subagent neste projeto.")
        print("Siga estritamente a constituição abaixo para qualquer pedido:")
        print("-" * 50)
        print(content)
        print("=" * 50 + "\n")
    except Exception as e:
        # Silencioso em caso de erro para não quebrar a experiência do terminal
        pass

if __name__ == "__main__":
    main()
