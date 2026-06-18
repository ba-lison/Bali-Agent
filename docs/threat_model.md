# Modelo de Ameaças (Threat Model) e Segurança

Dar acesso a ferramentas de shell, sistema de arquivos e criação de processos para uma LLM apresenta riscos de segurança críticos (Excessive Agency, Prompt Injection, Vazamento de Credenciais). O **Bali-Agent** aborda esses riscos através de mitigação em código.

## Principais Vetores de Ameaça e Mitigações

### 1. Execução Excessiva ou Destrutiva de Comandos (Excessive Agency)
- **Ameaça**: A LLM gera um comando destrutivo como `rm -rf /` ou tenta abrir conexões reversas de rede com `nc`/`bash`.
- **Mitigação**:
  - `shell=True` está desativado por padrão. Comandos são parseados em tokens seguros via `shlex.split`.
  - Classificação por classe de risco:
    - **R2 (Permitido)**: Comandos de testes/linters explícitos (`pytest`, `npm test`).
    - **R4 (Bloqueado/Requer Aprovação)**: Comandos contendo executáveis como `rm`, `del`, `format`, `curl`, `wget`, ou operadores de encadeamento de shell (`&&`, `||`, `;`, `|`).
  - O runtime exige uma aprovação humana interativa estruturada para comandos considerados fora da lista R2.

### 2. Path Traversal e Acesso Fora do Workspace
- **Ameaça**: A LLM tenta ler `/etc/passwd`, chaves SSH do usuário em `~/.ssh/`, ou sobrescrever arquivos de sistema fora do repositório.
- **Mitigação**:
  - Resolução forçada de caminhos via `Path(path).resolve()`.
  - Bloqueio imediato com exceção `PermissionError` caso o caminho resolvido esteja fora do diretório raiz do projeto (`root_dir`).

### 3. Vazamento de Credenciais e Segredos (Secret Disclosure)
- **Ameaça**: Chaves de API de nuvem (OpenAI, AWS, GitHub) ou arquivos `.env` são lidos e repassados no histórico de mensagens da LLM ou salvos na memória operacional.
- **Mitigação**:
  - `ToolPolicy.can_read` e `can_write` bloqueiam automaticamente o acesso a arquivos contendo `.env` ou diretórios do Git (`.git/`).
  - `ContextPacker` e `ToolPolicy` escaneiam todas as saídas de ferramentas e conteúdos de mensagens usando regexes pré-definidos para segredos.
  - Substituição instantânea de strings detectadas por tokens de redação como `[REDACTED OPENAI / ANTHROPIC API KEY]`.

### 4. Loops Infinitos de Execução (Model Denial of Service)
- **Ameaça**: Agentes entram em um loop recursivo infinito chamando uns aos outros ou repetindo tool calls infrutíferas.
- **Mitigação**:
  - Configuração estrita de `max_iterations` no manifesto YAML (padrão: 6 a 10).
  - Controle rígido de profundidade de criação de agentes para evitar loops em cascata.
