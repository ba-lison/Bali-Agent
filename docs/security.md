# Guia de Seguranca e Controles de Permissao

Este documento descreve os controles de seguranca do **Bali-Agent**. Eles sao aplicados diretamente quando o Bali Runtime/tools locais conduzem a execucao. Em hosts nativos, Bali materializa politicas e instrucoes, mas a aplicacao final depende dos controles oferecidos pelo host.

## Manifesto de Permissoes (`subagent.config.yaml`)

```yaml
id: spec-frontend
role: frontend-engineer
model: default
allowed_tools:
  - read_file
  - write_file
denied_paths:
  - .env
  - .git/
  - secrets/
max_iterations: 6
max_tokens: 12000
requires_review_by: reviewer
can_spawn_agents: false
```

- **allowed_tools**: lista de ferramentas que o subagente pode invocar. No Bali Runtime/tools locais, ferramenta fora da lista aborta a execucao.
- **denied_paths**: subdiretorios ou arquivos bloqueados para leitura/escrita.
- **can_spawn_agents**: indica se este subagente pode criar novos subagentes.

## Fluxo de Aprovacao Humana

Quando o Bali Runtime e o executor:

1. O runtime avalia o comando contra a classe de risco.
2. Se detectar comando fora da lista permitida ou alteracao critica, aciona aprovacao interativa quando disponivel.
3. A execucao e congelada e o usuario recebe acao solicitada, justificativa, riscos e diff quando houver escrita.
4. Se o usuario recusar, o subagente recebe erro de permissao e deve tentar uma abordagem alternativa.
