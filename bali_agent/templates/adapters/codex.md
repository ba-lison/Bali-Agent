# Codex Adapter

Codex possui subagentes nativos e custom agents por arquivo TOML de projeto.
O installer do Bali-Agent materializa cada `.agent/team/*.md` como
`.codex/agents/<id>.toml` e cria `.codex/config.toml`.

Contrato:
- O Orchestrator deve pedir explicitamente o spawn de subagentes Codex.
- Use os agents customizados (`orchestrator`, `planner`, `reviewer`, `spec-*`)
  para trabalho isolado.
- Se a sessão Codex atual não puder spawnar subagentes, use o Bali Runtime:

```bash
python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Para validar:

```bash
python .agent/runtime/bali_runtime.py verify
python .agent/runtime/bali_runtime.py list-agents
```

Nunca opere Orchestrator, Planner, especialista e Reviewer como papéis no mesmo contexto.
