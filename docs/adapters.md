## Adapters Ativos

> Documentação técnica dos adapters de enforcamento do Bali-Agent.
> Cada adapter conecta o time de subagentes a uma superfície nativa (IDE, CLI, terminal).

### 1. Claude Code (`bali_agent/adapters/claude.py`)

Claude Code surfaces suportadas pelo Bali-Agent:

| Superficie | Caminho Bali | Observacao |
|-----------|--------------|------------|
| **CLI/terminal** (`claude`) | `.claude/agents/*.md` ou Bali Runtime | Use subagentes nativos quando disponiveis; caso contrario rode `bali --root . run "<tarefa>"`. |
| **Desktop Code tab** | `.claude/agents/*.md` ou Bali Runtime | A sessao precisa ter acesso ao workspace local/remoto. |
| **VS Code / JetBrains** | `.claude/agents/*.md` | Integracoes de IDE consomem o mesmo projeto e instrucoes persistentes. |
| **Web/cloud** | `.claude/agents/*.md` quando o workspace esta montado | Se nao houver shell/tools, exponha Bali por wrapper externo. |
| **API pura sem shell** | Wrapper externo obrigatorio | Use MCP, CI job, webhook ou servico que execute o Bali Runtime. |

- **Fallback universal**: Bali Runtime com `BALI_LLM_COMMAND` ou `bali --root . run`.
- **Subagentes Nativos**: Sim (`.claude/agents/*.md`).
- **Hooks**: `SessionStart` e `UserPromptSubmit` via `.agent/hooks/claude_hook.py` — re-injeta regras invioláveis a cada prompt.
- **Configuração**: `.claude/settings.json` com `context.alwaysInclude` + `hooks`.

### 2. OpenCode (`bali_agent/adapters/opencode.py`)
- **Subagentes Nativos**: Sim (`.opencode/agents/*.md` com `mode: subagent`).
- **Configuração**: `opencode.json` com `instructions` + `references` para AGENTS.md e protocolos.

### 3. Codex (`bali_agent/adapters/codex.py`)
- **Subagentes Nativos**: Sim (`.codex/agents/*.toml`).
- **Configuração**: `.codex/config.toml` com `max_threads = 1` por padrão para evitar colisão de quota.

### 4. Cursor (`bali_agent/adapters/cursor.py`)
- **Subagentes Nativos**: Não (baseado em regras/prompts).
- **Fallback**: Bali Runtime para isolamento real de subagentes.
- **Configuração**: `.cursor/rules/bali-agent.mdc` com `alwaysApply: true`.

### 5. Antigravity 2.0 / CLI (`bali_agent/adapters/antigravity.py`)

Suporta todas as superfícies Antigravity:

| Superfície | Skills path | Subagentes |
|-----------|-------------|------------|
| **Antigravity 2.0** (desktop app, VS Code fork) | `.antigravity/skills/` | `define_subagent` + Manager view multi-agente |
| **Antigravity CLI** (`agy`, terminal) | `.agents/skills/` | `define_subagent` + background agents |

- **Subagentes Nativos**: Sim. `define_subagent` para definir subagentes customizados; background agents existem, mas o Bali-Agent usa fila segura por padrão (`max_parallel: 1`) para agentes de escrita.
- **Contexto**: Lê `AGENTS.md` automaticamente da raiz + skills como injeção de contexto.
- **Configuração**: Skills em ambos os paths para compatibilidade máxima.
- **Nota**: O Antigravity CLI (binário `agy`, Go) substituiu o Gemini CLI (descontinuado em Jun/2026).

### Contrato operacional comum

- Agentes de escrita rodam em sequência por padrão: `execution_mode: "sequential"`, `max_parallel: 1`.
- Subagentes recebem contexto mínimo: tarefa, artefatos/contratos relevantes e prior output necessário.
- Tarefas acopladas usam produtor antes do consumidor: backend/API/schema em `produces`, frontend/UI em `depends_on` + `consumes`.
- Falhas de quota, timeout ou crash devem virar `agent_failed` estruturado antes de qualquer novo dispatch.

### 6. Ollama / API crua (`bali_agent/adapters/ollama.py`)
- **Subagentes Nativos**: Não.
- **Fallback**: Bali Runtime com `BALI_LLM_COMMAND` para subagentes isolados por processo.

---

## Comando de Verificação

```bash
bali verify-adapter [nome-do-adaptador]
```

Exemplo:
```bash
bali verify-adapter claude-code
bali verify-adapter antigravity
```
