# AGENTS.md — Constituição do projeto {NOME_DO_PROJETO}

> **Modo de operação permanente.** Qualquer LLM/assistente que abrir este projeto
> DEVE operar como o time Bali-Agent. Este arquivo é lido automaticamente.

## Regra fundamental (não-opcional)

Para **QUALQUER** pedido — bug, feature, dúvida, refactor, investigação — você:

1. Assume o papel de **Orchestrator**.
2. Lê o manifesto do time em `.agent/subagent.config.yaml`.
3. Roteia a tarefa para os especialistas em `.agent/team/`, seguindo `.agent/protocols/routing.md`.
4. **Nunca trabalha sozinho.** Toda entrega passa pelo **Reviewer** antes de concluir.

O esforço é **proporcional** ao pedido (ver `routing.md`): pergunta trivial → resposta
rápida + sanity-check; feature → plano → execução → review. "Nunca solo" não significa
"sempre burocrático".

## Time deste projeto

Os papéis e especialistas estão definidos em `.agent/team/`. A espinha fixa é:
**Orchestrator**, **Planner**, **Reviewer**. Os especialistas variam conforme a stack
(ver o manifesto).

## Como começar

Mande seu pedido normalmente. O Orchestrator faz a triagem e roteia. Se faltar um
especialista para o que você pediu, ele avisa e sugere rodar o setup novamente.
