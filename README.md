# Bali-Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/ba-lison/Bali-Agent/blob/main/LICENSE)
[![CI](https://github.com/ba-lison/Bali-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/ba-lison/Bali-Agent/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.2.0-green.svg)](https://github.com/ba-lison/Bali-Agent/blob/main/CHANGELOG.md)

Bali-Agent e um **orquestrador de subagentes** para trabalho de engenharia de software. Hoje ele entrega time base, contratos, adapters, runtime de orquestracao e artefatos verificaveis; ainda nao e um orquestrador autonomo completo em qualquer host sem depender do suporte real do host.

A ideia e simples: eu entro num projeto com um time base de agentes, uso Discovery/PRD/SDD para entender antes de sair executando, delego a implementacao para especialistas e deixo QA/Seguranca/Reviewer fecharem a entrega.

O foco nao e "usar varios modelos a qualquer custo". O foco e ter separacao real de responsabilidade. Se o host deixar escolher modelo por agente, eu uso `model_policy`. Se nao deixar, todo mundo roda no modelo atual do host e o fluxo continua.

## Ideia Central

```text
Humano
  -> Orchestrator
      -> Discovery / PRD / SDD quando produto ou arquitetura muda
      -> Recruiter quando o projeto precisa de especialista recorrente
      -> Planner para decompor tarefas
      -> Specialists para execucao
      -> QA / Security quando necessario
      -> Reviewer como gate final
      -> Memory Curator para aprendizado do projeto
  -> Humano
```

Na pratica, eu falo com o Orchestrator. Dali, o trabalho e organizado, os agentes certos entram em cena, as saidas sao revisadas e o que ficou incompleto volta para ajuste. Quando o Bali Runtime esta no controle, essa organizacao depende de uma resposta `routing_plan` em JSON valido; se o LLM devolver apenas texto solto, o runtime falha de forma explicita em vez de fingir coordenacao.

## O Que E Um Subagente

Aqui, subagente nao e so "finge que agora voce e QA" no mesmo chat. A intencao e cada agente ter definicao propria, escopo, prompt, fronteira de contexto e um caminho de execucao claro.

Bali usa tres tipos de subagente:

| Tipo | Exemplos | Ciclo de vida |
|---|---|---|
| Core Team | `orchestrator`, `discovery`, `prd-writer`, `sdd-architect`, `reviewer` | Sempre presente em todo projeto |
| Especialistas fixos do projeto | `spec-supabase`, `spec-cloudflare`, `spec-lgpd` | Persistem no projeto e assumem trabalho recorrente |
| Agentes temporarios | `temp-debug-timeout`, `temp-pdf-audit` | Criados para um run e descartados depois |

Agent-as-tool ainda faz sentido para coisa pequena, stateless e bem encapsulada. Para trabalho de projeto, eu prefiro subagente: tem contexto, handoff e revisao.

## Core Team Obrigatorio

Todo projeto inicializado com Bali tem este time em `.agent/team/`:

- `orchestrator`: hub central e unico coordenador voltado ao humano.
- `discovery`: entrevista o usuario e descobre contexto de projeto existente.
- `prd-writer`: transforma discovery em requisitos de produto.
- `sdd-architect`: transforma PRD em arquitetura e design tecnico.
- `planner`: quebra trabalho aprovado em tarefas ordenadas.
- `implementer`: especialista geral de implementacao.
- `qa`: especialista de testes e verificacao.
- `security`: especialista de seguranca e risco de dados.
- `reviewer`: gate obrigatorio de qualidade.
- `recruiter`: cria ou promove especialistas fixos do projeto.
- `memory-curator`: atualiza working context e memoria duravel.
- `docs`: especialista de documentacao e conhecimento.

`spec-implementer` ainda e criado como fallback legado para o caminho atual do Runtime. Mantive isso para nao quebrar compatibilidade enquanto o Core Team novo fica mais firme.

## Product Spine

Antes de implementar mudanca grande, eu passo pela Product Spine:

```text
Discovery -> PRD Writer -> SDD Architect
```

Use a Product Spine para:

- projetos novos;
- features grandes;
- mudancas de comportamento de produto;
- mudancas de arquitetura ou modelo de dados;
- integracoes, auth, permissoes, billing, IA, deploy ou seguranca;
- projetos existentes quando o contexto do repo esta incerto.

Tarefa pequena pode ir por um caminho reduzido. Mudanca grande, produto novo, arquitetura, seguranca, dados ou integracao pede Discovery, PRD e SDD antes da execucao.

## Estado Atual: O Que Ja Roda

Nem tudo no README tem o mesmo nivel de automacao hoje. Esta e a leitura honesta do projeto:

| Area | Estado | Observacao |
|---|---|---|
| `bali init` | Funcional | Instala `.agent/`, Core Team, runtime, protocolos, memoria, hooks e adapters. |
| `verify` / `list-agents` | Funcional | Valida manifesto, time obrigatorio e arquivos principais. |
| `create-agent` | Funcional | Cria especialista fixo `spec-*`, registra no manifesto e espelha para Claude/Codex/OpenCode quando as pastas existem. |
| `remember` | Funcional | Escreve memoria curada e bloqueia padroes obvios de segredo. |
| `bali run --dry-run` | Funcional via CLI e `.agent/runtime/bali_runtime.py` | Gera cadeia e artefatos sem chamar LLM. |
| Runtime de subagentes | Funcional com runner de subagente configurado | Executa cada agente como etapa isolada, com prompts, outputs, artefatos e revisao separados. |
| Product Spine `greenfield` | Funcional com artefatos de run | Roda pelo `routing_plan` do Orchestrator e persiste `artifacts/discovery.md`, `artifacts/prd.md`, `artifacts/sdd.md` e `artifacts/tasks.md` quando esses agentes executam. |
| Routing dinamico do Orchestrator | Parcial | O runtime ja entende routing plan JSON, cria especialistas temporarios/permanentes e faz retry com Reviewer, mas depende do Orchestrator/LLM devolver o contrato certo. |
| Multi-modelo por agente | Parcial/depende do host | `model_policy` existe no manifesto; aplicar modelo diferente por agente depende do adapter/host suportar isso. |
| Subagentes nativos por host | Depende do host | Bali materializa arquivos para Claude, Codex e OpenCode, mas quem executa isolamento nativo e a ferramenta. Se nao houver isolamento nativo, use Bali Runtime. |
| Memoria automatica no fim de task aprovada | Funcional no Bali Runtime | Depois de um run aprovado, o runtime chama `memory-curator`, grava `artifacts/memory-summary.md` e registra entrada em `.agent/memory.md`. Em hosts nativos, ainda depende do adapter/host seguir o protocolo. |
| `inspect-runs` | Funcional para o runtime atual | Le `.agent/output/runtime/*/run_manifest.json` e ainda aceita manifests legados em `.agent/runs`. |
| `capability-report` | Funcional | Mostra o que esta entregue, o que depende de contrato com LLM, o que depende do host e o que ainda nao foi entregue. |

## Compatibilidade Real

O que esta compativel hoje:

- CLI principal (`bali --root ...`) para `init`, `verify`, `list-agents`, `create-agent`, `remember`, `run`, `run --dry-run` e `inspect-runs`.
- Auditoria local com `capability-report`, para separar capacidade entregue de dependencia externa.
- Bali Runtime instalado em `.agent/runtime/bali_runtime.py`, com `--root` explicito, manifests em `.agent/output/runtime/*/run_manifest.json` e artefatos por agente.
- Product Spine em modo `greenfield` quando o Orchestrator devolve `routing_plan` valido.
- Memoria automatica ao fim de runs aprovados pelo Bali Runtime.
- Adapters que materializam arquivos para hosts como Claude Code, Codex e OpenCode.

O que nao e promessa fechada ainda:

- Paralelismo real entre agentes: o runtime aceita apenas `execution_mode: sequential` e `max_parallel: 1`.
- Isolamento nativo garantido em todo host: Bali cria os arquivos/adapters, mas a execucao nativa depende da ferramenta.
- Multi-modelo obrigatorio: `model_policy` e declarativo; so vira troca real de modelo quando o host ou wrapper suportar.
- Orquestracao sem contrato: se o Orchestrator/LLM nao devolver JSON valido, o runtime para em erro em vez de fingir sucesso.

## Fluxo de Vida

### Projeto Novo

```text
1. Instalar Bali no repo alvo.
2. Discovery entrevista o usuario.
3. PRD Writer cria os requisitos de produto.
4. SDD Architect cria o design tecnico.
5. Recruiter cria especialistas fixos para dominios recorrentes.
6. Planner quebra o trabalho em tarefas executaveis.
7. Especialistas implementam.
8. QA e Security validam quando relevante.
9. Reviewer aprova ou rejeita.
10. Memory Curator atualiza a memoria do projeto quando o run e aprovado.
```

### Projeto Existente

```text
1. Primeiro eu preservo regras e governanca ja existentes no repo.
2. Discovery le contexto do repo, docs, working context e memoria.
3. Orchestrator classifica o pedido.
4. Product Spine roda se o pedido muda produto ou arquitetura.
5. Especialistas existentes assumem escopos correspondentes.
6. Recruiter cria especialista fixo apenas quando a necessidade e recorrente.
7. Agentes temporarios cuidam de investigacoes pontuais.
8. Reviewer faz o gate da entrega.
9. Memory Curator registra o que deve sobreviver para sessoes futuras quando o run e aprovado.
```

## Hosts E Adapters

Bali mantem um time de projeto e materializa esse time para cada host.

| Host | Caminho nativo | Observacoes |
|---|---|---|
| Claude Code | `.claude/agents/*.md` | Usa subagentes nativos quando a superficie tem Agent/Task tooling. Hooks continuam uteis para reinjecao de contexto. |
| Codex | `.codex/agents/*.toml` | Usa custom agents do projeto quando disponivel. |
| OpenCode | `.opencode/agents/*.md` | Usa `mode: subagent`. |
| Antigravity | `.antigravity/skills/` ou `.agents/skills/` | Usa `define_subagent` e background subagents com fila segura. |
| Cursor | Cursor rules + Bali Runtime | Rules dao contexto; Runtime da isolamento quando nao houver subagente nativo. |
| Hosts sem subagente nativo | Bali Runtime ou falha fechada | Use o Runtime apenas para preservar isolamento de subagentes. API sem mecanismo de subagente/modelo local sozinho nao e host Bali suficiente. |

Para escolher o caminho, eu olho menos para "desktop ou API?" e mais para isto: o host consegue rodar subagente isolado ou tool-calling de verdade? Se sim, vale usar o adapter nativo. Se nao, entra o Bali Runtime. Se nenhum caminho real existir, melhor parar do que fingir isolamento.

## Model Policy

Roteamento multi-modelo e opcional. Um projeto pode declarar preferencias por classe de agente:

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

Se o host suporta selecao de modelo por agente, o adapter pode usar isso. Se nao suporta, todos usam o modelo atual do host.

## Instalacao

Requisitos:

- Python 3.11+
- `pyyaml`

Instale localmente:

```bash
git clone https://github.com/ba-lison/Bali-Agent.git
cd Bali-Agent
pip install -e .
```

Inicialize um projeto alvo:

```bash
bali --root /caminho/do/projeto init
```

Verifique a instalacao:

```bash
bali --root /caminho/do/projeto verify
```

## CLI

```bash
bali --root /caminho/do/projeto <comando>
```

| Comando | Funcao |
|---|---|
| `init` | Instala `.agent/`, runtime, templates, protocolos, time, memoria e adapters. |
| `verify` | Valida time obrigatorio, manifesto, runtime, memoria e contrato de adapters. |
| `verify-adapter <nome>` | Verifica um adapter como `claude-code`, `codex` ou `antigravity`. |
| `list-agents` | Lista agentes registrados em `.agent/team/`. |
| `create-agent --id spec-name --scope "..."` | Cria especialista fixo do projeto. |
| `run "tarefa"` | Executa o fluxo do Orchestrator. |
| `run --workflow greenfield "tarefa"` | Executa o fluxo greenfield com Product Spine. |
| `remember` | Adiciona entrada curada de memoria. |
| `inspect-runs` | Mostra runs do Bali Runtime em `.agent/output/runtime` e runs legados em `.agent/runs`. |
| `capability-report` | Mostra uma matriz de maturidade: Delivered, Contract-dependent, Host-dependent e Not delivered. |

Exemplos:

```bash
bali --root . verify
bali --root . capability-report
bali --root . create-agent --id spec-supabase --scope "Supabase auth, RLS, storage, migrations"
bali --root . run "corrigir bug de redirect no login"
bali --root . remember --kind decision --title "Usar Supabase RLS" --summary "Dados de auth ficam protegidos por politica no banco"
```

## Variaveis De Ambiente

| Variavel | Funcao |
|---|---|
| `BALI_SUBAGENT_RUNNER` | Runner local usado pelo Bali Runtime para executar uma etapa de subagente com `{prompt_file}`, `{output_file}` e `{agent}`. Nao substitui adapter nativo quando ele existe. |
| `BALI_SUBAGENT_DEPTH` | Profundidade interna de subagentes spawnados. O maximo esperado e 2. |

## O Que `bali init` Instala

```text
.agent/
  subagent.config.yaml       # manifesto do time, product spine, model policy
  working-context.md         # estado vivo do projeto
  memory.md                  # memoria duravel curada
  task.md                    # checklist da tarefa atual
  run.py                     # bootstrapper que delega para o runtime
  verify_setup.py            # verificador de setup
  .gitignore                 # ignora outputs de runtime e segredos
  hooks/
    prevent_secrets.py
  runtime/
    bali_runtime.py
  team/
    orchestrator.md
    discovery.md
    prd-writer.md
    sdd-architect.md
    planner.md
    implementer.md
    qa.md
    security.md
    reviewer.md
    recruiter.md
    memory-curator.md
    docs.md
    spec-implementer.md
  protocols/
    subagents.md
    routing.md
    memory.md
    handoff.md
    quality-gates.md
    approval-gates.md
  agents/
  templates/
  skills/
    AUDIT.md
```

Adapters tambem podem criar pastas especificas do host:

```text
.claude/agents/*.md
.codex/agents/*.toml
.opencode/agents/*.md
.antigravity/skills/
.agents/skills/
.cursor/rules/bali-agent.mdc
```

## Formato Do Manifesto

O manifesto e a fonte de verdade do time:

```yaml
runtime_authority: "bali-runtime"
subagents_policy:
  role_play_permitido: false
  fallback_obrigatorio: "adapter-nativo-ou-bali-runtime"

time:
  core:
    - orchestrator
    - discovery
    - prd-writer
    - sdd-architect
    - planner
    - implementer
    - qa
    - security
    - reviewer
    - recruiter
    - memory-curator
    - docs
  product_spine:
    - discovery
    - prd-writer
    - sdd-architect
  project_fixed: []
  temporary_policy:
    max_per_task: 3
    promote_after_reuse_count: 3

model_policy:
  default: host-default
```

## Memoria

Bali separa estado vivo de aprendizado duravel.

| Arquivo | Significado |
|---|---|
| `.agent/working-context.md` | Status atual, handoff ativo, progresso recente, riscos e proxima acao. Nao e log historico. |
| `.agent/memory.md` | Decisoes curadas, incidentes, aprendizados reutilizaveis e convencoes do projeto. |
| `.agent/memory.db` | Indice SQLite FTS5 usado por busca de memoria. Ignorado pelo git. |

No ciclo ideal, memoria entra no fim de tasks, gates, decisoes, incidentes, PRs ou commits relevantes. Hoje a base disso ja existe com `remember`, `memory-curator`, templates e protocolos; a automacao total depende do fluxo/runtime usado.

O Memory Curator:

- atualiza `working-context.md` com estado vivo;
- escreve em `memory.md` apenas quando existe aprendizado reutilizavel;
- rejeita logs brutos;
- bloqueia segredos, tokens, chaves e dados pessoais desnecessarios.

## Seguranca

Mantive o modelo de seguranca anterior e trouxe ele para dentro do contrato do Runtime.

### Seguranca De Arquivos

- Paths sao normalizados antes de acesso.
- Traversal e ataques de prefixo de diretorio irmao sao bloqueados com checagens de path seguro.
- Caminhos sensiveis como `.env`, `.git` e pastas de segredo sao bloqueados.

### Seguranca De Comandos

Comandos sao classificados e executados sem composicao de string em shell. A politica considera subcomandos:

| Executavel | Exemplos permitidos | Exemplos bloqueados |
|---|---|---|
| `pytest` | execucoes diretas de teste | nenhum por padrao |
| `npm` | `test`, `run` | `install`, `ci`, `publish`, `exec` |
| `cargo` | `test`, `check`, `build` | `run`, `install` |
| `go` | `test`, `build`, `vet`, `fmt` | `run`, `install`, `get` |
| `git` | `status`, `diff`, `log`, `show` | `push`, `commit`, `reset`, `checkout` |
| `pip` | nenhum | tudo por padrao |

Operadores de encadeamento como `;`, `&&`, pipes e command substitution sao bloqueados na execucao de tools do Runtime.

### Tool Registry

Tools sao default-deny:

- `allowed_tools: []` significa nenhuma tool.
- `allowed_tools: ["read_file", "search_memory"]` significa apenas essas tools.
- `allowed_tools: ["*"]` e opt-in explicito para todas as tools registradas.

### Reviewer Fail-Closed

O Reviewer trabalha com JSON estruturado valido. Se a saida vier malformada, sem campos obrigatorios, aprovada com blockers ou pulando checks obrigatorios, o Runtime falha fechado em vez de aprovar silenciosamente.

### Protecao De Segredos

- `prevent_secrets.py` e instalado em `.agent/hooks/`.
- Escritas de memoria rejeitam padroes obvios de segredo.
- Outputs de runtime e bancos de memoria sao ignorados por `.agent/.gitignore`.

## Runtime E Observabilidade

Uso o Bali Runtime como fallback quando subagentes nativos nao estao disponiveis.

O runtime registra artefatos de run em `.agent/output/` ou pastas especificas, incluindo prompts, outputs, traces, eventos de falha, handoffs e dry-run output.

A superficie Runtime/CLI suporta:

- `verify`
- `list-agents`
- `create-agent`
- `run`
- `remember`
- `capability-report` pela CLI principal, para auditar maturidade operacional sem chamar LLM

Quando provider mode e usado, a execucao passa por `.agent/templates/run.py` para evitar loops recursivos de bootstrap.

## Testes

Rode a suite completa:

```bash
python -m pytest -q
```

Compile os modulos Python principais:

```bash
python -m py_compile bali_agent/cli.py bali_agent/adapters/claude.py bali_agent/core/agent_manager.py
```

Suites importantes:

| Suite | Cobre |
|---|---|
| `tests/test_cli.py` | `bali init`, delegacao para Runtime e criacao do manifesto. |
| `tests/test_claude_adapter.py` | Materializacao nativa de `.claude/agents`. |
| `tests/test_agent_manager.py` | Validacao de time, criacao de especialista e politicas do manifesto. |
| `tests/test_runtime_orchestration.py` | Routing plans dinamicos, retries, especialistas temporarios/permanentes. |
| `tests/test_runner_security.py` | Permissoes de tools, politica de comandos e Reviewer fail-closed. |
| `tests/test_memory.py` | Memoria curada e bloqueio de segredos. |
| `tests/test_security.py` | Seguranca de path e sanitizacao de comandos. |

## Direcao Atual Do Produto

Bali agora esta organizado por esta hierarquia:

```text
Product Spine:
  Discovery -> PRD -> SDD

Team Spine:
  Recruiter -> Core Team + Project Specialists

Execution Spine:
  Planner -> Specialists -> QA/Security -> Reviewer

Learning Spine:
  Memory Curator -> working-context.md + memory.md
```

Essa mudanca de foco nao joga fora o que ja existia. Seguranca, memoria, runtime, adapters e revisao continuam no projeto; a diferenca e que agora tudo gira em torno de um time persistente de subagentes por projeto.

## Licenca

MIT. Copyright (c) 2025-2026 Alison Cruz.
