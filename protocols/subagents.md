# Protocolo de Subagentes Reais

> Define o contrato operacional do Bali-Agent: o framework e seus adapters devem
> materializar subagentes reais. Role-play de varios papeis no mesmo contexto nao
> e modo valido de execucao.

---

## 1. Objetivo Master

O Bali-Agent e subagent-first. Ele deve operar com subagentes reais em todo projeto e em toda tarefa que exija trabalho de time. "Real" significa que Orchestrator, Discovery, PRD Writer, SDD Architect, Planner, Implementer, QA, Security, Reviewer, Recruiter, Memory Curator, Docs e especialistas possuem definicao propria e sao executados por um mecanismo que preserve isolamento operacional: subagente nativo da ferramenta, processo separado, sessao separada ou chamada separada ao modelo.

O modelo de linguagem e intercambiavel. A orquestracao por subagentes nao e opcional. Multi-modelo e uma capacidade opcional: se o host permite escolher modelo por subagente, use `model_policy`; se nao permite, todos os subagentes usam `host-default`.

Este protocolo deve funcionar em qualquer ambiente por um destes caminhos:

1. Adapter nativo da ferramenta.
2. Bali Runtime.
3. Falha fechada se nenhum isolamento real estiver disponivel.

---

## 2. Product Spine

Discovery, PRD Writer e SDD Architect ficam acima de qualquer execucao grande. Eles sao o funil obrigatorio de entendimento.

```text
Discovery -> PRD Writer -> SDD Architect
```

Projeto novo sempre passa por essa espinha. Projeto existente ou feature grande tambem passa por ela quando altera produto, dados, arquitetura, integracao, permissoes, billing, IA, deploy ou seguranca.

Tarefas pequenas podem seguir fluxo reduzido, mas ainda usam especialista e Reviewer.

---

## 3. Core Team Obrigatorio

Todo projeto Bali deve conter estes agentes em `.agent/team/`:

- `orchestrator`
- `discovery`
- `prd-writer`
- `sdd-architect`
- `planner`
- `implementer`
- `qa`
- `security`
- `reviewer`
- `recruiter`
- `memory-curator`
- `docs`

O Core Team existe em todo projeto. Ele nao depende da stack.

---

## 4. Tipos de Subagente

| Tipo | Exemplos | Ciclo de vida |
|------|----------|---------------|
| Core Team | `discovery`, `prd-writer`, `sdd-architect`, `reviewer`, `memory-curator` | Sempre presente |
| Project-fixed | `spec-supabase`, `spec-cloudflare`, `spec-lgpd` | Fixo no projeto quando a competencia e recorrente |
| Temporary | `temp-debug-timeout`, `temp-pdf-audit` | Criado para uma tarefa pontual e descartado apos o run |

Regra de criacao:

- Recorrente ou estrutural no projeto: especialista fixo `spec-*`.
- Pontual ou exploratorio: agente temporario.
- Essencial a todo projeto: Core Team.

---

## 5. Recruiter / Team Builder

O Recruiter decide quando o projeto precisa de um novo especialista fixo. Ele nao substitui Discovery, PRD ou SDD.

O Recruiter deve:

- Avaliar stack, dominios recorrentes e lacunas do time.
- Propor `spec-*` fixo quando a competencia for recorrente.
- Recomendar agente temporario quando a demanda for pontual.
- Registrar escopo, gatilhos de roteamento e motivo da criacao.
- Acionar Memory Gate apos criar ou promover especialista.

---

## 6. Ordem de Resolucao

| Prioridade | Mecanismo | Descricao |
|-----------|-----------|-----------|
| 1. Adapter nativo | Mecanismo oficial da ferramenta | `.claude/agents/`, `.opencode/agents/`, `.codex/agents/`, Task tool, `@mention`, `define_subagent` |
| 2. Bali Runtime | `python .agent/runtime/bali_runtime.py run` | Executa agentes isolados com prompt/output proprios |
| 3. Falha fechada | Bloquear tarefa e informar humano | Usado quando nao ha adapter nativo nem Runtime disponivel |

---

## 7. Requisitos Minimos de Instalacao

