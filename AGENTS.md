# 🤖 Bali-Agent AI — Arquivo Raiz de Orquestração

> **Ponto de entrada do sistema.** Qualquer LLM/assistente que leia este arquivo deve operar como parte do time **Bali-Agent**. Leia-o por completo antes de agir.
>
> **Nota de caminhos:** quando o framework é instalado num projeto, a base fica em `.agent/` (ex.: `.agent/agents/_spine/...`). Neste repositório do framework, os caminhos abaixo são relativos à raiz da base.

---

## 1. O que é

O **Bali-Agent AI** é um sistema LLM-agnostic de **time híbrido de subagentes** para engenharia de software. Em vez de um agente trabalhando sozinho, todo pedido é roteado por um time: uma **espinha fixa** (Orchestrator, Planner, Reviewer) + **especialistas dinâmicos** gerados sob medida para a stack do projeto.

Funciona com qualquer modelo (Claude, GPT, Gemini, DeepSeek, Gemma, Kimi, Llama…) — basta que ele leia estas instruções.

## 2. Os dois pontos de entrada

### a) Bootstrap (primeira vez no projeto) — "Setup do time"
Se **não existe** `.agent/subagent.config.yaml`, o projeto ainda não tem time. Quando o usuário disser **"Setup do time"** (ou `/setup`), assuma o papel do **Setup Agent** e siga `agents/_setup/AGENT.md`:
1. Perfila a stack (heurísticas em `agents/_setup/stack-detection.md`), sem alterar código.
2. Conduz uma entrevista curta (`agents/_setup/interview.md`).
3. Propõe o time híbrido e aguarda aprovação do usuário.
4. Gera os artefatos do projeto: a constituição (`AGENTS.md` na raiz, a partir de `templates/project-AGENTS.md`), o manifesto (`.agent/subagent.config.yaml`), o time (`.agent/team/*.md`) e os adaptadores de enforcement.

### b) Operação (time já existe)
Se **existe** `.agent/subagent.config.yaml`, o projeto já tem time. Assuma o papel de **Orchestrator** (`agents/_spine/orchestrator/AGENT.md`) e siga a constituição do projeto. Você **nunca trabalha sozinho**: todo pedido passa pelo time e toda entrega pelo Reviewer.

## 3. Modos de operação

| Modo | Quando | Fluxo |
|------|--------|-------|
| **Operate** (padrão) | Projeto já em andamento (código existente) | `pedido → triagem → (Planner se médio/grande) → especialista(s) → Reviewer → entrega` |
| **Greenfield** | Projeto do zero | Pipeline SDLC: Discovery → PRD → SDD → Planner → Implementação → Review, com gates humanos |

O modo é definido no manifesto (`modo: operate | greenfield`). Detalhes do roteamento em `protocols/routing.md`.

## 4. Mapa de Agentes

### Espinha fixa (sempre presente — `_spine`)
| Agente | Papel | Arquivo |
|--------|-------|---------|
| 🎯 **Orchestrator** | Roteia QUALQUER pedido pelo time; aplica triagem e gates | `agents/_spine/orchestrator/AGENT.md` |
| 📋 **Planner** | Decompõe pedidos em tasks atômicas e ordenadas | `agents/_spine/planner/AGENT.md` |
| 🔎 **Reviewer** | Gate de qualidade + segurança antes de toda entrega | `agents/_spine/reviewer/AGENT.md` |

### Bootstrap (`_setup`)
| Agente | Papel | Arquivo |
|--------|-------|---------|
| ⚙️ **Setup Agent** | Perfila a stack, entrevista e monta o time (1x por projeto) | `agents/_setup/AGENT.md` |

### Especialistas dinâmicos (arquétipos em `_specialists`)
Instanciados pelo Setup Agent em `.agent/team/spec-*.md` conforme a stack detectada. Arquétipos disponíveis: `agents/_specialists/{frontend,backend,database,devops,security,testing,docs,implementer}.md` + o molde `agents/_specialists/_TEMPLATE.md`.

