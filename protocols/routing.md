# Protocolo de Roteamento

> Como o Orchestrator transforma QUALQUER pedido em trabalho de time. Aplica-se a
> todo projeto que tenha `.agent/subagent.config.yaml`.

## Triagem

Ao receber um pedido, o Orchestrator classifica o tamanho:

| Classe | Exemplos | Caminho |
|--------|----------|---------|
| **Trivial** | dúvida pontual, explicação, leitura de 1 arquivo | Especialista responde direto → Reviewer faz sanity-check rápido |
| **Pequeno** | bugfix localizado, ajuste de copy, tweak de config | Especialista executa → Reviewer revisa |
| **Médio/Grande** | feature, refactor, mudança multi-arquivo | Planner decompõe → especialista(s) executam → Reviewer revisa |

A triagem é explícita: o Orchestrator diz ao usuário em 1-2 linhas qual classe e qual caminho.

## Processo proporcional

A constituição obriga rotear **sempre** pelo time, mas o esforço é proporcional ao pedido.
Nunca aplique o pipeline pesado a uma pergunta trivial; nunca pule o Reviewer numa feature.
O objetivo é "nunca solo", não "sempre burocrático".

## Seleção de especialista

1. Leia `time.especialistas[].escopo` no manifesto.
2. Escolha o especialista cujo escopo melhor casa com a tarefa.
3. Se nenhum casar, escale ao usuário: "não há especialista para X — quer que eu rode o setup de novo para adicionar um?".
4. Tarefas que cruzam stacks podem envolver mais de um especialista em sequência.

## Modo Operate

Fluxo padrão de projeto em andamento:
`pedido → triagem → (Planner se médio/grande) → especialista(s) → Reviewer → entrega`.

## Modo Greenfield

Quando `modo: greenfield`, o roteamento segue o pipeline SDLC de
`agents/_spine/orchestrator/workflows/novo-projeto.md`, com os gates de
`protocols/approval-gates.md`.

## Saída ao usuário

Toda resposta do Orchestrator começa com uma linha de roteamento, ex.:
`🎯 Roteando: [classe=Médio] Planner → spec-supabase → Reviewer`.
