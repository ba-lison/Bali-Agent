# Protocolo de Roteamento

> Como o Orchestrator transforma QUALQUER pedido em trabalho de time. Aplica-se a
> todo projeto que tenha `.agent/subagent.config.yaml`.

## Triagem

Ao receber um pedido, o Orchestrator classifica o tamanho:

| Classe | Exemplos | Caminho |
|--------|----------|---------|
| **Trivial** | dúvida pontual, explicação, leitura de 1 arquivo | Especialista responde direto → Reviewer faz sanity-check rápido |
| **Pequeno** | bugfix localizado, ajuste de copy, tweak de config | Especialista executa → Reviewer revisa |
| **Médio/Grande** | feature, refactor, mudança multi-arquivo | Planner decompõe → especialista(s) executam → Reviewer revisa |

A triagem é explícita: o Orchestrator diz ao usuário em 1-2 linhas qual classe e qual caminho.

## Processo proporcional

A constituição obriga rotear **sempre** pelo time, mas o esforço é proporcional ao pedido.
Nunca aplique o pipeline pesado a uma pergunta trivial; nunca pule o Reviewer numa feature.
O objetivo é "nunca solo", não "sempre burocrático".

## Seleção de especialista

1. Leia `time.especialistas[].escopo` no manifesto.
2. Escolha o especialista cujo escopo melhor casa com a tarefa, mapeando pela extensão do arquivo ou contexto:
   - **`frontend.md` (`spec-frontend-*`):** Interface, layouts e estilos. Ativado para arquivos `.tsx`, `.jsx`, `.ts` (client-side/componentes), `.html`, `.css`, `.scss`, `.vue`.
   - **`backend.md` (`spec-backend-*`):** APIs, lógica de negócios, integrações. Ativado para lógica server-side, rotas e controladores (arquivos `.py`, `.go`, `.cs`, `.js`/`.ts` do lado servidor).
   - **`database.md` (`spec-database-*`):** Estrutura de dados e queries. Ativado para arquivos `.sql`, esquemas ORM (ex.: `schema.prisma`, migrations) ou queries brutas.
   - **`devops.md` (`spec-devops`):** Infraestrutura, containers e builds. Ativado para `Dockerfile`, `docker-compose.yml`, fluxos de CI/CD (`.github/workflows/*.yaml`), configurações Web/Nginx.
   - **`security.md` (`spec-security`):** Permissões, criptografia e políticas de segurança. Ativado para regras de RLS (Row Level Security), middlewares de auth, controle de acessos ou auditoria.
   - **`testing.md` (`spec-testing`):** Testes e QA. Ativado para arquivos em diretórios `tests/`, `__tests__/`, ou com sufixos `.test.*` e `.spec.*`.
   - **`docs.md` (`spec-docs`):** Documentação. Ativado para `.md` na documentação do projeto, guias, esquemas OpenAPI/Swagger.
   - **`implementer.md` (Geral):** Engenharia de software genérica, refatoração estrutural e scripts auxiliares que não pertençam a uma stack especializada.
3. Se nenhum casar, crie um especialista real novo antes de executar a tarefa:
   - gere `.agent/team/spec-<nome>.md` com escopo claro e reutilizável;
   - registre o novo especialista em `.agent/subagent.config.yaml`;
   - quando houver adapter nativo, espelhe o arquivo no formato da ferramenta;
   - quando não houver adapter nativo, use `python .agent/runtime/bali_runtime.py create-agent --id spec-<nome> --scope "<escopo>"`.
4. Tarefas que cruzam stacks podem envolver mais de um especialista em sequência, sempre com fila (`max_parallel: 1`) para agentes de escrita.

## Sequenciamento, contratos e quota

O Orchestrator deve usar `execution_mode: "sequential"`, `max_parallel: 1` e `context_scope: "minimal"` por padrão. Mesmo quando a ferramenta nativa suporta background agents, agentes de escrita não iniciam em paralelo.

Para tarefas acopladas, declare o contrato entre etapas:

1. O produtor roda primeiro e grava o artefato contratual em `produces` (schema, tipo, endpoint, migração, interface).
2. O consumidor roda depois com `depends_on` e `consumes`, recebendo apenas o contrato necessário.
3. Backend/API/schema deve preceder frontend/UI quando a UI depende do formato de resposta.
4. O Reviewer valida o artefato final e também pode validar o contrato intermediário.

Cada subagente recebe apenas prompt, tarefa, artefatos/contratos relevantes e prior output necessário. Não herde histórico completo da sessão pai.

Se um subagente falhar por quota, timeout ou crash, registre `agent_failed` com `agent`, `error_type`, `retryable`, `message` e `next_retry_at`, então devolva esse evento ao Orchestrator antes de qualquer novo dispatch.

## Modo Operate

Fluxo padrão de projeto em andamento:
`pedido → triagem → (Planner se médio/grande) → especialista(s) → Reviewer → entrega`.

## Modo Greenfield

Quando `modo: greenfield`, o roteamento segue o pipeline SDLC de
`agents/_spine/orchestrator/workflows/novo-projeto.md`, com os gates de
`protocols/approval-gates.md`.

Pipeline obrigatório:
`Discovery → PRD Writer → SDD Architect → Planner → especialista(s) → Reviewer`.

O humano aprova gates de negócio e arquitetura; os agentes executam as etapas
intermediárias sem pedir prompts repetitivos.

## Saída ao usuário

Toda resposta do Orchestrator começa com uma linha de roteamento, ex.:
`🎯 Roteando: [classe=Médio] Planner → spec-supabase → Reviewer`.
