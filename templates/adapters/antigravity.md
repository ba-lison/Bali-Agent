# Antigravity Adapter

Antigravity possui subagentes/background subagents e pode definir subagentes
customizados dinamicamente via `define_subagent`.

Contrato:
- Carregue `.antigravity/skills/bali-agent/SKILL.md` quando disponível.
- Para cada `.agent/team/*.md`, defina um subagente Antigravity equivalente com
  system prompt próprio.
- Execute Orchestrator, Planner, especialista e Reviewer como subagentes/threads
  separados.
- Se a superfície atual não expuser `define_subagent` ou background subagents,
  use o Bali Runtime como fallback obrigatório.

```bash
python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

O Reviewer deve rodar separado do agente que implementou a mudança.
