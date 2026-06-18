# Protocolo de Memoria Curada

> Define como o Bali-Agent registra memoria recorrente sem transformar o projeto
> em um deposito de logs.

## Objetivo

Cada task, commit e PR relevante deve deixar uma memoria curta, revisada e util
para a proxima sessao. A memoria pertence ao projeto e fica em `.agent/memory.md`.

## Fonte de Verdade

- `.agent/working-context.md` e estado vivo: milestone atual, handoff, proxima acao,
  riscos ativos e progresso recente. Nao use esse arquivo como historico.
- `.agent/memory.md` e historico curado: decisoes, tasks concluidas, commits, PRs,
  incidentes, riscos aceitos e aprendizados reutilizaveis.
- Se a informacao explica "onde estamos agora", atualize `working-context.md`.
- Se a informacao explica "o que aprendemos e deve sobreviver a sessoes futuras",
  registre em `memory.md`.

## Quando Registrar

- Ao concluir uma task.
- Ao criar ou revisar um commit.
- Ao abrir, atualizar ou revisar um PR.
- Ao aceitar uma decisao arquitetural ou trade-off importante.
- Ao resolver incidente, bug nao-obvio ou regressao.

## O Que Registrar

- ID gerado pelo runtime.
- Referencia externa quando existir: task, commit SHA, PR, issue ou incidente.
- Resumo do que mudou.
- Motivo da decisao.
- Arquivos ou artefatos criticos.
- Verificacao executada.
- Riscos, pendencias ou follow-ups.

## O Que Nao Registrar

- Logs longos de terminal.
- Conteudo copiado sem curadoria.
- Segredos, tokens, payloads sensiveis ou dados pessoais sem necessidade.
- Opinioes soltas sem decisao ou consequencia tecnica.

## Comando Padrao

```bash
python .agent/runtime/bali_runtime.py remember \
  --kind task \
  --title "titulo curto" \
  --ref "TASK-123 ou abc1234 ou PR #12" \
  --summary "o que foi feito e por que importa" \
  --files "arquivos criticos" \
  --tests "comandos e resultado" \
  --risks "riscos ou pendencias"
```

O runtime bloqueia entradas com padroes obvios de segredo. Se precisar citar
um dado sensivel, escreva a classe do dado e o motivo, nunca o valor.

## Responsabilidade

O Orchestrator e responsavel por registrar a memoria. Especialistas podem
sugerir entradas, mas o Orchestrator revisa e salva somente o que for util.
