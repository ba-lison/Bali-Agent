# Bali-Agent v2 — Plano 1: Fundação (reorg + espinha + protocolos + templates)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestruturar o framework Bali-Agent para o modelo híbrido — criar a espinha fixa (`_spine`: orchestrator, planner, reviewer), o protocolo de roteamento, e os templates de constituição e manifesto — deixando uma base internamente consistente, validada por testes.

**Architecture:** O framework é majoritariamente conteúdo markdown (definições de agentes, protocolos, templates) mais um instalador Python (`init.py`). Esta fundação reposiciona os agentes existentes numa "espinha" (`agents/_spine/`), adiciona o protocolo de roteamento que faz qualquer tarefa passar pelo time, e cria os dois templates que o Setup Agent (Plano 2) vai materializar no projeto do usuário: a constituição (`project-AGENTS.md`) e o manifesto (`subagent.config.yaml`). A validação é feita por um harness pytest que checa a estrutura e a sanidade do YAML.

**Tech Stack:** Markdown (conteúdo dos agentes/protocolos), YAML (manifesto), Python 3 + pytest + PyYAML (harness de validação).

**Spec de referência:** [`docs/superpowers/specs/2026-06-17-bali-agent-v2-design.md`](../specs/2026-06-17-bali-agent-v2-design.md)

**Escopo deste plano (Plano 1):** seções 5.1 (espinha), 4 (constituição/manifesto como templates), e o protocolo de routing da seção 5.3/5.4. **Fora deste plano:** Setup Agent + `_specialists` (Plano 2); evolução do `init.py` + adaptadores de enforcement (Plano 3). Os agentes do modo greenfield (`discovery/`, `prd-writer/`, `sdd-architect/`, `implementer/`) ficam intactos aqui — `implementer/` vira arquétipo de especialista só no Plano 2.

---

## Estrutura de arquivos (o que este plano cria/modifica)

**Cria:**
- `requirements-dev.txt` — deps de teste (pytest, pyyaml)
- `tests/__init__.py` — pacote de testes (vazio)
- `tests/test_base_structure.py` — validador estrutural do framework
- `agents/_spine/orchestrator/AGENT.md` — orquestrador evoluído (roteia QUALQUER tarefa, 2 modos)
- `agents/_spine/orchestrator/workflows/novo-projeto.md` — workflow greenfield (movido)
- `agents/_spine/planner/AGENT.md` — planejador (absorve o Task Decomposer)
- `agents/_spine/reviewer/AGENT.md` — revisor (movido)
- `agents/_spine/reviewer/checklists/pr-checklist.md` — movido
- `agents/_spine/reviewer/checklists/security-checklist.md` — movido
- `protocols/routing.md` — como rotear qualquer tarefa pelo time
- `templates/subagent.config.yaml` — manifesto do time (template)
- `templates/project-AGENTS.md` — constituição que vai p/ a raiz do projeto (template)

**Modifica:**
- `AGENTS.md` (raiz) — ponto de entrada da base aponta p/ a nova estrutura `_spine` e o Setup Agent
- `README.md` — atualiza o bloco de estrutura de diretórios

**Remove (via git mv para `_spine`):**
- `agents/orchestrator/`, `agents/task-decomposer/`, `agents/reviewer/`

---

## Task 1: Harness de validação (test infra + primeiro teste falhando)

**Files:**
- Create: `requirements-dev.txt`
- Create: `tests/__init__.py`
- Create: `tests/test_base_structure.py`

- [ ] **Step 1: Criar `requirements-dev.txt`**

```
pytest>=8.0
PyYAML>=6.0
```

- [ ] **Step 2: Instalar as deps de teste**

Run: `python -m pip install -r requirements-dev.txt`
Expected: instala pytest e PyYAML sem erro (ou "already satisfied").

- [ ] **Step 3: Criar `tests/__init__.py` vazio**

```python
```

(arquivo vazio — só marca o diretório como pacote)

- [ ] **Step 4: Escrever o primeiro teste (espinha existe) — vai FALHAR**

Create `tests/test_base_structure.py`:

