# Claude Code Adapter

Use `CLAUDE.md` para carregar instrucoes persistentes, hooks em
`.claude/settings.json` para reinjecao por turno e subagentes nativos em
`.claude/agents/*.md`.

Contrato:
- Leia `.agent/subagent.config.yaml`.
- Confirme que `CLAUDE.md` importa `AGENTS.md` ou que `.claude/CLAUDE.md`
  referencia a constituicao Bali-Agent.
- Confirme que `.claude/settings.json` contem hooks `SessionStart` e
  `UserPromptSubmit` apontando para `.agent/hooks/claude_hook.py`.
- Use `.claude/agents/orchestrator.md`, `.claude/agents/planner.md`, `.claude/agents/reviewer.md` e `.claude/agents/spec-*.md`.
- Nunca substitua esses agentes por role-play no mesmo contexto.
- Se os agentes nativos não existirem, rode `python .agent/runtime/bali_runtime.py verify` e corrija o setup.
