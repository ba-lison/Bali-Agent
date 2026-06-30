# Codex Adapter

Codex usa custom agents por arquivo TOML de projeto. O installer do Bali-Agent deve materializar `.agent/team/*.md` como `.codex/agents/<id>.toml` e criar `.codex/config.toml`.

Contrato:
- Use o Core Team completo: Orchestrator, Discovery, PRD Writer, SDD Architect, Planner, Implementer, QA, Security, Reviewer, Recruiter, Memory Curator e Docs.
- Use `spec-*` para especialistas fixos do projeto.
- Use agentes temporarios apenas para tarefas pontuais.
- Cada subagente deve receber contexto minimo: tarefa, arquivos/contratos relevantes e prior output necessario.
- Agentes de escrita usam fila segura (`max_parallel: 1`) quando houver risco de conflito.
- Se a sessao Codex atual nao puder spawnar subagentes, use Bali Runtime.
- Nunca opere Orchestrator, Planner, especialistas e Reviewer como papeis no mesmo contexto.

Validacao:

```bash
python .agent/runtime/bali_runtime.py verify
python .agent/runtime/bali_runtime.py list-agents
```