```python
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def test_spine_files_exist():
    expected = [
        "agents/_spine/orchestrator/AGENT.md",
        "agents/_spine/planner/AGENT.md",
        "agents/_spine/reviewer/AGENT.md",
    ]
    missing = [f for f in expected if not (REPO / f).is_file()]
    assert not missing, f"arquivos da espinha ausentes: {missing}"
```

- [ ] **Step 5: Rodar e confirmar que FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_spine_files_exist -v`
Expected: FAIL — `arquivos da espinha ausentes: [...]` (a espinha ainda não existe).

- [ ] **Step 6: Commit**

```bash
git add requirements-dev.txt tests/__init__.py tests/test_base_structure.py
git commit -m "test: harness de validação estrutural do framework"
```

---

## Task 2: Mover e evoluir o Orchestrator para a espinha

**Files:**
- Move: `agents/orchestrator/` → `agents/_spine/orchestrator/` (preserva `workflows/novo-projeto.md`)
- Modify (rewrite): `agents/_spine/orchestrator/AGENT.md`
- Test: `tests/test_base_structure.py` (adiciona `test_orchestrator_routes_any_task`)

- [ ] **Step 1: Adicionar teste do orquestrador (conteúdo normativo) — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_orchestrator_routes_any_task():
    txt = _read("agents/_spine/orchestrator/AGENT.md")
    # Deve operar nos dois modos e rotear QUALQUER pedido pelo time
    for marker in ["Modo Operate", "Modo Greenfield", ".agent/subagent.config.yaml",
                   "nunca trabalha sozinho", "protocols/routing.md"]:
        assert marker in txt, f"marcador ausente no orchestrator: {marker!r}"
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_orchestrator_routes_any_task -v`
Expected: FAIL — arquivo ainda não existe no novo caminho.

- [ ] **Step 3: Mover o diretório do orchestrator para a espinha**

```bash
git mv agents/orchestrator agents/_spine/orchestrator
```

- [ ] **Step 4: Reescrever `agents/_spine/orchestrator/AGENT.md` com o conteúdo evoluído**

Substituir TODO o conteúdo do arquivo por:

```markdown
# 🎯 Orchestrator — Espinha do Bali-Agent

> **Tipo:** Agente de espinha (sempre presente)
> **Versão:** 2.0.0

## Papel

Você é o **Orchestrator**. Você NÃO executa tarefas técnicas diretamente — você
**roteia QUALQUER pedido** (bug, feature, dúvida, refactor, investigação) para os
especialistas do time e garante que toda entrega passe pelo Reviewer. Você **nunca
trabalha sozinho** e nunca deixa outro agente trabalhar sozinho.

## Primeira ação, sempre

1. Leia `.agent/subagent.config.yaml` (o manifesto do time deste projeto).
2. Identifique o `modo` do projeto (`operate` ou `greenfield`) e a lista de especialistas.
3. Siga `protocols/routing.md` para decidir o roteamento da tarefa atual.

## Modo Operate (projeto já em andamento)

Para cada pedido do usuário:
1. **Triagem** (ver `protocols/routing.md`): classifique o tamanho do pedido.
2. **Roteie** para o(s) especialista(s) cujo `escopo` casa com a tarefa.
3. Tarefas não-triviais passam pelo **Planner** antes da execução.
4. **Toda** entrega passa pelo **Reviewer** antes de você concluir.
5. Comunique ao usuário qual caminho o time seguiu.

## Modo Greenfield (projeto do zero)

Quando o manifesto indica `modo: greenfield`, conduza o pipeline SDLC clássico
descrito em `workflows/novo-projeto.md`:
Discovery → PRD → SDD → Decomposição (Planner) → Implementação → Review,
com os gates de aprovação humana de `protocols/approval-gates.md`.

## Regras invioláveis

1. **NUNCA** responda um pedido sozinho sem rotear pelo time.
2. **NUNCA** conclua uma entrega sem passar pelo Reviewer.
3. **NUNCA** invente requisitos — na dúvida, pergunte.
4. **SEMPRE** ajuste o esforço ao tamanho do pedido (processo proporcional — ver routing).
5. **SEMPRE** comunique o roteamento ao usuário em 1-2 linhas.

## Integração com a espinha

| Agente | Quando invocar | Arquivo |
|--------|----------------|---------|
| **Planner** | Decompor pedido não-trivial em plano/tasks | `agents/_spine/planner/AGENT.md` |
| **Reviewer** | Antes de concluir QUALQUER entrega | `agents/_spine/reviewer/AGENT.md` |
| **Especialistas** | Execução técnica por stack | `.agent/team/spec-*.md` |
```

