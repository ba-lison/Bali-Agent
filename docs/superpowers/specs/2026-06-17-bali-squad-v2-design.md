---
titulo: "Bali-Squad v2 — Setup único por projeto + time híbrido obrigatório"
data: 2026-06-17
status: aprovado-para-plano
autor: brainstorming colaborativo
---

# Bali-Squad v2 — Design

## 1. Contexto e Problema

O Bali-Squad AI hoje é um **pipeline linear de SDLC para projetos novos**: um time **fixo de 7 agentes**
(Orchestrator → Discovery → PRD Writer → SDD Architect → Task Decomposer → Implementer → Reviewer)
que roda em sequência, com gates de aprovação humana. O Orchestrator detecta a fase atual checando
artefatos em `output/{projeto}/`.

Isso resolve bem "começar um projeto do zero", mas **não cobre** o que precisamos agora:

1. **Setup único por projeto** — disparar uma vez, ler um projeto (novo *ou já em andamento*),
   entrevistar o usuário e **montar um time sob medida** para aquele projeto.
2. **Time híbrido** — uma espinha fixa + especialistas **derivados da stack real** do projeto
   (ex.: Next.js+Supabase ganha agentes diferentes de um plugin AutoCAD em C#).
3. **Constituição obrigatória** — depois do setup, **toda** tarefa (bug, feature, dúvida, refactor)
   roteia pelo time. Nunca mais um agente trabalhando sozinho. Isso vira o modo de operação
   permanente do projeto.

A filosofia existente (gates, handoff, "nunca solo", LLM-agnostic) é reaproveitada. **Estendemos,
não reescrevemos.**

## 2. Decisões já tomadas (do brainstorming)

| # | Decisão | Escolha |
|---|---------|---------|
| 1 | Formato de uso | Setup **único** por projeto; depois vira padrão automático |
| 2 | Composição do time | **Híbrido**: espinha fixa + especialistas dinâmicos por stack |
| 3 | Alvo / portabilidade | **Universal** (qualquer LLM). Reforço Claude Code via hook = **toggle opcional** |
| 4 | Caminho | **Evoluir** o repo Bali-Squad-AI existente (Abordagem A) |

## 3. Conceito central — dois modos unificados

O Orchestrator passa a operar em **dois modos**, decididos no setup:

| Modo | Quando | O que roda |
|------|--------|-----------|
| **Greenfield** | Setup detecta projeto vazio / do zero | Pipeline SDLC atual (Discovery→PRD→SDD→Tasks→Impl→Review) — **mantido** |
| **Operate** | Setup detecta código existente | Roteamento contínuo: qualquer pedido → especialista(s) → Reviewer |

Adiciona-se um agente de **meta-nível**: o **Setup Agent** (bootstrap), que roda **uma vez** por
projeto e *gera* o time. Greenfield e Operate convivem na mesma base.

## 4. O Setup único (bootstrap)

Disparo: `python init.py` copia a base para o projeto; o usuário então manda `Setup do time` no chat
do assistente. O **Setup Agent**:

1. **Perfila o projeto** (somente leitura, não altera nada). Detecta stack por arquivos-sinal:
   - `package.json` + deps (Next/React/Vue/Express), `*.csproj`/`*.sln` (C#/.NET → plugins AutoCAD),
     `pyproject.toml`/`requirements.txt`, `composer.json` (WordPress/Woo), `supabase/`,
     `wrangler.toml` (Cloudflare/WASM), `Dockerfile`, schema SQL, `.github/workflows`, etc.
   - Detecta o domínio quando possível (IFC/WASM, WooCommerce, AutoCAD/.NET, dashboards Next+Supabase).
2. **Entrevista adaptativa curta** — pula o que já detectou. Pergunta: objetivo atual, restrições,
   **o que NÃO mexer**, convenções de código, e quais especialistas fazem sentido.
3. **Monta o time híbrido** (seção 5).
4. **Gera os artefatos no projeto:** `AGENTS.md` (constituição) + `.agent/squad.config.yaml`
   (manifesto) + `.agent/team/*.md`.
5. **Gate de aprovação:** apresenta o time proposto; o usuário aprova ou ajusta.
6. **Idempotente:** ao rodar de novo, detecta o manifesto e oferece **"atualizar time"** quando a
   stack mudou (ex.: passou a usar Supabase).

## 5. Time híbrido + Constituição

### 5.1 Espinha fixa (SEMPRE gerada, em todo projeto)

- 🎯 **Orchestrator** — roteia *qualquer* tarefa (evoluído: não só SDLC de projeto novo).
- 📋 **Planner** — decompõe qualquer pedido em plano/tasks (absorve o antigo Task Decomposer).
- 🔎 **Reviewer** — gate de qualidade + segurança (mantido do Bali atual).

### 5.2 Especialistas dinâmicos (gerados pela stack)

Exemplos: `spec-nextjs.md`, `spec-supabase.md` (com o schema real embutido), `spec-autocad-csharp.md`,
`spec-wordpress.md`, `spec-wasm-ifc.md`. Cada um é instanciado de um **arquétipo** em
`agents/_specialists/` preenchido com o contexto concreto do projeto.

### 5.3 A Constituição (vai para o `AGENTS.md` da raiz do projeto)

Texto universal que qualquer LLM segue, em essência:

> **Modo de operação permanente deste projeto.** Para QUALQUER pedido — bug, feature, dúvida,
> refactor — você assume o papel de **Orchestrator**, lê `.agent/squad.config.yaml` e roteia a tarefa
> para os especialistas em `.agent/team/`. Você **nunca trabalha sozinho**. Toda entrega passa pelo
> **Reviewer** antes de concluir. Isso não é opcional.

### 5.4 Anti-burocracia (processo proporcional)

A constituição obriga a rotear *sempre*, mas com **esforço proporcional ao pedido**:

- Pergunta trivial → especialista responde direto + Reviewer dá um sanity-check rápido.
- Feature → Planner faz o plano → especialista implementa → Reviewer revisa.

Isso evita que "sempre o time" vire lentidão para coisa pequena.

### 5.5 Reforço por ferramenta (enforcement adapters)

**Problema que isto resolve:** `AGENTS.md`/`CLAUDE.md` são instrução **passiva** — lidas no início da
sessão. Em sessão longa, quando o contexto enche, o assistente **resume/compacta** o histórico e a
constituição pode "diluir", fazendo o modelo voltar a trabalhar sozinho. A blindagem é re-injetar a
regra a cada turno, via mecanismo que o **harness executa** (não depende da vontade do modelo).

**Distinção crítica — modelo ≠ ferramenta:** o reforço é por **harness/ferramenta**, não por
**modelo**. Modelos (Claude, Gemini, DeepSeek, Gemma3/4, Kimi, Llama…) são **todos cobertos de graça**
pelo `AGENTS.md` universal — qualquer modelo que receba o arquivo segue a constituição. Runtimes de
modelo (ex.: Ollama) também não enforçam nada sozinhos; quem lê e re-injeta é o front-end por cima
deles. Portanto **não há adaptador por modelo** — só por ferramenta.

O setup gera o **adaptador mais forte que cada ferramenta-alvo suporta**. Escopo decidido:

| Ferramenta | No escopo? | Adaptador gerado | Força |
|-----------|-----------|------------------|-------|
| **Claude Code** | ✅ PADRÃO | hook `UserPromptSubmit` + `SessionStart` no `.claude/settings.json` re-injetando a constituição a cada turno; espelha o time em `.claude/agents/*.md` | **Forte** (re-injeção por turno, garantida pelo harness) |
| **Cursor** | ✅ | `.cursor/rules/squad.mdc` com `alwaysApply: true` | Médio-forte (regra "always" re-aplicada) |
| **Gemini CLI** | ✅ | `.gemini/settings.json` apontando para `AGENTS.md` como context file | Médio (recarrega por sessão; janela grande ajuda) |
| **Codex CLI** | ✅ | `AGENTS.md` na raiz (já é a camada de instrução nativa) | Médio |
| Windsurf, outros | ⛔ fora do escopo v2 | (só `AGENTS.md` universal) | Instrução forte (passiva) |
| Qualquer modelo (DeepSeek/Gemma/Kimi/…) | n/a | coberto pelo `AGENTS.md` universal | Instrução forte (passiva) |

**Decisão:** Claude Code é instalado **por padrão**; Cursor, Gemini CLI e Codex CLI também entram no
escopo v2. Demais ferramentas ficam fora (YAGNI) — quando necessário, adicionar novo adaptador é
barato. Modelos são sempre cobertos pelo núcleo universal.

> ⚠️ Nota de precisão: as capacidades de hook/config dessas CLIs evoluem rápido (conhecimento até
> jan/2026). Antes de implementar um adaptador específico, validar a sintaxe atual da ferramenta-alvo.

## 6. Estrutura de arquivos

### 6.1 No repo da base (Bali-Squad-AI)

```
Bali-Squad-AI/
├── AGENTS.md                    [REVISADO] ponto de entrada da BASE: explica o sistema e dispara o Setup Agent
├── agents/
│   ├── _setup/
│   │   ├── AGENT.md             [NOVO] bootstrap: perfila + entrevista + gera o time
│   │   ├── stack-detection.md   [NOVO] heurísticas de detecção de stack
│   │   └── interview.md         [NOVO] roteiro adaptativo do setup
│   ├── _spine/                  [NOVO] espinha fixa
│   │   ├── orchestrator/AGENT.md
│   │   ├── planner/AGENT.md
│   │   └── reviewer/AGENT.md
│   ├── _specialists/            [NOVO] arquétipos de especialista
│   │   ├── _TEMPLATE.md         [NOVO] molde para gerar especialista sob medida
│   │   ├── frontend.md  backend.md  database.md  devops.md
│   │   └── security.md  testing.md  docs.md
│   ├── discovery/               [MANTIDO] modo greenfield
│   ├── prd-writer/              [MANTIDO]
│   └── sdd-architect/           [MANTIDO]
├── templates/
│   ├── squad.config.yaml        [NOVO] manifesto do time montado por projeto
│   ├── project-AGENTS.md        [NOVO] template da constituição que vai p/ a raiz do projeto
│   ├── prd.md  sdd.md  tasks.md [MANTIDOS]
├── protocols/
│   ├── routing.md               [NOVO] como o Orchestrator roteia QUALQUER tarefa
│   ├── handoff.md               [MANTIDO]
│   ├── approval-gates.md        [MANTIDO]
│   └── quality-gates.md         [MANTIDO]
├── examples/                    [MANTIDO] + novos exemplos de squad.config
└── init.py                      [EVOLUÍDO] instala a base em .agent/ e dispara o Setup Agent
```

Observação: os antigos `agents/task-decomposer/` e `agents/implementer/` são reposicionados — o
Task Decomposer vira o **Planner** na espinha; o Implementer vira um arquétipo de especialista
genérico (`_specialists/`), já que a implementação real fica a cargo do especialista de stack.

### 6.2 No projeto do usuário (depois do setup)

```
<projeto>/
├── AGENTS.md                    # constituição gerada (raiz, lida por qualquer LLM)
└── .agent/
    ├── squad.config.yaml        # stack detectada + time montado + versão da base
    ├── team/                    # agentes DESTE projeto
    │   ├── orchestrator.md
    │   ├── planner.md
    │   ├── reviewer.md
    │   ├── spec-<stack>.md       # especialistas sob medida
    │   └── ...
    ├── protocols/               # copiados da base
    └── output/                  # planos/reviews por tarefa
```

## 7. O manifesto `squad.config.yaml`

Fonte de verdade do time montado. Estrutura proposta:

```yaml
versao_base: "2.0.0"
projeto: nome-do-projeto
modo: operate | greenfield
criado_em: "2026-06-17T10:00:00-03:00"
stack_detectada:
  - linguagem: typescript
    framework: next.js
    sinais: ["package.json", "next.config.js"]
  - servico: supabase
    sinais: ["supabase/config.toml"]
nao_mexer:
  - "migrations legadas em db/legacy/"
time:
  espinha:
    - orchestrator
    - planner
    - reviewer
  especialistas:
    - id: spec-nextjs
      arquivo: .agent/team/spec-nextjs.md
      escopo: "app router, RSC, rotas"
    - id: spec-supabase
      arquivo: .agent/team/spec-supabase.md
      escopo: "schema, RLS, edge functions"
enforcement_adapters:   # adaptadores de reforço instalados (ver seção 5.5)
  - claude-code          # PADRÃO: re-injeta a constituição a cada turno via hook
```

## 8. Fora de escopo (YAGNI)

- Skill/slash-command nativo do Claude Code como invólucro (`/montar-time`) — pode entrar depois como
  casquinha fina sobre esta base; **não** nesta entrega.
- Métricas/telemetria de uso do time.
- Sincronização automática do time quando arquivos da stack mudam (a atualização é manual via re-run
  do setup).
- Suporte a múltiplos repositórios/monorepo com times distintos por subpasta (futuro).

## 9. Critérios de sucesso

1. Rodar o setup em um **projeto existente** gera `AGENTS.md` + `.agent/` com espinha + ao menos um
   especialista coerente com a stack detectada.
2. Rodar o setup em um **projeto vazio** entra no modo greenfield (pipeline SDLC atual preservado).
3. Após o setup, abrir o projeto em qualquer LLM e fazer um pedido qualquer faz o assistente operar
   como Orchestrator e rotear pelo time (verificável pela resposta seguir o protocolo de routing).
4. O setup é **idempotente**: rodar de novo não duplica, oferece atualizar.
5. Por padrão (Claude Code), os subagentes aparecem em `.claude/agents/` e o hook re-injeta a
   constituição a cada turno; adaptadores de Cursor/Gemini CLI/Codex são gerados conforme declarado.
6. Nada do fluxo greenfield atual quebra (regressão zero nos artefatos PRD/SDD/tasks).

## 10. Riscos e mitigações

| Risco | Mitigação |
|-------|-----------|
| Detecção de stack incompleta/errada | Entrevista confirma e permite correção antes de gerar o time |
| "Sempre o time" vira lento demais | Regra de processo proporcional (5.4) |
| Reorg de `agents/` quebra referências no AGENTS.md | Plano de implementação atualiza todas as tabelas/links |
| Hook do Claude Code mal configurado | Toggle opcional e desligado por padrão; documentado e testável isolado |
