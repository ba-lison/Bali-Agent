# Ollama Adapter

Ollama é provider/modelo, não orquestrador de agentes. Para usar Bali-Agent com Ollama,
execute pelo Bali Runtime com chamadas isoladas por agente.

Exemplo:

```bash
BALI_LLM_COMMAND='ollama run llama3.1 < {prompt_file}' python .agent/runtime/bali_runtime.py run "descreva a tarefa"
```

Troque `llama3.1` pelo modelo local desejado.
