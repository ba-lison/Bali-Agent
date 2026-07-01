# OpenCode Adapter

OpenCode possui subagentes nativos configuraveis. O installer do Bali-Agent
cria `opencode.json` com instrucoes criticas e materializa cada
`.agent/team/*.md` como `.opencode/agents/<id>.md` com `mode: subagent`.

Contrato:
- Primary agents devem invocar `orchestrator`, `planner`, `reviewer` e `spec-*`
  por @mention ou por comando configurado com `subtask: true`.
- `opencode.json` deve incluir `AGENTS.md`, `.agent/protocols/subagents.md` e
  `.agent/protocols/routing.md` em `instructions`.
- Cada subagente deve rodar em child session própria.
- Use fila segura: `max_parallel: 1` para agentes de escrita. Nao inicie backend e frontend em paralelo quando um consome contrato do outro.
- Cada child session recebe apenas contexto minimo: tarefa, artefatos/contratos relevantes e prior output necessario.
- Se uma child session falhar por quota, timeout ou crash, registre `agent_failed` e devolva esse evento ao Orchestrator antes de novo dispatch.
- Se a instalação OpenCode atual não puder criar child sessions, use:

```bash
python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Se o OpenCode atual nao puder criar child sessions, configure o Bali Runtime
como runner de subagente. Nao substitua subagentes por um prompt generico.
