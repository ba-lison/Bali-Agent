# Modelo de Ameacas e Seguranca

Dar acesso a ferramentas de shell, sistema de arquivos e criacao de processos para uma LLM apresenta riscos criticos: excessive agency, prompt injection e vazamento de credenciais. Quando o Bali Runtime executa o fluxo, o **Bali-Agent** mitiga esses riscos em codigo. Em adapters nativos, Bali materializa politicas e instrucoes, mas a aplicacao final depende dos controles do host.

## Principais Vetores e Mitigacoes

### 1. Execucao Excessiva ou Destrutiva

- **Ameaca**: a LLM gera comando destrutivo como `rm -rf /` ou tenta abrir conexoes reversas.
- **Mitigacao no Runtime**:
  - `shell=True` fica desativado por padrao.
  - Comandos sao parseados em tokens seguros.
  - Comandos de alto risco, operadores de shell e ferramentas de rede sao bloqueados ou exigem aprovacao.

### 2. Path Traversal e Acesso Fora do Workspace

- **Ameaca**: a LLM tenta ler chaves SSH, arquivos do sistema ou sobrescrever arquivos fora do repositorio.
- **Mitigacao no Runtime**:
  - caminhos sao resolvidos antes do acesso;
  - acessos fora do diretorio raiz sao bloqueados;
  - paths sensiveis como `.env`, `.git/` e `secrets/` sao negados.

### 3. Vazamento de Credenciais

- **Ameaca**: chaves de API ou `.env` entram no historico da LLM ou na memoria.
- **Mitigacao no Runtime**:
  - leitura e escrita em paths sensiveis sao bloqueadas;
  - conteudos passam por scanner de segredos;
  - valores detectados sao redigidos antes de persistir contexto/memoria.

### 4. Loops Infinitos

- **Ameaca**: agentes entram em loop recursivo ou repetem tool calls sem progresso.
- **Mitigacao no Runtime**:
  - `max_iterations` limita repeticoes;
  - profundidade de criacao de subagentes e controlada;
  - Reviewer e manifests tornam falhas auditaveis.