- `.agent/subagent.config.yaml` deve existir com `subagents_policy.role_play_permitido: false`.
- O Core Team completo deve existir em `.agent/team/`.
- `time.product_spine` deve declarar `discovery`, `prd-writer` e `sdd-architect`.
- `time.project_fixed` deve existir, mesmo vazio.
- `time.temporary_policy` deve declarar limites para temporarios.
- `model_policy.default` deve existir e aceitar fallback `host-default`.
- Adapters nativos devem espelhar o time no formato da ferramenta hospedeira.
- Reviewer deve ser executado como subagente separado do agente que implementou a mudanca.
- `.agent/runtime/bali_runtime.py` deve suportar `verify`, `list-agents`, `create-agent` e `run`.
- `.agent/memory.md` e `.agent/working-context.md` devem existir.

---

## 8. Verificacao de Integridade

O comando `verify` deve checar:

- [ ] `.agent/subagent.config.yaml` existe e e valido.
- [ ] `subagents_policy.role_play_permitido` e `false`.
- [ ] Core Team completo existe em `.agent/team/`.
- [ ] `time.product_spine`, `time.project_fixed`, `time.temporary_policy` e `model_policy` existem.
- [ ] Adapters nativos estao sincronizados com `.agent/team/`.
- [ ] Bali Runtime esta funcional.
- [ ] Memoria curada e working context existem.

---

## 9. Contrato de Isolamento por Ferramenta

| Ferramenta | Mecanismo de isolamento | Caminho |
|-----------|-------------------------|---------|
| Claude Code | Subagentes nativos quando a superficie tem Agent/Task tool | `.claude/agents/*.md` |
| Codex | Subagentes nativos/custom agents | `.codex/agents/*.toml` |
| OpenCode | Subagentes nativos com `mode: subagent` | `.opencode/agents/*.md` |
| Antigravity | `define_subagent` e background subagents com fila segura | `.antigravity/skills/` ou `.agents/skills/` |
| Cursor | Bali Runtime quando nao houver isolamento nativo | `.cursor/rules/bali-agent.mdc` + Runtime |
| Hosts sem subagente nativo | Bali Runtime com runner de subagente, ou falha fechada | `.agent/runtime/bali_runtime.py` |

API vs Desktop nao e o criterio principal. O criterio e: existe mecanismo real de subagente/tool calling isolado? Se sim, adapter nativo. Se nao, Runtime com runner de subagente. Se nenhum existe, falha fechada.

---

## 10. Model Policy

`model_policy` descreve preferencia, nao obrigacao. Todo agente deve ter fallback para `host-default`.

```yaml
model_policy:
  default: host-default
  agents:
    orchestrator:
      preferred: strong-reasoning
      fallback: host-default
    reviewer:
      preferred: strong-reasoning
      fallback: host-default
    implementer:
      preferred: strong-coding
      fallback: host-default
```

Se o host nao suporta selecao de modelo por subagente, todos usam o modelo atual do host.

---

## 11. Subagent vs Agent-as-Tool

Subagent e membro delegado do time, com identidade, contexto minimo, handoff e revisao. Agent-as-tool e chamada pontual, stateless e encapsulada para uma funcao estreita.

Use subagent para trabalho complexo, autonomo ou com estado de projeto. Use agent-as-tool para funcoes pequenas e reutilizaveis, como transformar texto, consultar um indice ou executar uma analise isolada.

---

## 12. Falha Fechada

Nunca substitua subagentes reais por "um modelo respondendo como se fosse varios". Se a execucao isolada nao estiver disponivel via adapter nativo nem Bali Runtime, a resposta correta e bloquear a tarefa, explicar qual adapter/runtime falta e orientar a instalacao necessaria.

---

## 13. Regras Inviolaveis

1. Nunca fazer role-play de multiplos agentes no mesmo contexto.
2. Nunca o Orchestrator implementar codigo.
3. Sempre preservar Discovery -> PRD -> SDD para projeto novo e feature grande.
4. Sempre executar Reviewer como subagente separado.
5. Sempre atualizar memoria via Memory Gate ao concluir task/gate relevante.
6. Sempre usar adapter nativo quando disponivel; Bali Runtime como fallback.
7. Sempre falhar fechado se nenhum caminho de isolamento estiver disponivel.

---

Subagentes reais sempre. Product Spine acima da execucao. Multi-modelo e opcional.
