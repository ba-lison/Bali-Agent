# PRD: Bali-Agent Subagent-First Team Runtime

> Autor: Codex + Alison | Data: 2026-06-30 | Versao: 1.0 | Status: Rascunho para revisao

---

## 1. Resumo Executivo

O Bali-Agent precisa voltar a ter um foco simples: coordenar trabalho por subagentes reais, nao por role-play nem por um unico agente fazendo tudo sozinho. A melhoria proposta transforma o Bali em um sistema de time permanente por projeto, com uma espinha obrigatoria de Discovery, PRD e SDD acima da execucao, especialistas fixos por projeto, agentes temporarios para tarefas pontuais e memoria automatica em cada ciclo. Multi-modelo deve existir como capacidade opcional por papel/agente, mas o produto continua funcionando quando todos os subagentes usam o modelo padrao do host.

---

## 2. Problema

### 2.1 Descricao do Problema

O desenho atual do Bali-Agent mistura tres preocupacoes: subagentes reais, detalhes de runtime/adapters e possibilidade de usar varios modelos. Essa mistura torna facil perder o objetivo principal: o usuario quer trabalhar em Claude Code, Codex, Antigravity, OpenCode ou outro host e ver um Orchestrator delegar trabalho para subagentes especializados, com contexto proprio, gates claros e revisao.

### 2.2 Evidencias

- O repositorio ja possui agentes de Discovery, PRD Writer, SDD Architect, Planner, Orchestrator, Reviewer e especialistas.
- O repositorio ja possui memoria curada e working context em `.agent/memory.md`, `.agent/working-context.md` e `bali_agent/core/memory.py`.
- O stash local `backup-before-refresh-2026-06-30` iniciou a criacao de `.claude/agents/*.md`, indicando a direcao de materializar subagentes nativos no Claude.
- A conversa de produto confirmou que PRD e SDD nao podem ser perdidos e devem ficar acima de qualquer execucao.
- A conversa tambem confirmou que multi-modelo e desejavel, mas nao deve ser requisito para subagentes.

### 2.3 Impacto de Nao Resolver

Se o foco continuar ambivalente, o Bali pode virar apenas uma colecao de prompts/adapters ou um runtime generico, em vez de um sistema que monta e evolui um time real de subagentes por projeto. Isso aumenta risco de role-play, perda de memoria, falta de PRD/SDD em features grandes e criacao caotica de especialistas.

---

## 3. Objetivo

Criar uma versao do Bali-Agent onde:

- Todo projeto possui um Core Team obrigatorio de subagentes.
- Todo projeto novo ou feature grande passa pela Product Spine: Discovery -> PRD -> SDD.
- Todo projeto pode ganhar especialistas fixos especificos, criados pelo Recruiter/Team Builder.
- Tarefas pontuais podem usar agentes temporarios sem poluir o time fixo.
- Todo ciclo aprovado atualiza memoria automaticamente.
- Cada host usa adapters para materializar o mesmo contrato de time.
- Model routing por agente existe como opcional, com fallback para `host-default`.

---

## 4. Usuarios Alvo

### 4.1 Persona Primaria

- Nome: Alison
- Perfil: desenvolvedor/produtor usando ferramentas agenticas como Claude Code, Codex, Antigravity e OpenCode.
- Necessidade principal: trabalhar com um Orchestrator que delega para subagentes reais e mantem um time por projeto.
- Jornada atual: usa uma ferramenta principal, mas precisa conduzir manualmente descoberta, planejamento, especialistas, revisao e memoria.

### 4.2 Persona Secundaria

- Nome: Engenheiro Agentico
- Perfil: pessoa ou agente que entra em um repo existente.
- Necessidade principal: entender rapidamente o time do projeto, os especialistas, a memoria, o PRD, o SDD e o proximo passo.
- Jornada atual: precisa ler docs espalhados e inferir o fluxo.

---

## 5. Hipoteses

| # | Hipotese | Como Validar | Status |
|---|---|---|---|
| H1 | Subagent-first e o contrato correto do Bali; multi-modelo e apenas opcional. | Testes e docs devem permitir rodar tudo com um unico modelo. | Nao testada |
| H2 | Um Core Team padrao reduz improviso e melhora consistencia entre projetos. | `bali init` deve criar sempre o mesmo time minimo. | Nao testada |
| H3 | Especialistas fixos por projeto melhoram tarefas recorrentes. | Criar `spec-supabase` e verificar roteamento futuro para ele. | Nao testada |
| H4 | Memory Gate automatico evita perda de aprendizado sem pedir acao ao usuario. | Concluir tarefa e verificar atualizacao de working context/memory. | Nao testada |

