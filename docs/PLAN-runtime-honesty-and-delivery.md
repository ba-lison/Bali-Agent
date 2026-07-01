# Plano: Honestidade de Runtime e Entrega

> Autor: Codex + Alison | Data: 2026-06-30 | Status: Aprovado para implementacao

## 1. Objetivo

Transformar a auditoria senior do README em um contrato verificavel de entrega. O Bali-Agent deve continuar se apresentando como subagent-first, mas precisa deixar claro quais capacidades sao entregues pelo codigo, quais dependem de contrato com o LLM e quais dependem do host.

## 2. Referencia de Processo

Este plano segue o fluxo descrito no guia `PR, PRD, SDD, IA no SDLC e Vibe Coding`: ideia -> PRD/plano -> SDD -> implementacao -> testes -> PR/review. A melhoria e pequena, mas deve manter governanca: nada de promessa aspiracional sem criterio de verificacao.

## 3. Problema

O README atual ja e mais honesto do que uma landing page de produto, mas a honestidade ainda vive majoritariamente em texto. Um usuario pode ler "subagentes reais" e assumir isolamento nativo universal, paralelismo ou multi-modelo garantido, quando o codigo entrega uma combinacao mais precisa:

- Runtime isolado por processo/chamada quando `BALI_LLM_COMMAND` esta configurado.
- Materializacao de arquivos para hosts nativos, com execucao dependente do host.
- Product Spine e memoria automatica verificaveis no Bali Runtime.
- Routing dinamico dependente de `routing_plan` JSON valido.

## 4. Escopo

### Dentro do escopo

- Criar um SDD especifico para a melhoria.
- Adicionar um comando CLI de auditoria de capacidades.
- Atualizar README para apontar o comando e reforcar os limites.
- Adicionar teste automatizado para o novo comando.

### Fora do escopo

- Implementar paralelismo real.
- Implementar multi-modelo real por host.
- Integrar com provedores comerciais em runtime provider mode.
- Garantir isolamento nativo em ferramentas externas.

## 5. Criterios de Aceitacao

- `bali --root <projeto> capability-report` imprime uma matriz com quatro grupos: Delivered, Contract-dependent, Host-dependent e Not delivered.
- O comando retorna `0` mesmo quando algumas capacidades estao indisponiveis, porque e um relatorio, nao um gate de build.
- O README documenta o comando e nao transforma dependencia em promessa fechada.
- A suite de testes passa.

## 6. Plano de Implementacao

1. Criar `docs/SDD-runtime-honesty-and-delivery.md`.
2. Adicionar `capability_report(root: Path) -> int` em `bali_agent/cli.py`.
3. Registrar subcomando `capability-report` no parser.
4. Atualizar README em "Estado Atual", "CLI" e "Runtime E Observabilidade".
5. Adicionar teste em `tests/test_cli.py`.
6. Rodar teste focado e suite completa.

## 7. Riscos

| Risco | Mitigacao |
|---|---|
| O relatorio virar mais uma promessa textual | Basear status em arquivos, env vars e adapter verification quando possivel |
| O comando falhar em projeto incompleto | Relatorio deve ser tolerante e indicar ausencias |
| O README ficar longo demais | Adicionar apenas uma secao curta e apontar para o comando |

## 8. Done

- Plano salvo.
- SDD salvo.
- CLI implementado.
- README atualizado.
- Teste automatizado cobrindo o relatorio.
- `pytest` verde.
