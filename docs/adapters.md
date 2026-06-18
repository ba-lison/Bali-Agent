# Guia de Adaptadores (Adapters)

O **Bali-Agent** separa adaptadores (adapters) de garantias de comportamento. Cada IDE, CLI ou LLM suportada declara explicitamente quais capacidades ela suporta nativamente.

## Contrato de Capacidades dos Adaptadores

Cada adaptador herda de `BaseAdapter` e retorna um manifesto de suporte contendo:

```yaml
adapter: [nome-do-adaptador]
supports:
  native_subagents: true/false
  pre_tool_hooks: true/false
  post_tool_hooks: true/false
  session_hooks: true/false
  permissions: true/false
  background_agents: true/false
```

Se um adaptador não suportar isolamento nativo ou políticas de tool control, o runtime do Bali-Agent executará sob o **Bali Runtime** como fallback universal seguro.

## Adaptadores Suportados e Recursos Declarados

### 1. Claude Code (`bali_agent/adapters/claude.py`)
- **Subagentes Nativos**: Sim.
- **Pre/Post Tool Hooks**: Sim (configura interceptores no CLI do Claude).
- **Controle de Permissões**: Sim.
- **Fallback**: Utiliza subagentes nativos quando disponíveis; senão, delega ao Bali Runtime.

### 2. Codex (`bali_agent/adapters/codex.py`)
- **Subagentes Nativos**: Sim.
- **Configuração**: Configurações geradas em `.codex/agents/*.toml`.

### 3. OpenCode (`bali_agent/adapters/opencode.py`)
- **Subagentes Nativos**: Não (fallback para Bali Runtime).
- **Configuração**: Cria arquivo `opencode.json` mapeando comandos de fallback para a CLI do Bali.

### 4. Cursor (`bali_agent/adapters/cursor.py`)
- **Subagentes Nativos**: Não (baseado em prompts/regras).
- **Configuração**: Cria regras locais de prompt sob `.cursor/rules/bali-agent.mdc`.

### 5. Gemini e Ollama (`bali_agent/adapters/gemini.py`, `bali_agent/adapters/ollama.py`)
- **Subagentes Nativos**: Não.
- **Fallback**: Rodam em loop usando o Bali Runtime seguro e isolado por processos.

## Comando de Verificação

Você pode auditar os recursos suportados pelo adaptador ativo no projeto executando:

```bash
bali verify-adapter [nome-do-adaptador]
```
Exemplo:
```bash
bali verify-adapter claude-code
```
