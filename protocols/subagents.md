# Protocolo de Subagentes Reais

> Define o contrato operacional do Bali-Agent: o framework e seus adapters devem
> materializar subagentes reais. role-play de vários papéis no mesmo contexto não
> é modo válido de execução.

## Objetivo Master

O Bali-Agent deve operar com subagentes reais em todo projeto. "Real" significa
que Orchestrator, Planner, especialistas e Reviewer possuem definição própria e
são executados por um mecanismo que preserve isolamento operacional: subagente
nativo da ferramenta, processo separado, sessão separada ou chamada separada ao
modelo.

O modelo é intercambiável. A orquestração não é. Claude, GPT, Gemini, Llama,
Ollama ou outro provider podem alimentar os subagentes, mas não substituem a
materialização do time.

Este protocolo deve funcionar em Antigravity, Claude Code, Codex, OpenCode,
Cursor, Gemini CLI, Ollama e qualquer IDE/LLM futuro através de um dos dois
caminhos: adapter nativo ou Bali Runtime.

## Ordem de resolução

O Setup Agent e os adapters seguem esta ordem:

1. **Adapter nativo da ferramenta**: use o mecanismo oficial da ferramenta para
   criar subagentes reais. Exemplo: `.claude/agents/*.md` no Claude Code.
2. **Bali Runtime**: quando a ferramenta não expuser subagentes nativos, execute
   cada agente em sessão, processo ou chamada isolada, com entrada e saída
   registradas em `.agent/output/`.
3. **Falha fechada**: se não houver adapter nativo nem Bali Runtime disponível,
   pare e informe ao usuário que aquele ambiente ainda não consegue executar
   subagentes reais.

## Requisitos mínimos

- `.agent/subagent.config.yaml` deve existir e conter
  `subagents_policy.role_play_permitido: false`.
- `.agent/team/orchestrator.md`, `.agent/team/planner.md` e
  `.agent/team/reviewer.md` devem existir.
- `.agent/team/discovery.md`, `.agent/team/prd-writer.md` e
  `.agent/team/sdd-architect.md` devem existir como agentes base do fluxo.
- Pelo menos um especialista `spec-*.md` deve existir em `.agent/team/`.
- Se nenhum especialista existente cobrir a tarefa, o Orchestrator deve criar um
  novo `spec-*.md`, registrar no manifesto e salvar o evento em
  `.agent/output/subagents-created.md`.
- Quando `claude-code` estiver em `enforcement_adapters`, os subagentes devem
  estar espelhados em `.claude/agents/*.md`.
- O Reviewer deve ser executado como agente separado do agente que implementou a
  mudança.
- `.agent/runtime/bali_runtime.py` deve suportar `verify`, `list-agents`,
  `create-agent` e `run`.
- `.agent/runtime/bali_runtime.py create-agent` deve criar subagentes
  reutilizáveis em `.agent/team/` e atualizar o manifesto.
- `.agent/memory.md` deve existir para memoria curada do projeto.
- `BALI_LLM_COMMAND` é o contrato universal para plugar qualquer CLI/modelo. O
  comando pode usar `{prompt_file}`, `{output_file}` e `{agent}`.

## Bali Runtime

Comandos mínimos:

```bash
python .agent/runtime/bali_runtime.py verify
python .agent/runtime/bali_runtime.py list-agents
python .agent/runtime/bali_runtime.py create-agent --id spec-pagamentos --scope "pagamentos e webhooks"
python .agent/runtime/bali_runtime.py run --dry-run "descreva a tarefa"
```

Exemplo com Ollama:

```bash
BALI_LLM_COMMAND='ollama run llama3.1 < {prompt_file}' python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Cada etapa recebe um prompt próprio e grava output próprio. O Reviewer recebe a
saída dos agentes anteriores, mas não é o mesmo agente que implementou.

## Falha fechada

Nunca substitua subagentes reais por "um modelo respondendo como se fosse vários".
Se a execução isolada não estiver disponível, a resposta correta é bloquear a
tarefa, explicar qual adapter/runtime falta e orientar a instalação ou atualização
necessária.