---

## 6. Requisitos Funcionais

### RF-001: Definir Core Team obrigatorio

- Como usuario do Bali-Agent, quero que todo projeto tenha uma equipe base de subagentes, para que o Orchestrator nunca trabalhe sozinho.
- Prioridade: P0

Criterios de Aceitacao:
- [ ] `bali init` cria ou preserva os agentes: `orchestrator`, `discovery`, `prd-writer`, `sdd-architect`, `planner`, `implementer`, `qa`, `security`, `reviewer`, `recruiter`, `memory-curator`, `docs`.
- [ ] `bali verify` falha se os agentes obrigatorios estiverem ausentes.
- [ ] A documentacao deixa claro que esses agentes sao subagentes reais, nao papeis interpretados no mesmo contexto.

### RF-002: Tornar Product Spine obrigatoria

- Como usuario, quero que Discovery, PRD e SDD fiquem acima da execucao, para que features grandes tenham entendimento e arquitetura antes de codigo.
- Prioridade: P0

Criterios de Aceitacao:
- [ ] O protocolo declara que `Discovery -> PRD -> SDD` e obrigatorio para projeto novo.
- [ ] O protocolo declara que feature grande passa por PRD/SDD quando altera produto, dados, arquitetura, integracao, permissoes, billing, IA, deploy ou seguranca.
- [ ] Tarefas pequenas podem seguir fluxo reduzido, mas ainda passam por especialista e Reviewer.

### RF-003: Expandir Discovery para projeto novo e projeto existente

- Como Orchestrator, quero usar o Discovery Agent tanto para entrevista de projeto novo quanto para descoberta de projeto em andamento.
- Prioridade: P0

Criterios de Aceitacao:
- [ ] Discovery entrevista o usuario quando faltam informacoes.
- [ ] Discovery le repo, docs, memoria e working context em projeto existente.
- [ ] Discovery produz um Discovery Brief consumido pelo PRD Writer.

### RF-004: Criar especialistas fixos por projeto

- Como Orchestrator, quero que o Recruiter crie especialistas fixos quando uma competencia recorrente aparece no projeto.
- Prioridade: P0

Criterios de Aceitacao:
- [ ] O Recruiter pode criar `spec-<dominio>.md` em `.agent/team/`.
- [ ] O especialista criado e registrado em `.agent/subagent.config.yaml`.
- [ ] O especialista e espelhado nos adapters nativos ativos.
- [ ] Tarefas futuras dentro do escopo dele sao roteadas para esse especialista.

### RF-005: Criar agentes temporarios para tarefas pontuais

- Como Orchestrator, quero criar subagentes temporarios para investigacoes ou tarefas unicas, para nao poluir o time fixo.
- Prioridade: P1

Criterios de Aceitacao:
- [ ] Agentes temporarios ficam sob `.agent/output/runs/<run-id>/temp-agents/` ou caminho equivalente.
- [ ] Agentes temporarios nao entram no manifesto como time fixo.
- [ ] O resultado do temporario passa por Reviewer antes de ser usado.

### RF-006: Promover temporarios para fixos quando fizer sentido

- Como Recruiter, quero promover um temporario para especialista fixo quando o mesmo dominio aparece repetidamente.
- Prioridade: P1

Criterios de Aceitacao:
- [ ] Existe regra configuravel como `promote_after_reuse_count`.
- [ ] A promocao exige registro no manifesto e Memory Gate.
- [ ] A promocao nao acontece sem escopo claro e nome estavel.

### RF-007: Adicionar model routing opcional

- Como usuario avancado, quero definir preferencias de modelo por agente, para usar modelos diferentes quando o host permitir.
- Prioridade: P1

Criterios de Aceitacao:
- [ ] O manifesto aceita `model_policy` por agente ou classe de agente.
- [ ] Todo agente tem fallback para `host-default`.
- [ ] Se o host nao suportar selecao de modelo por subagente, o setup continua valido.
- [ ] A documentacao deixa claro que multi-modelo nao e requisito para subagentes.

### RF-008: Materializar o time em adapters nativos

- Como usuario, quero que o mesmo time Bali seja materializado em Claude Code, Codex, Antigravity e OpenCode quando possivel.
- Prioridade: P0 para Claude; P1 para demais hosts.