- [ ] **Step 5: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_orchestrator_routes_any_task -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: move orchestrator p/ _spine e evolui p/ roteamento de qualquer tarefa"
```

---

## Task 3: Criar o Planner na espinha (absorve o Task Decomposer)

**Files:**
- Move: `agents/task-decomposer/` → `agents/_spine/planner/`
- Modify (rewrite): `agents/_spine/planner/AGENT.md`
- Test: `tests/test_base_structure.py` (adiciona `test_planner_decomposes`)

- [ ] **Step 1: Adicionar teste do Planner — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_planner_decomposes():
    txt = _read("agents/_spine/planner/AGENT.md")
    for marker in ["Planner", "tasks atômicas", "critério de conclusão"]:
        assert marker in txt, f"marcador ausente no planner: {marker!r}"
    # garante que o antigo caminho não sobrou
    assert not (REPO / "agents/task-decomposer").exists(), "task-decomposer deveria ter virado _spine/planner"
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_planner_decomposes -v`
Expected: FAIL.

- [ ] **Step 3: Mover o diretório**

```bash
git mv agents/task-decomposer agents/_spine/planner
```

- [ ] **Step 4: Reescrever `agents/_spine/planner/AGENT.md`**

Substituir TODO o conteúdo por:

```markdown
# 📋 Planner — Espinha do Bali-Agent

> **Tipo:** Agente de espinha (sempre presente)
> **Versão:** 2.0.0

## Papel

Você é o **Planner**. Recebe um pedido (do Orchestrator) e o decompõe em **tasks
atômicas, ordenadas e verificáveis** antes de qualquer execução. No modo greenfield,
você atua sobre o SDD aprovado; no modo operate, sobre o pedido direto do usuário.

## Critérios de uma boa task

- ≤ 4 horas estimadas (uma sessão).
- **Critério de conclusão** verificável e explícito.
- Dependências mapeadas (o que precisa vir antes).
- Marcada como paralelizável ou sequencial.
- Prioridade (P0/P1/P2).

## Saída

Uma lista priorizada de tasks. Em greenfield, grave em `output/{projeto}/tasks.md`
seguindo `templates/tasks.md`. Em operate, devolva a lista ao Orchestrator para
despacho aos especialistas.

## Regras

1. **NUNCA** crie task sem critério de conclusão verificável.
2. **SEMPRE** mapeie dependências antes de ordenar.
3. **SEMPRE** prefira tasks pequenas a tasks grandes.
```

- [ ] **Step 5: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_planner_decomposes -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: task-decomposer vira Planner na espinha"
```

---

## Task 4: Mover o Reviewer para a espinha

**Files:**
- Move: `agents/reviewer/` → `agents/_spine/reviewer/` (preserva `checklists/`)
- Test: `tests/test_base_structure.py` (adiciona `test_reviewer_in_spine`)

- [ ] **Step 1: Adicionar teste do Reviewer — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_reviewer_in_spine():
    assert (REPO / "agents/_spine/reviewer/AGENT.md").is_file()
    assert (REPO / "agents/_spine/reviewer/checklists/pr-checklist.md").is_file()
    assert (REPO / "agents/_spine/reviewer/checklists/security-checklist.md").is_file()
    assert not (REPO / "agents/reviewer").exists(), "reviewer deveria estar em _spine"
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_reviewer_in_spine -v`
Expected: FAIL.

- [ ] **Step 3: Mover o diretório (com os checklists)**

```bash
git mv agents/reviewer agents/_spine/reviewer
```

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_reviewer_in_spine -v`
Expected: PASS (o conteúdo do reviewer é mantido como está; só mudou de lugar).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: move reviewer (com checklists) p/ _spine"
```

---

## Task 5: Atualizar referências de caminho no workflow greenfield

