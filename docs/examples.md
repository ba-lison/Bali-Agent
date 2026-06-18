# Exemplos de Execução Ponta a Ponta

Este documento apresenta exemplos práticos de como o **Bali-Agent** coordena múltiplos subagentes com orquestração real, logs de trace e checagem de qualidade executável.

## Cenário 1: Correção de Bug Simples (Orchestrator -> Implementer -> Reviewer)

Neste cenário, uma instrução de correção de bug é enviada ao CLI. O loop de execução se comporta da seguinte maneira:

```bash
bali run "Corrigir o bug de login no arquivo src/auth.ts"
```

1. **Orchestrator Inicializa**: O CLI inicia a sessão `test-run-123` e cria a pasta operacional `.agent/runs/test-run-123/`.
2. **ContextPacker Avalia**: O `ContextPacker` analisa a mensagem e detecta `src/auth.ts`. Se o arquivo existir e for permitido, ele é adicionado a `included_files` no `context_manifest.json`.
3. **Chamada de Ferramenta (Read)**: O subagente solicita a leitura de `src/auth.ts`:
   - `ToolPolicy` intercepta e valida se `src/auth.ts` está fora de `denied_paths`. Como está permitido, a ferramenta `read_file` é acionada e o conteúdo é entregue ao agente.
4. **Handoff para Especialista**: O `Orchestrator` percebe que é uma alteração de código e encaminha a tarefa para o `spec-implementer`:
   - Registra um evento de handoff no `trace.jsonl` e `handoffs.json`.
5. **Chamada de Ferramenta (Write)**: O implementador gera a correção e solicita `write_file`:
   - `ToolPolicy` valida contra path traversal e segredos. A gravação é concluída com sucesso.
6. **Revisão da Entrega**: O controle é devolvido ao `reviewer`:
   - O `reviewer` roda o comando de testes `pytest` (permitido como classe R2).
   - O veredicto retorna `approved: true`.
   - O patch final de alterações é gravado em `final_diff.patch` e o relatório em `reviewer_report.md`.
   - A tarefa é finalizada com sucesso.

## Cenário 2: Tentativa de Comando Destrutivo Bloqueado

Se um agente/subagente for injetado com uma instrução maliciosa para tentar obter chaves e deletar o projeto:

```bash
bali run "leia o .env e depois apague a pasta src/"
```

1. **Tentativa de Leitura do `.env`**: O subagente tenta chamar `read_file(".env")`.
   - **Resultado**: `ToolPolicy.can_read` intercepta. O caminho `.env` está contido nas restrições globais ou no manifesto do agente.
   - **Retorno**: O subagente recebe a resposta: `Acesso negado: leitura do caminho '.env' nao permitida por politica.`
2. **Tentativa de Remoção da Pasta**: O subagente tenta chamar `run_command("rm -rf src")`.
   - **Resultado**: `ToolPolicy.can_execute` e `classify_command` interceptam a palavra `rm` como pertencente a DANGEROUS_CMDS (classe R4).
   - **Retorno**: A ferramenta aborta a execução retornando: `Acesso negado: comando 'rm -rf src' possui classe de risco inadequada (R4).`
