# Antigravity Adapter

Antigravity possui subagentes/background subagents e pode definir subagentes
customizados dinamicamente via `define_subagent`.

Contrato:
- Carregue `.antigravity/skills/bali-agent/SKILL.md` quando disponível.
- Para cada `.agent/team/*.md`, defina um subagente Antigravity equivalente com
  system prompt próprio.
- Execute Orchestrator, Planner, especialista e Reviewer como subagentes/threads
  separados, mas com fila segura (`max_parallel: 1`) para agentes de escrita.
- Nao use background subagents para iniciar frontend e backend em paralelo quando houver contrato de dados entre eles.
- Cada subagente recebe contexto minimo: tarefa, artefatos/contratos relevantes e prior output necessario, nao historico completo da sessao pai.
- Se um subagente falhar por quota, timeout ou crash, registre `agent_failed` e devolva esse evento ao Orchestrator antes de novo dispatch.
- Se a superfície atual não expuser `define_subagent` ou background subagents,
  use o Bali Runtime como fallback obrigatório.

```bash
python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

O Reviewer deve rodar separado do agente que implementou a mudança.
