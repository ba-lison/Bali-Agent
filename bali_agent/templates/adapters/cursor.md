# Cursor Adapter

Cursor Rules e `AGENTS.md` são contexto persistente, não isolamento de execução.
O installer do Bali-Agent cria `.cursor/rules/bali-agent.mdc` para forçar o
contrato e mantém o Bali Runtime como executor real.

Fluxo obrigatório:
- Se a versão do Cursor tiver uma superfície nativa de subagentes isolados, use-a.
- Caso contrário, rode as tarefas por `python .agent/runtime/bali_runtime.py run "..."`.
- Use `.cursor/rules/bali-agent.mdc` e `AGENTS.md` apenas como enforcement de contexto.
