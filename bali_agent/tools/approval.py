# -*- coding: utf-8 -*-
"""Human approval verification tool."""

import sys

def request_human_approval_tool(message: str) -> str:
    """Request explicit human confirmation for sensitive or critical actions."""
    print(f"\n[GATE DE APROVACAO HUMANA]\n{message}")
    try:
        response = input("\nSua resposta/aprovação (pressione Enter para confirmar padrão):\n> ")
        return f"Aprovação do Usuário: {response if response.strip() else 'Aprovado sem observações'}"
    except KeyboardInterrupt:
        return "Erro: Operação interrompida pelo usuário."
