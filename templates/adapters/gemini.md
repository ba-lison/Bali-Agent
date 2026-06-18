# Gemini CLI Adapter

Gemini CLI carrega contexto via `GEMINI.md` e pode ser configurado para carregar
`AGENTS.md` com `.gemini/settings.json` usando `context.fileName`. Isso é
contexto, não subagente isolado.

Contrato:
- O installer cria/mescla `.gemini/settings.json` com `context.fileName`.
- Use `BALI_LLM_COMMAND` para executar cada subagente em chamada/processo
  separado:

```bash
BALI_LLM_COMMAND='gemini < {prompt_file}' python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Adapte o comando ao CLI instalado. Cada agente recebe prompt e output próprios.
