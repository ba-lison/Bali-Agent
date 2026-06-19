# Protocolo de Subagentes Reais

> Define o contrato operacional do Bali-Agent: o framework e seus adapters devem
> materializar subagentes reais. Role-play de vários papéis no mesmo contexto não
> é modo válido de execução.

---

## 1. Objetivo Master

O Bali-Agent deve operar com subagentes reais em **todo projeto, toda tarefa, sem exceção**. "Real" significa que Orchestrator, Planner, especialistas e Reviewer possuem definição própria e são executados por um mecanismo que preserve **isolamento operacional**: subagente nativo da ferramenta, processo separado, sessão separada ou chamada separada ao modelo.

O modelo de linguagem é intercambiável (Claude, GPT, Gemini, Llama, Ollama...). A **orquestração não é**. O modelo alimenta os subagentes, mas não substitui a materialização do time.

Este protocolo deve funcionar em qualquer ambiente — Antigravity, Claude Code surfaces (CLI/terminal, Desktop Code tab, VS Code/JetBrains e web/cloud com workspace), Codex, OpenCode, Cursor, Ollama e qualquer IDE/LLM futuro — através de um dos dois caminhos: **adapter nativo** ou **Bali Runtime**. API pura sem shell/tools precisa de wrapper externo (MCP, CI job, webhook ou servico) para acionar o Bali Runtime.

---

## 2. Topologia Hub-and-Spoke

O Orchestrator é o **hub central**. Ele é o único ponto de contato com o humano. Toda tarefa flui assim:

```
Humano → Orchestrator → [Subagente Real 1..N] → Orchestrator (valida) → Reviewer (Subagente Real) → Orchestrator → Humano
```

O Orchestrator **nunca** executa tarefas diretamente. Ele **sempre** delega a subagentes reais e isolados. Se a saída for insuficiente, ele rejeita e reenvia (até 3 tentativas por especialista).

---

## 3. Ordem de Resolução

O Orchestrator segue esta ordem para materializar subagentes reais:

| Prioridade | Mecanismo | Descrição |
|-----------|-----------|-----------|
| **1. Adapter nativo** | Mecanismo oficial da ferramenta | Subagentes nativos: `.claude/agents/`, `.opencode/agents/`, `.codex/agents/`, Task tool, `@mention`, `define_subagent` |
| **2. Bali Runtime** | `python .agent/runtime/bali_runtime.py run` | Executa cada agente em processo isolado via `subprocess`, com entrada/saída em `.agent/output/` |
| **3. Falha fechada** | Bloquear tarefa, informar humano | Se não houver adapter nativo nem Bali Runtime disponível |

---

## 4. Requisitos Mínimos de Instalação

- `.agent/subagent.config.yaml` deve existir com `subagents_policy.role_play_permitido: false`.
- `.agent/team/orchestrator.md`, `.agent/team/planner.md` e `.agent/team/reviewer.md` devem existir.
- `.agent/team/discovery.md`, `.agent/team/prd-writer.md` e `.agent/team/sdd-architect.md` devem existir como agentes base.
- Pelo menos um especialista `spec-*.md` deve existir em `.agent/team/`.
- Se nenhum especialista cobrir a tarefa, o Orchestrator deve criar um novo `spec-*.md`, registrar no manifesto e espelhar no formato nativo da ferramenta.
- Os adapters nativos devem espelhar os agentes do time no formato da ferramenta hospedeira (ex.: `.opencode/agents/*.md`, `.claude/agents/*.md`).
- O Reviewer deve ser executado como subagente separado do agente que implementou a mudança.
- `.agent/runtime/bali_runtime.py` deve suportar `verify`, `list-agents`, `create-agent` e `run`.
- `.agent/memory.md` deve existir para memória curada do projeto.
- `BALI_LLM_COMMAND` é o contrato universal para plugar qualquer CLI/modelo. O comando pode usar `{prompt_file}`, `{output_file}` e `{agent}`.

---

## 5. Verificação de Integridade

O comando `verify` do runtime deve checar:

```bash
python .agent/runtime/bali_runtime.py verify
```

Itens verificados:
- [ ] `.agent/subagent.config.yaml` existe e é válido
- [ ] `subagents_policy.role_play_permitido` é `false`
- [ ] `.agent/team/orchestrator.md`, `planner.md`, `reviewer.md` existem
- [ ] `.agent/team/discovery.md`, `prd-writer.md`, `sdd-architect.md` existem
- [ ] Pelo menos um `spec-*.md` existe
- [ ] Adapters nativos estão sincronizados com `.agent/team/`
- [ ] Bali Runtime está funcional

---

## 6. Contrato de Isolamento por Ferramenta

| Ferramenta | Mecanismo de Isolamento | Caminho |
|-----------|------------------------|---------|
| **OpenCode** | Subagentes nativos (`mode: subagent`) + Task tool | `.opencode/agents/*.md` |
| **Claude Code surfaces** | CLI/terminal, Desktop Code tab, VS Code/JetBrains e web/cloud com workspace usam subagentes nativos + Task tool; API pura sem shell exige wrapper para Bali Runtime | `.claude/agents/*.md` ou `.agent/runtime/bali_runtime.py` |
| **Codex** | Subagentes nativos | `.codex/agents/*.toml` |
| **Antigravity 2.0 / CLI** | `define_subagent` nativo + Manager view/background subagents com fila segura | `.antigravity/skills/` (desktop) ou `.agents/skills/` (CLI) |
| **Cursor** | Bali Runtime (sem subagentes nativos) | `.cursor/rules/bali-agent.mdc` |
| **Ollama / API crua / outros** | Bali Runtime via `BALI_LLM_COMMAND` | `.agent/runtime/bali_runtime.py` |

Capacidade de background/multi-agente não é permissão para paralelismo livre. Agentes de escrita usam `max_parallel: 1` por padrão, contexto mínimo e handoff por contrato (`produces`/`consumes`) quando uma etapa depende da outra.

---

## 7. Criação de Novo Subagente

Quando a tarefa exige competência que não existe no time:

```bash
python .agent/runtime/bali_runtime.py create-agent --id spec-<nome> --scope "<escopo>"
```

O runtime:
1. Cria `.agent/team/spec-<nome>.md` com o escopo fornecido.
2. Registra o novo especialista em `.agent/subagent.config.yaml`.
3. Espelha no formato nativo de cada adapter configurado.
4. Registra o evento em `.agent/output/subagents-created.md`.

---

## 8. Bali Runtime

Comandos:

```bash
python .agent/runtime/bali_runtime.py verify
python .agent/runtime/bali_runtime.py list-agents
python .agent/runtime/bali_runtime.py create-agent --id spec-pagamentos --scope "pagamentos e webhooks"
python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Exemplo com Ollama:

```bash
BALI_LLM_COMMAND='ollama run llama3.1 < {prompt_file}' python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Cada etapa recebe prompt próprio e grava output próprio. O Reviewer é executado como agente separado do agente que implementou.

---

## 9. Falha Fechada

Nunca substitua subagentes reais por "um modelo respondendo como se fosse vários". Se a execução isolada não estiver disponível via adapter nativo nem Bali Runtime, a resposta correta é **bloquear a tarefa**, explicar qual adapter/runtime falta e orientar a instalação necessária.

---

## 10. Regras Invioláveis

1. ❌ **NUNCA** role-play de múltiplos agentes no mesmo contexto.
2. ❌ **NUNCA** pular subagentes — toda tarefa passa por especialista(s) + Reviewer.
3. ❌ **NUNCA** o Orchestrator executar tarefas diretamente.
4. ✅ **SEMPRE** isolar subagentes (processo, sessão ou chamada separada).
5. ✅ **SEMPRE** usar adapter nativo quando disponível; Bali Runtime como fallback.
6. ✅ **SEMPRE** falhar fechado se nenhum caminho de isolamento estiver disponível.

---

<p align="center"><em>Subagentes reais sempre. Isolamento operacional. Nunca role-play.</em></p>