Criterios de Aceitacao:
- [ ] Claude adapter gera `.claude/agents/*.md` para o Core Team e especialistas do projeto.
- [ ] Claude adapter inclui `orchestrator.md`; o stash local atual deve ser corrigido nesse ponto.
- [ ] Codex, OpenCode e Antigravity mantem ou recebem espelhamento equivalente.
- [ ] Bali Runtime permanece fallback quando nao houver subagente nativo.

### RF-009: Tornar memoria automatica parte do ciclo

- Como usuario, quero que o Bali atualize memoria sozinho, para que aprendizado nao dependa de eu pedir.
- Prioridade: P0

Criterios de Aceitacao:
- [ ] Todo subagente pode retornar `memory_suggestions`.
- [ ] O Reviewer aprova ou rejeita a entrega antes de memoria duravel.
- [ ] O Orchestrator chama `memory-curator` ao fim de task, gate, decisao, bug nao obvio, incidente, PR ou commit.
- [ ] `.agent/working-context.md` e atualizado para estado vivo.
- [ ] `.agent/memory.md` recebe apenas aprendizado curado e reutilizavel.
- [ ] Segredos e dados sensiveis continuam bloqueados.

### RF-010: Diferenciar sub-agent de agent-as-tool

- Como mantenedor do Bali, quero separar subagentes de tools agenticas, para evitar arquitetura errada.
- Prioridade: P1

Criterios de Aceitacao:
- [ ] Docs definem subagent como membro delegado do time com autonomia/contexto proprio.
- [ ] Docs definem agent-as-tool como chamada pontual, stateless e encapsulada.
- [ ] O Orchestrator usa subagents para trabalho complexo e tools para funcoes pequenas/reutilizaveis.

---

## 7. Requisitos Nao-Funcionais

| ID | Categoria | Requisito | Metrica |
|---|---|---|---|
| RNF-001 | Compatibilidade | O Bali deve funcionar mesmo quando todos os subagentes usam o mesmo modelo. | `bali verify` passa sem `model_policy` customizada |
| RNF-002 | Portabilidade | O contrato do time deve ser independente do host. | Mesmo manifesto gera adapters diferentes |
| RNF-003 | Seguranca | Memoria nao pode registrar segredos. | Testes existentes de secret scan continuam passando |
| RNF-004 | Idempotencia | Setup nao pode sobrescrever trabalho local sem preservar/mesclar. | Rodar setup duas vezes nao remove especialistas existentes |
| RNF-005 | Observabilidade | Criacao de agente, roteamento, revisao e memoria devem ser auditaveis. | Eventos em output/log ou memoria curada |
| RNF-006 | Escopo | O Orchestrator nao deve criar especialistas fixos demais. | Regra de criacao exige recorrencia ou justificativa explicita |

---

## 8. Metricas de Sucesso

| Metrica | Baseline Atual | Meta | Prazo |
|---|---|---|---|
| Core Team criado por setup | Parcial | 100% dos agentes obrigatorios criados | MVP |
| Claude native agents completos | Parcial no stash | 100% do Core Team + project specialists espelhados | MVP |
| Product Spine preservada | Parcial | Discovery, PRD e SDD exigidos em projeto novo/feature grande | MVP |
| Memory Gate automatico | Parcial/protocolo | Working context e memoria atualizados sem pedido do usuario | v1 |
| Multi-model fallback | Nao formal | Todos agentes aceitam `host-default` | MVP |

---

## 9. Fora de Escopo

- Criar suporte real para todos os provedores/modelos comerciais na primeira iteracao.
- Garantir execucao paralela multi-modelo em todos os hosts.
- Criar UI visual para gerenciar time.
- Substituir ferramentas nativas do host quando elas ja oferecem subagentes.
- Registrar logs completos de terminal ou conversas em memoria.

---

## 10. Riscos e Dependencias

| # | Risco/Dependencia | Tipo | Probabilidade | Impacto | Mitigacao |
|---|---|---|---|---|---|
| R1 | Misturar novamente multi-modelo com subagent-first. | Risco | Media | Alto | Docs e testes devem exigir funcionamento com `host-default`. |
| R2 | Criar especialistas fixos demais e poluir o projeto. | Risco | Media | Medio | Recruiter exige escopo, recorrencia e registro em memoria. |
| R3 | Remover hooks/contexto Claude sem substituto equivalente. | Risco | Media | Alto | Avaliar hooks como mecanismo de reinjecao, nao remover sem teste. |
| R4 | Memory Gate virar log bruto. | Risco | Media | Alto | `memory-curator` e secret scan bloqueiam conteudo inutil/sensivel. |
| D1 | Capacidade nativa de subagentes varia por host. | Dependencia | - | - | Adapter declara capacidades e fallback para Bali Runtime. |
| D2 | Model routing depende do host permitir escolha de modelo por subagente. | Dependencia | - | - | `model_policy` sempre tem fallback `host-default`. |

