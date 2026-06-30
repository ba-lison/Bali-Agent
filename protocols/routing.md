# Protocolo de Roteamento

> Como o Orchestrator transforma pedidos humanos em trabalho de time.

---

## 1. Topologia

O Orchestrator e o hub central. Ele fala com o humano, classifica o pedido, escolhe o fluxo, despacha subagentes reais, valida saidas, aciona Reviewer e so entao devolve resultado.

```text
Human -> Orchestrator -> Subagent(s) -> Orchestrator -> Reviewer -> Orchestrator -> Human
```

O Orchestrator nunca implementa codigo e nunca faz role-play de outro agente.

---

## 2. Triagem

| Classe | Exemplos | Caminho |
|--------|----------|---------|
| Trivial | duvida pontual, explicacao curta | Orchestrator responde e usa Reviewer quando houver entrega de projeto |
| Pequeno | bugfix local, copy, config simples | Especialista -> Reviewer -> Orchestrator |
| Medio | feature local, refactor pequeno | Planner -> Reviewer do plano -> Especialista -> Reviewer |
| Grande | projeto novo, feature estrutural, migracao | Product Spine -> Recruiter se necessario -> Planner -> Especialistas -> QA/Security -> Reviewer |

Esforco proporcional: tarefa pequena nao vira burocracia, mas trabalho real de projeto nao pula subagente nem Reviewer.

---

## 3. Product Spine

Projeto novo sempre segue:

```text
Discovery -> PRD Writer -> SDD Architect
```

Feature grande tambem usa Product Spine quando altera produto, dados, arquitetura, integracao, permissoes, billing, IA, deploy ou seguranca.

Discovery faz entrevista e descoberta de projeto em andamento. PRD Writer transforma entendimento em requisitos. SDD Architect transforma PRD em arquitetura e plano tecnico. Planner e especialistas executam depois.

---

## 4. Selecao de Time

1. Leia `.agent/subagent.config.yaml`.
2. Consulte `time.core`, `time.project_fixed`, `time.especialistas` e `model_policy`.
3. Use especialistas fixos existentes quando o escopo bater.
4. Acione Recruiter quando uma competencia recorrente nao existir.
5. Crie agente temporario quando a demanda for pontual.
6. Nunca crie especialista fixo sem escopo, gatilhos de roteamento e motivo.

---

## 5. Ciclo de Validacao

```text
Subagent output
  -> Orchestrator valida
  -> Reviewer revisa
  -> se aprovado: Memory Gate
  -> se reprovado: volta ao subagent com feedback
```

Limite padrao: ate 3 tentativas por especialista. Na quarta falha, escale ao humano com diagnostico.

---

## 6. Memory Gate

Ao concluir task, gate, decisao, bug nao obvio, incidente, PR ou commit, o Orchestrator aciona `memory-curator`.

O Memory Curator:

- Atualiza `.agent/working-context.md` com estado vivo.
- Registra `.agent/memory.md` apenas quando houver aprendizado duravel.
- Rejeita logs brutos, segredos e dados pessoais desnecessarios.

---

## 7. Sequenciamento

Agentes de escrita usam `max_parallel: 1` por padrao. Tarefas acopladas declaram `depends_on`, `produces` e `consumes`.

Backend/API/schema precede frontend/UI quando a UI depende do contrato de dados. Security e QA entram antes do Reviewer final quando a mudanca tocar risco, permissao, dados ou comportamento critico.

---

## 8. Runtime Routing Plan

Quando estiver rodando via Bali Runtime, a primeira resposta do Orchestrator deve conter um bloco JSON `routing_plan` extraivel:

```json
{
  "routing_plan": true,
  "classification": "small|medium|large",
  "execution_mode": "sequential",
  "max_parallel": 1,
  "context_scope": "minimal",
  "max_retries": 3,
  "steps": [
    {
      "id": "step-id",
      "agent": "implementer",
      "prompt": "tarefa atomica",
      "depends_on": [],
      "produces": [],
      "consumes": [],
      "review": true
    }
  ]
}
```

---

## 9. Anti-Patterns

- Orchestrator implementando codigo.
- Role-play de multiplos agentes no mesmo contexto.
- Especialista fixo criado para tarefa pontual.
- Execucao grande sem Discovery/PRD/SDD.
- Memoria tratada como log bruto.
- Reviewer executado pelo mesmo agente que implementou.

---

Routing v4: Product Spine primeiro, subagentes reais sempre, memoria automatica no fim do ciclo.