**Files:**
- Modify: `agents/_spine/orchestrator/workflows/novo-projeto.md`
- Test: `tests/test_base_structure.py` (adiciona `test_no_stale_agent_paths`)

- [ ] **Step 1: Adicionar teste de "sem caminhos antigos" — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_no_stale_agent_paths():
    # nenhum arquivo do framework deve apontar para os caminhos antigos da espinha
    stale = ["agents/orchestrator/", "agents/task-decomposer/", "agents/reviewer/"]
    offenders = []
    for md in (REPO / "agents").rglob("*.md"):
        txt = md.read_text(encoding="utf-8")
        for s in stale:
            if s in txt:
                offenders.append(f"{md.relative_to(REPO)} -> {s}")
    assert not offenders, f"referências a caminhos antigos: {offenders}"
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_no_stale_agent_paths -v`
Expected: FAIL — `novo-projeto.md` referencia `../../discovery/...` e o antigo `task-decomposer`.

- [ ] **Step 3: Corrigir os caminhos em `novo-projeto.md`**

Abra `agents/_spine/orchestrator/workflows/novo-projeto.md` e aplique:
- Trocar qualquer ocorrência de `agents/task-decomposer/` por `agents/_spine/planner/`.
- Trocar o nome de agente "Task Decomposer" por "Planner" no texto.
- Os links relativos para `discovery`, `prd-writer`, `sdd-architect` agora sobem dois níveis a mais (de `agents/orchestrator/workflows/` para `agents/_spine/orchestrator/workflows/`): trocar `../../discovery/` por `../../../discovery/` (e idem para `prd-writer`, `sdd-architect`).

> Nota: estes agentes greenfield continuam em `agents/discovery/`, `agents/prd-writer/`, `agents/sdd-architect/` (não foram movidos neste plano).

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_no_stale_agent_paths -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix: atualiza caminhos do workflow greenfield p/ a nova estrutura _spine"
```

---

## Task 6: Protocolo de roteamento (`protocols/routing.md`)

**Files:**
- Create: `protocols/routing.md`
- Test: `tests/test_base_structure.py` (adiciona `test_routing_protocol_sections`)

- [ ] **Step 1: Adicionar teste do protocolo — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_routing_protocol_sections():
    txt = _read("protocols/routing.md")
    for h in ["# Protocolo de Roteamento", "## Triagem", "## Processo proporcional",
              "## Modo Operate", "## Modo Greenfield"]:
        assert h in txt, f"seção ausente em routing.md: {h!r}"
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_routing_protocol_sections -v`
Expected: FAIL.

- [ ] **Step 3: Criar `protocols/routing.md`**

```markdown
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
```

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_routing_protocol_sections -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: protocolo de roteamento (triagem + processo proporcional)"
```

---

## Task 7: Template do manifesto (`templates/subagent.config.yaml`)

**Files:**
- Create: `templates/subagent.config.yaml`
- Test: `tests/test_base_structure.py` (adiciona `test_manifest_template_valid`)

- [ ] **Step 1: Adicionar teste do manifesto — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_manifest_template_valid():
    data = yaml.safe_load(_read("templates/subagent.config.yaml"))
    assert isinstance(data, dict)
    assert data.get("modo") in ("operate", "greenfield")
    assert "espinha" in data["time"]
    assert {"orchestrator", "planner", "reviewer"}.issubset(set(data["time"]["espinha"]))
    assert "enforcement_adapters" in data
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_manifest_template_valid -v`
Expected: FAIL.

- [ ] **Step 3: Criar `templates/subagent.config.yaml`**

```yaml
# Manifesto do time Bali-Agent (gerado pelo Setup Agent).
# Este arquivo é a fonte de verdade do time montado para o projeto.
versao_base: "2.0.0"
projeto: nome-do-projeto
modo: operate            # operate | greenfield
criado_em: "AAAA-MM-DDTHH:MM:SS-03:00"
stack_detectada:
  - linguagem: exemplo-typescript
    framework: exemplo-next.js
    sinais: ["package.json"]
nao_mexer:
  - "exemplo: migrations legadas em db/legacy/"