---

## 11. Criterios de Aceitacao Globais

- [ ] O README descreve Bali como subagent-first, nao multi-model-first.
- [ ] `protocols/subagents.md` diferencia Core Team, project-fixed specialists e temporary agents.
- [ ] `protocols/routing.md` preserva Product Spine e fluxo Reviewer loop.
- [ ] `protocols/memory.md` define Memory Gate automatico.
- [ ] `bali init` cria o Core Team obrigatorio.
- [ ] Claude adapter gera `.claude/agents/orchestrator.md` e demais agentes obrigatorios.
- [ ] `bali verify` valida Core Team, memoria e adapter nativo.
- [ ] Testes cobrem setup, verify, Claude adapter e memoria automatica.
- [ ] A versao local do stash e aproveitada seletivamente, corrigindo ausencia do Orchestrator e testes frouxos.

---

## 12. Cronograma Estimado

| Fase | Escopo | Responsavel |
|---|---|---|
| Fase 1 | Consolidar docs/protocolos e manifesto do time | Orchestrator + PRD/SDD |
| Fase 2 | Implementar Core Team e verify | Implementer + QA |
| Fase 3 | Corrigir Claude adapter e aplicar stash local com ajustes | Claude specialist + Reviewer |
| Fase 4 | Adicionar Recruiter/project specialists/temporarios | Architect + Implementer |
| Fase 5 | Automatizar Memory Gate | Memory Curator + Security + Reviewer |
| Fase 6 | Expandir/validar adapters Codex, OpenCode e Antigravity | Adapter specialists |

---

## 13. Secoes para IA/LLM

### 13.1 Intent Scope

O Bali-Agent coordena subagentes para engenharia de software e gerenciamento de conhecimento de projeto. Ele nao promete que todo host executara varios modelos ao mesmo tempo; promete que o trabalho sera estruturado como subagentes reais quando houver mecanismo nativo ou fallback isolado.

### 13.2 Data Boundary

| Dado | Acessivel pela IA? | Justificativa |
|---|---|---|
| Codigo do projeto | Sim | Necessario para Discovery, SDD, implementacao e revisao |
| PRD/SDD/memoria curada | Sim | Fonte de verdade do projeto |
| Segredos/tokens/chaves | Nao | Bloqueado por politica de seguranca e secret scan |
| Logs completos | Nao por padrao | Usar apenas trechos curados e relevantes |
| Dados pessoais | Somente se necessario e minimizado | Evitar memoria duravel com PII |

### 13.3 Nivel de Automacao

Nivel 3: o Bali pode criar subagentes, atualizar memoria e propor planos automaticamente, mas mudancas grandes de produto/arquitetura devem passar por gates de PRD/SDD e aprovacao do usuario quando necessario.

### 13.4 Model Routing

O manifesto deve permitir classes de modelo, nao depender de nomes comerciais especificos:

```yaml
model_policy:
  default: host-default
  classes:
    cheap-fast:
      fallback: host-default
    balanced:
      fallback: host-default
    strong-coding:
      fallback: host-default
    strong-reasoning:
      fallback: host-default
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

### 13.5 Fallback

Se o host nao suporta subagentes nativos, usar Bali Runtime. Se o host suporta subagentes mas nao suporta modelo por agente, usar o modelo atual do host. Se nenhum mecanismo permite isolamento real, falhar fechado e explicar o requisito ausente.

---

## 14. Pendencias e Decisoes em Aberto

| # | Pendencia | Impacto se Nao Resolvida | Responsavel |
|---|---|---|---|
| P1 | Nome final do agente "Recruiter": Recruiter, Team Builder ou Talent Scout. | Pode afetar docs e prompts. | Usuario |
| P2 | Politica exata para promover temporario a fixo. | Pode criar agentes demais ou de menos. | SDD Architect |
| P3 | Como preservar hooks Claude sem conflitar com `.claude/agents`. | Afeta reinjecao de contexto. | Claude specialist |
| P4 | Formato final do manifesto para `model_policy`. | Afeta adapters e runtime. | SDD Architect |

---

## 15. Historico de Revisoes

| Versao | Data | Alteracoes |
|---|---|---|
| 1.0 | 2026-06-30 | Versao inicial baseada no brainstorm subagent-first, Product Spine, especialistas por projeto e memoria automatica. |
