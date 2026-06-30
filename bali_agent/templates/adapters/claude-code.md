# Claude Code Adapter

Claude Code usa o contrato subagent-first do Bali quando a superficie consegue carregar `.claude/agents/*.md` e despachar agentes nativos.

Superficies esperadas:
- CLI/terminal (`claude`).
- Desktop Code tab.
- VS Code e JetBrains via integracoes.
- Web/cloud quando a sessao tem workspace e acesso aos arquivos `.claude/`.

Contrato:
- Leia `.agent/subagent.config.yaml`.
- Carregue `CLAUDE.md`, `AGENTS.md` e os protocolos principais.
- Use `.claude/agents/*.md` para o Core Team inteiro: Orchestrator, Discovery, PRD Writer, SDD Architect, Planner, Implementer, QA, Security, Reviewer, Recruiter, Memory Curator e Docs.
- Use `spec-*` em `.claude/agents/` para especialistas fixos do projeto.
- Use agentes temporarios apenas para tarefas pontuais.
- Preserve hooks em `.claude/settings.json` quando existirem; eles reforcam reinjecao de contexto e nao substituem subagentes.
- Cada subagente recebe contexto minimo: tarefa, artefatos relevantes e prior output necessario.
- Se a superficie atual nao conseguir executar subagentes nativos, use Bali Runtime.
- Nunca substitua subagentes por role-play no mesmo contexto.

API vs Desktop nao e o criterio principal. O criterio e: existe mecanismo real de subagente/tool calling isolado? Se sim, adapter nativo. Se nao, Bali Runtime. Se nenhum caminho existir, falha fechada.
