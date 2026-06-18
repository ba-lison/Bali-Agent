# Memoria Curada do Projeto

> Memoria persistente e revisada do time Bali-Agent. Este arquivo nao e log bruto.
> O Orchestrator atualiza somente com fatos que ajudam proximas sessoes:
> decisoes, trade-offs, arquivos criticos, verificacoes, riscos e aprendizados.

## Como Atualizar

Use o Bali Runtime para registrar entradas curadas:

```bash
python .agent/runtime/bali_runtime.py remember --kind task --title "titulo" --ref "TASK-123" --summary "o que mudou" --tests "comando e resultado"
python .agent/runtime/bali_runtime.py remember --kind commit --title "ajuste de memoria" --ref "abc123" --summary "por que o commit existe" --tests "comando e resultado"
python .agent/runtime/bali_runtime.py remember --kind pr --title "PR de memoria" --ref "PR #123" --summary "escopo e resultado da revisao" --tests "checks executados"
```

## Fonte de Verdade

- `.agent/working-context.md`: estado vivo, proxima acao, handoff e riscos atuais.
- `.agent/memory.md`: historico curado de tasks, commits, PRs, decisoes, incidentes e aprendizados.

## Regras

- Nao copiar logs longos.
- Nao salvar segredo, token, payload sensivel ou dado pessoal desnecessario.
- Registrar somente informacao reutilizavel em novas sessoes.
- Toda entrada deve dizer o que foi feito, por que, como foi verificado e quais riscos sobraram.
- Toda entrada gerada pelo runtime deve conter `ID`; use `Ref` quando houver task, commit, PR, issue ou incidente externo.
