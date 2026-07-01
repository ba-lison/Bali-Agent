# SDD: Honestidade de Runtime e Entrega

> Autor: Codex + Alison | Data: 2026-06-30 | Versao: 1.0 | Status: Implementado

## 1. Contexto

O Bali-Agent promete uma fundacao subagent-first. A auditoria senior confirmou que isso nao e vaporware: existem CLI, runtime, manifestos, agentes, adapters, memoria e testes. A lacuna esta em tornar essa entrega auditavel por comando, nao apenas por leitura do README.

## 2. Decisao de Design

Adicionar um comando `capability-report` ao CLI principal. Ele nao executa agentes nem chama LLM. Ele inspeciona o projeto alvo e imprime uma matriz de maturidade operacional.

O comando usa quatro categorias:

- `Delivered`: capacidade entregue por codigo local verificavel.
- `Contract-dependent`: capacidade existente, mas dependente de contrato com LLM/comando externo.
- `Host-dependent`: capacidade materializada pelo Bali, mas executada pela ferramenta externa.
- `Not delivered`: capacidade explicitamente fora da entrega atual.

## 3. Interface

```bash
bali --root /caminho/do/projeto capability-report
```

Saida esperada:

```text
Bali Capability Report
Root: /repo

[Delivered]
- CLI installed structure: available
- Core team manifest: available

[Contract-dependent]
- Runtime with LLM command: unavailable (BALI_LLM_COMMAND not configured)

[Host-dependent]
- claude-code native adapter: unavailable (...)

[Not delivered]
- Parallel agent execution: not implemented (runtime requires sequential/max_parallel=1)
```

O retorno e `0` porque a ausencia de capacidade nao e erro do relatorio. Erros continuam aparecendo em `verify` e `verify-adapter`.

## 4. Dados Inspecionados

| Capacidade | Fonte |
|---|---|
| Estrutura `.agent` | `.agent/` e arquivos principais |
| Core Team | `bali_agent.core.agent_manager.verify(root)` |
| Runtime instalado | `.agent/runtime/bali_runtime.py` |
| LLM command | `BALI_LLM_COMMAND` |
| Provider mode | `BALI_LLM_PROVIDER` |
| Adapters nativos | `ADAPTERS[name](root).verify()` |
| Paralelismo | constante documental: ainda nao implementado |
| Multi-modelo real | constante documental: depende do host/wrapper |

## 5. Alternativas Consideradas

### 5.1 Apenas README

Baixo risco, mas fraco. O problema principal e justamente depender de texto.

### 5.2 `verify` mais rigoroso

Ruim para este caso. `verify` deve falhar quando a instalacao esta incompleta; `capability-report` deve explicar maturidade e dependencias sem bloquear.

### 5.3 Auditoria automatica do README

Interessante, mas maior do que o necessario agora. Pode virar etapa futura: comparar claims em markdown contra capacidades declaradas.

## 6. Seguranca

O comando nao le segredos, nao executa comandos externos e nao chama LLM. Ele apenas verifica existencia de arquivos, variaveis de ambiente e metodos locais de adapters.

## 7. Testes

Adicionar teste que:

- Inicializa um projeto temporario com `init_command`.
- Executa `capability_report`.
- Verifica que a saida contem as quatro categorias.
- Verifica que o runtime local aparece como entregue.
- Verifica que paralelismo aparece como nao implementado.

## 8. Rollout

Mudanca compativel com versoes anteriores. Nenhum comando existente muda de comportamento.

## 9. Futuro

- Exportar `--json` para automacoes.
- Usar o relatorio em CI.
- Ligar cada claim do README a uma capability id.
- Criar `bali audit-readme` quando houver uma taxonomia estavel de promessas.
