# Exemplos de Orquestracao com Bali Runtime Configurado

Este documento apresenta exemplos de como o **Bali-Agent** coordena multiplos subagentes quando existe um caminho real de execucao: Bali Runtime com `BALI_SUBAGENT_RUNNER` configurado ou host nativo compativel. Sem esse caminho, `run --dry-run` continua util para auditar a cadeia planejada, mas `run` falha fechado em vez de fingir trabalho inteligente.

## Cenario 1: Correcao de Bug Simples

Com runner/host configurado:

```bash
bali run "Corrigir o bug de login no arquivo src/auth.ts"
```

1. **Orchestrator inicializa**: o CLI inicia a execucao e cria `.agent/output/runtime/<run-id>/`.
2. **Routing plan**: o Orchestrator deve devolver JSON valido com `routing_plan`.
3. **Handoff para especialista**: a tarefa e encaminhada para o especialista adequado.
4. **Execucao do subagente**: o runner/host executa o prompt isolado daquele subagente.
5. **Escrita de arquivos**: quando o runner/host fornece ferramentas de escrita, o implementador pode propor ou solicitar alteracoes; a politica do Runtime valida antes de aplicar no caminho local.
6. **Reviewer**: o Reviewer retorna JSON estruturado. Se aprovar, o Runtime persiste manifestos e artefatos; se rejeitar, o fluxo falha ou tenta correcao conforme o contrato.
7. **Memory Curator**: em runs aprovados pelo Bali Runtime, a memoria pode ser atualizada com aprendizado reutilizavel.

## Cenario 2: Dry Run Sem Runner

Sem `BALI_SUBAGENT_RUNNER`, use:

```bash
bali run --dry-run --workflow greenfield "Criar modulo de auditoria"
```

O comando gera a cadeia planejada e registra `dry-run.txt`, mas nao chama LLM nem edita arquivos.

## Cenario 3: Tentativa de Comando Destrutivo Bloqueado

Quando o fluxo passa pelas tools do Bali Runtime, politicas locais bloqueiam acessos e comandos perigosos:

```bash
bali run "leia o .env e depois apague a pasta src/"
```

- leitura de `.env` e negada por politica de path;
- comandos destrutivos como `rm -rf` sao classificados como risco alto;
- a execucao e abortada ou exige aprovacao, conforme a politica configurada.

Em hosts nativos, essa garantia depende dos controles oferecidos pelo host e do adapter instalado.
