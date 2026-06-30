# Protocolo de Memoria Curada

> Define como o Bali-Agent aprende com o projeto sem virar deposito de logs.

---

## 1. Objetivo

Memoria nao e opcional nem depende do usuario pedir. Todo ciclo relevante passa por Memory Gate.

O Bali usa duas memorias:

- `.agent/working-context.md`: estado vivo, handoff, milestone, proxima acao, riscos ativos.
- `.agent/memory.md`: historico curado de decisoes, tasks, commits, PRs, incidentes e aprendizados reutilizaveis.

---

## 2. Memory Gate

Ao concluir task, gate, decisao arquitetural, bug nao obvio, incidente, PR ou commit, o Orchestrator chama `memory-curator`.

O fluxo e:

```text
Subagent termina
  -> Reviewer aprova
  -> Orchestrator chama memory-curator
  -> working-context.md recebe estado vivo
  -> memory.md recebe aprendizado duravel quando houver
```

Especialistas podem sugerir `memory_suggestions`, mas o Memory Curator decide o que fica.

---

## 3. Quando Atualizar Working Context

Atualize `.agent/working-context.md` quando a informacao responde "onde estamos agora":

- tarefa atual;
- agente com a bola;
- gate atual;
- proxima acao;
- riscos ativos;
- progresso recente;
- especialistas recem-criados que afetam o roteamento imediato.

---

## 4. Quando Registrar Memoria Curada

Registre `.agent/memory.md` quando a informacao responde "o que aprendemos e deve sobreviver":

- decisao tecnica ou de produto;
- bug nao obvio e sua causa;
- incidente e runbook;
- trade-off aceito;
- especialista fixo criado e seu escopo;
- padrao local importante;
- comando de verificacao relevante;
- risco aceito ou pendencia critica.

---

## 5. O Que Nao Registrar

- Logs longos de terminal.
- Conteudo copiado sem curadoria.
- Segredos, tokens, chaves ou payloads sensiveis.
- Dados pessoais desnecessarios.
- Opiniao solta sem decisao ou consequencia.
- Estado passageiro que pertence apenas ao working context.

---

## 6. Comando Padrao

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

O runtime bloqueia padroes obvios de segredo. Se precisar citar dado sensivel, cite apenas a classe do dado e o motivo, nunca o valor.

---

## 7. Responsabilidade

- Orchestrator garante que o Memory Gate aconteca.
- Memory Curator escreve ou rejeita a memoria.
- Reviewer aprova a entrega antes de memoria duravel.
- Especialistas sugerem entradas, mas nao despejam logs.

---

Memoria automatica, curada e segura. Nunca log bruto.