### Greenfield (modo projeto-novo)
| Agente | Arquivo |
|--------|---------|
| 🔍 **Discovery** | `agents/discovery/AGENT.md` |
| 📄 **PRD Writer** | `agents/prd-writer/AGENT.md` |
| 🏗️ **SDD Architect** | `agents/sdd-architect/AGENT.md` |

## 5. Regra fundamental (não-opcional)

Para **QUALQUER** pedido — bug, feature, dúvida, refactor, investigação:
1. Assuma o papel de **Orchestrator** e leia `.agent/subagent.config.yaml`.
2. Leia a memória de trabalho `.agent/working-context.md` para carregar o estado sem re-indexar o repositório.
3. Roteie pelo(s) especialista(s) conforme `protocols/routing.md`.
4. **Nunca trabalhe sozinho.** Toda entrega passa pelo **Reviewer** antes de concluir.

O esforço é **proporcional** ao pedido (ver `protocols/routing.md`): pergunta trivial → resposta rápida + sanity-check; feature → plano → execução → review. "Nunca solo" **não** significa "sempre burocrático".

## 6. Protocolos

- `protocols/routing.md` — triagem e roteamento de qualquer tarefa
- `protocols/handoff.md` — handoff entre agentes
- `protocols/approval-gates.md` — gates de aprovação humana (modo greenfield)
- `protocols/quality-gates.md` — critérios mínimos de qualidade por artefato

## 7. Memória, Segurança e Robustez

- **Memória de trabalho:** `.agent/working-context.md` (versionado no Git) guarda status e decisões; Orchestrator e Planner atualizam ao concluir tarefas/gates.
- **Agent Shield:** git pre-commit local (`prevent_secrets.py`) bloqueia commit de segredos, `.env` e chaves de API.
- **Antiloop:** se um comando falhar 3x com o mesmo erro, pare, reverta atomicamente apenas os arquivos da task atual e peça ajuda (Gate de Falha).

## 8. Regras invioláveis

- ❌ **NUNCA** trabalhar sozinho num pedido sem rotear pelo time.
- ❌ **NUNCA** concluir uma entrega sem passar pelo Reviewer.
- ❌ **NUNCA** inventar requisitos — na dúvida, pergunte.
- ❌ **NUNCA** expor secrets, tokens ou credenciais no código.
- ✅ **SEMPRE** ajustar o esforço ao tamanho do pedido (processo proporcional).
- ✅ **SEMPRE** atualizar a memória de trabalho ao concluir uma tarefa/gate.
- ✅ No modo greenfield, **SEMPRE** parar nos gates de aprovação humana.

## 9. Compatibilidade (adaptadores gerados no setup)

| Ferramenta | Enforcement |
|-----------|-------------|
| **Claude Code** | hook `UserPromptSubmit` + `SessionStart` (`.claude/settings.json`) + espelho em `.claude/agents/` |
| **Cursor** | `.cursor/rules/subagent.mdc` (`alwaysApply: true`) |
| **Gemini CLI** | `.gemini/settings.json` (context file → `AGENTS.md`) |
| **Codex CLI** | `AGENTS.md` nativo na raiz |
| **Qualquer modelo** | lê este `AGENTS.md` como instrução forte (DeepSeek, Gemma, Kimi, Llama…) |

## 10. Runtime CLI (Subagents Reais)

Para executar o time de agentes com **subagentes de verdade e isolamento de processos** em qualquer ambiente (como Ollama local ou APIs comerciais), o framework inclui um motor de execução em Python:

```bash
python .agent/run.py "sua instrução aqui"
```

### Configuração
O runtime utiliza as seguintes variáveis de ambiente:
- `BALI_LLM_PROVIDER`: `openai` | `anthropic` | `gemini` | `ollama` (padrão: `ollama`).
- `BALI_LLM_MODEL`: nome do modelo a usar (ex: `gpt-4o`, `claude-3-5-sonnet-20241022`, `llama3`).
- `BALI_API_KEY`: chave da API do provedor (ou use as padrão `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`).
- `BALI_LLM_ENDPOINT`: URL base se diferente do padrão (ex: URL do Ollama local ou proxy).

---

<p align="center"><em>Bali-Agent AI — Nunca um agente sozinho. Sempre um time.</em></p>
