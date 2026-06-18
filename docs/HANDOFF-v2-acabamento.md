# HANDOFF — Bali-Agent v2 (acabamento rumo ao 10)

> **Data:** 2026-06-17 · **Branch:** `fix/v2-acabamento` · **Para:** continuar de onde paramos.
> Este doc é autocontido: dá pra retomar sem o histórico do chat.

## Estado atual

- **Nota:** ~9/10. Sistema coerente da entrada à execução, naming unificado em **Bali-Agent**, suíte **15/15 verde** (`python -m pytest tests/ -q`).
- **Rodar testes:** `pip install -r requirements-dev.txt` e `python -m pytest tests/ -v`.
- **Naming:** marca = **Bali-Agent**. ⚠️ NÃO renomear `subagent.config.yaml`, `.cursor/rules/subagent.mdc` nem o skill `subagent-driven-development` — são nomes/refs reais, não a marca.

### Já feito neste branch (commits `77af64d`, `fe79387` + ajuste de README)
1. `AGENTS.md` raiz reescrito pra v2 (entrada "Setup do time", modo operate em 1º plano, mapa correto, sem ref morta a `agents/implementer/`).
2. Naming unificado pra Bali-Agent (código + docs).
3. `cursor-rule.mdc` com frontmatter único válido (`alwaysApply: true`).
4. `init.py` instala enforcement do Claude Code de forma determinística (`.agent/hooks/claude_hook.py` + `.claude/settings.json`, sem sobrescrever config existente do usuário).
5. `prevent_secrets.py` com allowlist estreitada (removidos `env`/`config`/`const`/`)`).
6. README: tabela honesta de enforcement por ferramenta + nota de modo Operate vs Greenfield.

## ✅ UPDATE 2026-06-17 (sessão seguinte — CONCLUÍDO)
Itens **2, 3, 4, 5, 6 FEITOS**; suíte **16/16 verde**:
- **Item 2:** `templates/verify_setup.py` + cópia no `init.py` (`.agent/verify_setup.py`) + `test_verify_setup_logic`.
- **Item 3:** fiação do `task.md` (init.py copia para `.agent/task.md`; incluído no `test_templates_exist`).
- **Item 4:** `gemini-settings.json` corrigido para `{"contextFileName": "AGENTS.md"}` (chave confirmada na doc do Gemini CLI).
- **Item 5:** CI em `.github/workflows/tests.yml` (roda pytest em push/PR).
- **Item 6:** README com tabela de enforcement por ferramenta + modo Operate.
- Setup Agent agora roda `verify_setup.py` ao final.

**Resta só o ITEM 1 (e2e com LLM real):** procedimento documentado em `examples/dry-run.md`. A parte do
instalador é coberta por `test_installer_flow`; a geração do time pelo LLM e o disparo do hook
exigem uma execução manual num projeto real (não dá pra automatizar em CI).

## ✅ UPDATE 2026-06-17 (objetivo master corrigido)

O foco do framework foi corrigido para **subagentes reais sempre**:
- `init.py` agora materializa um time mínimo em `.agent/team/`, cria `.agent/subagent.config.yaml` e espelha `.claude/agents/*.md`.
- `protocols/subagents.md` virou o contrato operacional: adapter nativo, Bali Runtime ou falha fechada.
- `templates/runtime/bali_runtime.py` e `templates/adapters/*.md` entram como caminho universal para Antigravity, Claude Code, Codex, OpenCode, Cursor, Gemini, Ollama e qualquer LLM/IDE futuro.
- README, AGENTS, templates e `verify_setup.py` não aceitam mais role-play de papéis no mesmo contexto como modo válido.
- A suíte subiu para 18 testes e valida que o setup físico já passa em `verify_setup.verify(...)`.

---

## O que FALTA pra ser 10 (itens 2→6 + e2e). Código pronto pra colar.

### ITEM 3 — Template `task.md` (rápido) — PARCIAL
✅ **`templates/task.md` JÁ foi criado e commitado** (commit `a7d84f6`). **Falta só a fiação:** (a) `init.py` copiar para `.agent/task.md`; (b) incluir no teste. Conteúdo do template já criado (referência):

**`templates/task.md`:**
```markdown
# 📋 Task Atual — {NOME_DO_PROJETO}

> Checklist de progresso da tarefa em andamento. Orchestrator e Planner mantêm vivo.
> Leia junto com `working-context.md` para retomar sem re-indexar o repositório.

## 🎯 Tarefa atual
- **Descrição:** {DESCRICAO_DA_TAREFA}
- **Classe (triagem):** {trivial | pequeno | medio | grande}
- **Especialista(s):** {spec-...}

## ✅ Checklist
- [ ] {passo 1}

## 🚧 Bloqueios
- nenhum

## 📝 Notas de handoff
- {resumo do que foi feito e o que falta}
```

Em `init.py`, dentro de `initialize_project`, copiar para `.agent/task.md` se não existir (mesmo padrão do `working-context.md`):
```python
    dest_task = os.path.join(agent_dir, "task.md")
    if not os.path.exists(dest_task):
        src_task = os.path.join(src_dir, "templates", "task.md")
        if os.path.exists(src_task):
            shutil.copy2(src_task, dest_task)
            print("[x] Checklist de tarefa criado: .agent/task.md")
```
E em `tests/test_base_structure.py::test_templates_exist`, adicionar `"templates/task.md"` à lista esperada.

### ITEM 2 — `verify_setup.py` determinístico (o que mais vale)
Script que confirma que o Setup Agent realmente montou o time + adaptadores. Criar:

**`templates/verify_setup.py`:**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador deterministico do setup do time Bali-Agent.
Uso: python .agent/verify_setup.py  (rodar na raiz do projeto)
"""
import os
import sys
try:
    import yaml
except ImportError:
    yaml = None

def verify(project_root):
    """Retorna lista de problemas (strings). Lista vazia = setup OK."""
    problems = []
    agent_dir = os.path.join(project_root, ".agent")
    manifest = os.path.join(agent_dir, "subagent.config.yaml")
    if not os.path.isfile(manifest):
        problems.append("Manifesto ausente: .agent/subagent.config.yaml")
        return problems
    data = None
    if yaml is not None:
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            problems.append(f"Manifesto invalido (YAML): {e}")
    team_dir = os.path.join(agent_dir, "team")
    for member in ("orchestrator.md", "planner.md", "reviewer.md"):
        if not os.path.isfile(os.path.join(team_dir, member)):
            problems.append(f"Membro da espinha ausente: .agent/team/{member}")
    if os.path.isdir(team_dir):
        specs = [f for f in os.listdir(team_dir) if f.startswith("spec-") and f.endswith(".md")]
        if not specs:
            problems.append("Nenhum especialista gerado: .agent/team/spec-*.md")
    if not os.path.isfile(os.path.join(agent_dir, "working-context.md")):
        problems.append("Memoria de trabalho ausente: .agent/working-context.md")
    adapters = data.get("enforcement_adapters") or [] if isinstance(data, dict) else []
    checks = {
        "claude-code": [os.path.join(project_root, ".claude", "settings.json"),
                        os.path.join(agent_dir, "hooks", "claude_hook.py")],
        "cursor": [os.path.join(project_root, ".cursor", "rules", "subagent.mdc")],
        "gemini": [os.path.join(project_root, ".gemini", "settings.json")],
    }
    for adapter in adapters:
        for path in checks.get(adapter, []):
            if not os.path.exists(path):
                problems.append(f"Adaptador '{adapter}' incompleto: falta {os.path.relpath(path, project_root)}")
    return problems

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    problems = verify(root)
    if problems:
        print("[VERIFY-SETUP] Setup INCOMPLETO:")
        for p in problems:
            print(f"  [!] {p}")
        sys.exit(1)
    print("[VERIFY-SETUP] OK: time e adaptadores instalados corretamente.")
    sys.exit(0)

if __name__ == "__main__":
    main()
```
- Em `init.py`, copiar `templates/verify_setup.py` para `.agent/verify_setup.py` (chmod 0o755), igual ao `prevent_secrets.py`.
- Em `agents/_setup/AGENT.md` (passo 4), adicionar: "Ao final, rode `python .agent/verify_setup.py` e mostre o resultado ao usuário."
- Adicionar teste em `tests/test_base_structure.py`:
```python
def test_verify_setup_logic(tmp_path):
    import sys
    if str(REPO) not in sys.path:
        sys.path.append(str(REPO))
    from templates import verify_setup
    # 1. Sem .agent -> reporta problema
    assert verify_setup.verify(str(tmp_path))
    # 2. Setup completo -> zero problemas
    proj = tmp_path / "ok"; agent = proj / ".agent"; team = agent / "team"
    team.mkdir(parents=True)
    (agent / "subagent.config.yaml").write_text(
        "modo: operate\ntime:\n  espinha: [orchestrator, planner, reviewer]\nenforcement_adapters:\n  - claude-code\n", encoding="utf-8")
    for m in ("orchestrator.md","planner.md","reviewer.md","spec-x.md"):
        (team / m).write_text("x", encoding="utf-8")
    (agent / "working-context.md").write_text("x", encoding="utf-8")
    (agent / "hooks").mkdir(); (agent / "hooks" / "claude_hook.py").write_text("x", encoding="utf-8")
    (proj / ".claude").mkdir(); (proj / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    assert verify_setup.verify(str(proj)) == []
    # 3. Falta o hook -> reporta
    (agent / "hooks" / "claude_hook.py").unlink()
    assert any("claude-code" in p for p in verify_setup.verify(str(proj)))
```
- Em `test_templates_exist`, adicionar `"templates/verify_setup.py"`.

### ITEM 4 — `gemini-settings.json` (verificar chave)
Atual: `{"contextFiles": ["AGENTS.md"]}`. **Verificar na doc atual do Gemini CLI** se a chave correta é `contextFileName` (string única) em vez de `contextFiles` (array). Pesquisar "gemini cli settings.json contextFileName" no repo `google-gemini/gemini-cli`. Ajustar `templates/gemini-settings.json` conforme. (Suspeita forte: deve ser `"contextFileName": "AGENTS.md"`.)

### ITEM 5 — CI (rápido)
Criar **`.github/workflows/tests.yml`:**
```yaml
name: tests
on: [push, pull_request]
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: pip install -r requirements-dev.txt
      - run: python -m pytest -q
```

### ITEM 1 — Prova end-to-end (o que vale o ponto final)
Os testes validam estrutura/instalador/segredo, mas **não** o comportamento real do time. Falta:
1. Rodar `python init.py` apontando para um projeto-exemplo (ex: um Next.js+Supabase de mentira).
2. No chat de um LLM, mandar "Setup do time" e deixar o Setup Agent gerar `.agent/team/` + adaptadores.
3. Rodar `python .agent/verify_setup.py` e confirmar OK.
4. Confirmar no Claude Code que o hook `UserPromptSubmit` realmente dispara (ver a constituição re-injetada).
5. Documentar esse dry-run em `examples/` (ex: `examples/dry-run-nextjs-supabase.md`).

## Como continuar (resumo)
1. `git checkout fix/v2-acabamento`
2. Fazer itens 3 → 2 → 5 (rápidos), 4 (verificar chave), 1 (e2e).
3. `python -m pytest tests/ -v` (manter verde).
4. Commit incremental por item. Push no `fix/v2-acabamento`. Abrir PR pra `main`.
