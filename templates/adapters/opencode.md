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
- Se a instalação OpenCode atual não puder criar child sessions, use:

```bash
python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Defina `BALI_LLM_COMMAND` para plugar o provedor/modelo desejado.
