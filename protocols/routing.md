# Protocolo de Roteamento (Hub-and-Spoke)

> Como o Orchestrator (hub central) transforma QUALQUER pedido em trabalho de time.
> Aplica-se a todo projeto que tenha `.agent/subagent.config.yaml`.

---

## 1. Topologia

O Orchestrator opera como **hub central** de uma topologia estrela. Todo pedido do humano entra pelo Orchestrator, é delegado a subagentes reais e isolados, validado, revisado e só então devolvido ao humano.

```
Humano ↔ Orchestrator (hub)
              ↕
    ┌─────────┼─────────┐
    ↓         ↓         ↓
  Planner  Espec.1   Espec.2   ← subagentes reais (isolados)
              ↕
         Orchestrator           ← valida, rejeita, reenvia
              ↓
          Reviewer               ← gate final obrigatório
              ↕
         Orchestrator           ← devolve ao humano
              ↕
           Humano
```

**Regra zero:** O Orchestrator NUNCA trabalha solo. NENHUM pedido — por mais trivial que seja — escapa de passar por subagente(s) + Reviewer.

---

## 2. Triagem

Ao receber um pedido, o Orchestrator classifica:

| Classe | Exemplos | Caminho |
|--------|----------|---------|
| **Trivial** | Dúvida pontual, "que horas são?", explicação de 1 arquivo | Orchestrator responde direto → Reviewer (sanity-check) |
| **Pequeno** | Bugfix localizado, ajuste de copy, tweak de config | Especialista executa → Orchestrator valida → Reviewer |
| **Médio** | Feature em 2-3 arquivos, refactor local | Planner (cria plano) → Reviewer (valida plano) → Especialista(s) → Reviewer |
| **Grande** | Feature multi-módulo, refactor estrutural, migração | Planner → Reviewer (plano) → Especialista(s) em sequência → Reviewer |

**Regra de ouro:** Esforço proporcional. O Orchestrator responde trivial direto — sem burocracia. Tarefas complexas passam pelo pipeline completo (plano → validação do plano → execução → revisão).

A triagem é explícita: o Orchestrator informa ao humano a classe e o caminho em 1-2 linhas.

---

## 3. Ciclo de Validação (Iteração)

Após receber a saída de um subagente, o Orchestrator **valida** antes de prosseguir:

```
Recebe saída do especialista
        ↓
    Está completa e correta?
    ├── ✅ Sim → Encaminha ao Reviewer
    └── ❌ Não → Rejeita + reenvia ao especialista com feedback
                    ↓
              Especialista refaz (até 3 tentativas)
                    ↓
              Na 4ª falha → escala ao humano
```

**Regra de ouro:** O Orchestrator é o **guardião da qualidade**. Ele não é um repassador passivo de mensagens — ele examina, questiona, rejeita e exige correção.

---

## 4. Gate do Reviewer

**Toda entrega**, sem exceção, passa pelo Reviewer como subagente real antes de chegar ao humano.

O Reviewer retorna um veredito JSON:
```json
{
  "approved": true|false,
  "blockers": [{"reason": "..."}],
  "warnings": [{"reason": "..."}],
  "nits": [{"reason": "..."}]
}
```

- **approved: true** → Orchestrator devolve ao humano.
- **approved: false** → Orchestrator reenvia ao especialista com os blockers listados.

O Orchestrator **nunca** ignora ou sobrepõe o veredito do Reviewer.

---

## 5. Seleção de Especialista

1. Leia `time.especialistas[].escopo` no manifesto.
2. Mapeie pela extensão do arquivo ou domínio:
   - **`spec-frontend`**: `.tsx`, `.jsx`, `.html`, `.css`, `.scss`, `.vue`, componentes client-side
   - **`spec-backend`**: `.py`, `.go`, `.cs`, `.js`/`.ts` server-side, rotas, APIs
   - **`spec-database`**: `.sql`, schema ORM, migrations, queries
   - **`spec-devops`**: `Dockerfile`, CI/CD, infra, containers
   - **`spec-security`**: RLS, auth middlewares, permissões
   - **`spec-testing`**: diretórios `tests/`, `__tests__/`, `.test.*`, `.spec.*`
   - **`spec-docs`**: `.md` de documentação, OpenAPI/Swagger
   - **`spec-implementer`**: Fallback geral para qualquer stack não coberta
3. Se nenhum especialista cobrir: **crie um novo** antes de executar a tarefa.
4. Tarefas multi-stack podem disparar múltiplos especialistas em paralelo ou sequência.

---

## 6. Modo Greenfield

Quando `modo: greenfield`, o roteamento segue o pipeline SDLC com gates humanos:

```
Discovery → Gate 1 (humano) → PRD Writer → Gate 2 (humano) → SDD Architect →
Gate 3 (humano) → Planner → Especialista(s) → Reviewer → Gate 5 (humano)
```

Cada gate para e aguarda aprovação humana antes de prosseguir. Ver `protocols/approval-gates.md`.

---

## 7. Contrato de Isolamento

Subagentes **SEMPRE** são reais. Ver `protocols/subagents.md` para o contrato completo.

Resumo da ordem de resolução:
1. **Subagentes nativos da ferramenta** (Task tool, `@mention`, `.opencode/agents/`, `.claude/agents/`, etc.)
2. **Bali Runtime** (`python .agent/runtime/bali_runtime.py run` com subprocesso isolado)
3. **Falha fechada** (bloquear, informar humano)

---

## 8. Anti-Padrões

| Anti-padrão | Por que é errado |
|-------------|-----------------|
| Orchestrator respondendo sozinho | Viola "nunca solo" |
| Orchestrator implementando código | Viola separação de responsabilidades |
| Cadeia linear fixa (A→B→C) sem validação | Viola hub-and-spoke + iteração |
| Output bruto de subagente ao humano | Viola papel de porta-voz do Orchestrator |
| Subagente role-play no mesmo contexto | Viola contrato de isolamento real |

---

<p align="center"><em>Routing v3.0 — Hub central. Nunca solo. Sempre validado. Sempre revisado.</em></p>
