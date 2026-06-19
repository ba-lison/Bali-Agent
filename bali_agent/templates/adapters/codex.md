# Codex Adapter

Codex possui subagentes nativos e custom agents por arquivo TOML de projeto.
O installer do Bali-Agent materializa cada `.agent/team/*.md` como
`.codex/agents/<id>.toml` e cria `.codex/config.toml`.

Contrato:
- O Orchestrator deve pedir explicitamente o spawn de subagentes Codex.
- Use fila segura: `max_parallel: 1` para agentes de escrita. Nao dispare frontend e backend em paralelo quando houver contrato de dados entre eles.
- Cada subagente deve receber contexto minimo: tarefa, arquivos/contratos relevantes e prior output necessario, nunca historico completo da sessao pai.
- Use os agents customizados (`orchestrator`, `planner`, `reviewer`, `spec-*`)
  para trabalho isolado.
- Se um subagente falhar por quota, timeout ou crash, registre `agent_failed` e devolva esse evento ao Orchestrator antes de continuar.
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
