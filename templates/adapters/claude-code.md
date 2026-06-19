# Claude Code Adapter

Claude Code surfaces suportadas pelo Bali-Agent:
- CLI/terminal (`claude`).
- Desktop Code tab.
- VS Code e JetBrains via IDE integrations.
- Web/cloud quando a sessao tiver acesso ao workspace e aos arquivos `.claude/`.

Use `CLAUDE.md` para carregar instrucoes persistentes, hooks em
`.claude/settings.json` para reinjecao por turno e subagentes nativos em
`.claude/agents/*.md`.

Claude Code nao e tratado como "uma IDE". O adapter nativo e usado quando a
superficie consegue ler `.claude/agents/*.md` e criar subagentes reais. Quando
o host for uma API sem subagentes nativos, mas com shell, rode o Bali Runtime
via `bali --root . run "<tarefa>"` ou `python .agent/runtime/bali_runtime.py run
"<tarefa>"`. Quando o host nao tiver shell/tools, Bali precisa ser exposto por
wrapper externo (MCP, CI job, webhook ou servico) antes de ser usado.

Contrato:
- Leia `.agent/subagent.config.yaml`.
- Confirme que `CLAUDE.md` importa `AGENTS.md` ou que `.claude/CLAUDE.md`
  referencia a constituicao Bali-Agent.
- Confirme que `.claude/settings.json` contem hooks `SessionStart` e
  `UserPromptSubmit` apontando para `.agent/hooks/claude_hook.py`.
- Use `.claude/agents/orchestrator.md`, `.claude/agents/planner.md`, `.claude/agents/reviewer.md` e `.claude/agents/spec-*.md`.
- Use fila segura: `max_parallel: 1` para agentes de escrita. Backend/API/schema deve produzir contrato antes de frontend/UI consumir.
- Cada subagente recebe contexto minimo: tarefa, artefatos/contratos relevantes e prior output necessario, nao o historico completo da sessao pai.
- Se um subagente falhar por quota, timeout ou crash, registre `agent_failed` e devolva esse evento ao Orchestrator antes de novo dispatch.
- Nunca substitua esses agentes por role-play no mesmo contexto.
- Se os agentes nativos não existirem, rode `python .agent/runtime/bali_runtime.py verify` e corrija o setup.