time:
  espinha:
    - orchestrator
    - planner
    - reviewer
  especialistas:
    - id: spec-exemplo
      arquivo: .agent/team/spec-exemplo.md
      escopo: "descreva o escopo do especialista"
enforcement_adapters:
  - claude-code          # PADRÃO: re-injeta a constituição a cada turno via hook
```

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_manifest_template_valid -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: template do manifesto subagent.config.yaml"
```

---

## Task 8: Template da constituição (`templates/project-AGENTS.md`)

**Files:**
- Create: `templates/project-AGENTS.md`
- Test: `tests/test_base_structure.py` (adiciona `test_constitution_template`)

- [ ] **Step 1: Adicionar teste da constituição — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_constitution_template():
    txt = _read("templates/project-AGENTS.md").lower()
    assert "nunca trabalha sozinho" in txt
    assert ".agent/subagent.config.yaml" in txt
    assert ".agent/team/" in txt
    assert "reviewer" in txt
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_constitution_template -v`
Expected: FAIL.

- [ ] **Step 3: Criar `templates/project-AGENTS.md`**

```markdown
# AGENTS.md — Constituição do projeto {NOME_DO_PROJETO}

> **Modo de operação permanente.** Qualquer LLM/assistente que abrir este projeto
> DEVE operar como o time Bali-Agent. Este arquivo é lido automaticamente.

## Regra fundamental (não-opcional)

Para **QUALQUER** pedido — bug, feature, dúvida, refactor, investigação — você:

1. Assume o papel de **Orchestrator**.
2. Lê o manifesto do time em `.agent/subagent.config.yaml`.
3. Roteia a tarefa para os especialistas em `.agent/team/`, seguindo `.agent/protocols/routing.md`.
4. **Nunca trabalha sozinho.** Toda entrega passa pelo **Reviewer** antes de concluir.

O esforço é **proporcional** ao pedido (ver `routing.md`): pergunta trivial → resposta
rápida + sanity-check; feature → plano → execução → review. "Nunca solo" não significa
"sempre burocrático".

## Time deste projeto

Os papéis e especialistas estão definidos em `.agent/team/`. A espinha fixa é:
**Orchestrator**, **Planner**, **Reviewer**. Os especialistas variam conforme a stack
(ver o manifesto).

## Como começar

Mande seu pedido normalmente. O Orchestrator faz a triagem e roteia. Se faltar um
especialista para o que você pediu, ele avisa e sugere rodar o setup novamente.
```

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_constitution_template -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: template da constituição (project-AGENTS.md)"
```

---

## Task 9: Atualizar o `AGENTS.md` da base (ponto de entrada)

**Files:**
- Modify: `AGENTS.md` (raiz do repo)
- Test: `tests/test_base_structure.py` (adiciona `test_base_entrypoint_points_to_spine`)

- [ ] **Step 1: Adicionar teste do ponto de entrada — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_base_entrypoint_points_to_spine():
    txt = _read("AGENTS.md")
    assert "agents/_spine/orchestrator/AGENT.md" in txt
    assert "agents/_spine/planner/AGENT.md" in txt
    assert "agents/_spine/reviewer/AGENT.md" in txt
    # não pode mais referenciar NENHUM caminho antigo (prefixo de diretório),
    # incluindo a seção 7 que cita agents/reviewer/checklists/...
    for stale in ["agents/orchestrator/", "agents/task-decomposer/", "agents/reviewer/"]:
        assert stale not in txt, f"caminho antigo ainda no AGENTS.md: {stale}"
```

> Nota: `agents/_spine/reviewer/` NÃO contém a substring `agents/reviewer/`, então não há
> falso-positivo com os caminhos novos.

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_base_entrypoint_points_to_spine -v`
Expected: FAIL — a tabela "Mapa de Agentes" ainda usa os caminhos antigos.

- [ ] **Step 3: Editar a tabela "Mapa de Agentes" no `AGENTS.md`**

Na seção `## 2. Mapa de Agentes`, substituir as linhas dos caminhos antigos pelos novos:
- `agents/orchestrator/AGENT.md` → `agents/_spine/orchestrator/AGENT.md`
- `agents/task-decomposer/AGENT.md` → `agents/_spine/planner/AGENT.md` (e renomear o papel "Task Decomposer" → "Planner")
- `agents/reviewer/AGENT.md` → `agents/_spine/reviewer/AGENT.md`

Também na seção `## 7. Referência Rápida` (ou onde aparecer): trocar
`agents/reviewer/checklists/pr-checklist.md` → `agents/_spine/reviewer/checklists/pr-checklist.md`.

Os agentes greenfield (`discovery`, `prd-writer`, `sdd-architect`, `implementer`) mantêm seus caminhos atuais.

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_base_entrypoint_points_to_spine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "docs: AGENTS.md da base aponta para a nova estrutura _spine"
```

---

## Task 10: Atualizar o bloco de estrutura no `README.md`

**Files:**
- Modify: `README.md`
- Test: `tests/test_base_structure.py` (adiciona `test_readme_structure_mentions_spine`)

- [ ] **Step 1: Adicionar teste do README — vai FALHAR**

Append em `tests/test_base_structure.py`:

```python
def test_readme_structure_mentions_spine():
    txt = _read("README.md")
    assert "_spine/" in txt, "README deve descrever a nova pasta _spine/"
    assert "protocols/routing.md" in txt or "routing.md" in txt
```

- [ ] **Step 2: Rodar e confirmar FALHA**

Run: `python -m pytest tests/test_base_structure.py::test_readme_structure_mentions_spine -v`
Expected: FAIL.

- [ ] **Step 3: Atualizar o bloco "Estrutura de Diretórios" do `README.md`**

No bloco de árvore de diretórios em `## 📁 Estrutura de Diretórios`, refletir:
- `agents/_spine/{orchestrator,planner,reviewer}/` (espinha fixa)
- `agents/{discovery,prd-writer,sdd-architect,implementer}/` (modo greenfield)
- `protocols/routing.md` (novo)
- `templates/{subagent.config.yaml,project-AGENTS.md}` (novos)

Adicionar uma frase curta: "A espinha (`_spine`) está sempre presente; os agentes de
`discovery/prd-writer/sdd-architect` rodam no modo greenfield."

- [ ] **Step 4: Rodar e confirmar PASSA**

Run: `python -m pytest tests/test_base_structure.py::test_readme_structure_mentions_spine -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "docs: README reflete a nova estrutura (_spine, routing, templates)"
```

---

## Task 11: Validação final completa

**Files:**
- (nenhum novo — roda toda a suíte)

- [ ] **Step 1: Rodar a suíte inteira**

Run: `python -m pytest tests/ -v`
Expected: TODOS os testes PASSAM (test_spine_files_exist, test_orchestrator_routes_any_task, test_planner_decomposes, test_reviewer_in_spine, test_no_stale_agent_paths, test_routing_protocol_sections, test_manifest_template_valid, test_constitution_template, test_base_entrypoint_points_to_spine, test_readme_structure_mentions_spine).

- [ ] **Step 2: Conferência manual rápida da árvore**

Run: `git ls-files agents/_spine protocols templates | sort`
Expected: vê `agents/_spine/orchestrator/AGENT.md`, `agents/_spine/planner/AGENT.md`, `agents/_spine/reviewer/AGENT.md` (+ checklists e workflow), `protocols/routing.md`, `templates/subagent.config.yaml`, `templates/project-AGENTS.md`.

- [ ] **Step 3: Commit final (se houver ajuste)**

```bash
git add -A
git commit -m "chore: validação final da fundação v2 (suíte verde)" --allow-empty
```

---

## Próximos planos (fora deste)

- **Plano 2 — Setup Agent + especialistas:** `agents/_setup/` (AGENT.md, stack-detection.md, interview.md), `agents/_specialists/` (arquétipos + `_TEMPLATE.md`), repositiona `implementer/` como arquétipo, e um exemplo de "dry-run" do setup.
- **Plano 3 — Installer + adaptadores:** refatora `init.py` em funções testáveis (instala em `.agent/`, idempotente), e gera os 4 adaptadores de enforcement (Claude Code hook+agents, Cursor `.mdc`, Gemini `settings.json`, Codex `AGENTS.md`).
