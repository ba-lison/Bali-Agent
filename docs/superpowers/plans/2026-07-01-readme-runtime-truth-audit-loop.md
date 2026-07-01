# README Runtime Truth Audit Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the senior audit findings into an executable honesty loop: capabilities become structured data, README claims are checked against that data, and the agent team iterates until the audit gate passes.

**Architecture:** Keep the current Bali-Agent runtime intact and add an audit layer around it. A small capability catalog becomes the source of truth, `capability-report` renders human and JSON output from that catalog, `audit-readme` checks README claim text against explicit capability ids, and a final evaluation script runs tests plus both audits as a repeatable gate.

**Tech Stack:** Python 3.11+, stdlib only, `pyyaml>=6.0`, `pytest`, current `bali_agent.cli` command style, existing `tests/` fixture patterns.

## Global Constraints

- No new runtime dependency beyond the current `pyyaml>=6.0`.
- Keep `capability-report` non-gating by default; add a separate `--strict` or `audit-readme` gate for failures.
- Do not implement parallel execution, universal native isolation, or mandatory multi-model execution in this plan.
- README must describe delivered, contract-dependent, host-dependent, and not-delivered capabilities without implying universal autonomy.
- Every claim that sounds like a capability must map to a capability id or be rewritten as product direction.
- All new commands must work with `bali --root <project> ...`.
- Full validation target: `python -m pytest -q`, `python -m py_compile ...`, `bali --root <temp> capability-report --json`, `bali --root <repo> audit-readme`, and final senior re-audit.

---

## Delivery Team

Use this fixed agent team during execution. The orchestrator cycles through the team until the evaluation gate passes.

| Agent | Responsibility | Must return |
|---|---|---|
| `orchestrator` | Owns the loop, assigns tasks, decides whether another pass is needed. | Current pass status, blockers, next task owner. |
| `docs-truth-auditor` | Reviews README and docs for overclaims. | List of exact lines/sections to rewrite with claim ids. |
| `runtime-contract-engineer` | Builds structured capability catalog and CLI outputs. | Code changes, typed interfaces, command examples. |
| `cli-test-engineer` | Writes failing tests first for every command and output mode. | Test names, expected failures, final pass output. |
| `adapter-host-skeptic` | Challenges every adapter/native-host claim. | Host-dependent classifications and wording changes. |
| `security-risk-reviewer` | Ensures audit commands do not execute LLMs, shell, secrets, or host tools. | Security review notes and tests if needed. |
| `product-copy-editor` | Rewrites README in plain, honest language. | Replacement copy tied to capability ids. |
| `qa-evaluator` | Runs final evaluation gate and records evidence. | Command outputs and pass/fail decision. |
| `memory-curator` | Updates project memory after a passed loop. | Curated summary of final capability truth. |

## Iteration Loop

Each pass follows this sequence:

1. `orchestrator` opens a pass and assigns one task.
2. The task owner writes/updates tests first.
3. The task owner implements the smallest code/doc change.
4. `qa-evaluator` runs the task-specific command.
5. `docs-truth-auditor` or `adapter-host-skeptic` reviews any claim wording touched by the task.
6. `qa-evaluator` runs the final gate.
7. If final gate fails, `orchestrator` creates a new pass only for the failed category.
8. Stop only when the final gate passes twice in a row: once immediately after implementation, once after a clean fresh shell run.

Final gate:

```powershell
python -m pytest -q
python -m py_compile bali_agent\cli.py bali_agent\capabilities.py bali_agent\readme_audit.py bali_agent\templates\runtime\bali_runtime.py
$tmp = Join-Path $env:TEMP ('bali-final-audit-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
python -m bali_agent.cli --root $tmp init
python -m bali_agent.cli --root $tmp verify
python -m bali_agent.cli --root $tmp capability-report --json
python -m bali_agent.cli --root $tmp audit-readme --readme README.md --strict
Remove-Item -LiteralPath $tmp -Recurse -Force
```

Expected final result:

```text
pytest: passed
py_compile: passed
verify: OK
capability-report --json: valid JSON with delivered/contract_dependent/host_dependent/not_delivered
audit-readme --strict: no unsupported claims
```

## File Structure

- Create `bali_agent/capabilities.py`: source-of-truth catalog and project inspection functions.
- Create `bali_agent/readme_audit.py`: README claim scanner and strict audit result.
- Modify `bali_agent/cli.py`: wire `capability-report --json --strict` and new `audit-readme` command.
- Modify `README.md`: add capability ids, tighten overclaims, clarify host/runner limits.
- Modify `docs/SDD-runtime-honesty-and-delivery.md`: document the new catalog and README audit gate.
- Modify `docs/PLAN-runtime-honesty-and-delivery.md`: record scope extension.
- Modify `tests/test_cli.py`: CLI integration coverage for JSON/strict/readme audit.
- Create `tests/test_capabilities.py`: catalog-level unit tests.
- Create `tests/test_readme_audit.py`: README claim scanner tests.

---

### Task 1: Capability Catalog Source Of Truth

**Files:**
- Create: `bali_agent/capabilities.py`
- Test: `tests/test_capabilities.py`

**Interfaces:**
- Produces: `CapabilityStatus = Literal["delivered", "contract_dependent", "host_dependent", "not_delivered"]`
- Produces: `Capability` dataclass with `id: str`, `title: str`, `status: str`, `available: bool`, `detail: str`, `evidence: list[str]`
- Produces: `build_capability_report(root: Path) -> dict[str, list[Capability]]`
- Consumes: `bali_agent.core.agent_manager.verify(root)` and `bali_agent.adapters.ADAPTERS`

- [ ] **Step 1: Write failing tests**

Create `tests/test_capabilities.py`:

```python
from pathlib import Path

from bali_agent.capabilities import build_capability_report


def test_capability_report_has_stable_sections(temp_project_dir):
    report = build_capability_report(temp_project_dir)

    assert set(report) == {
        "delivered",
        "contract_dependent",
        "host_dependent",
        "not_delivered",
    }
    assert any(item.id == "cli.installed_structure" for item in report["delivered"])
    assert any(item.id == "runtime.dynamic_routing_plan" for item in report["contract_dependent"])
    assert any(item.id == "runtime.parallel_execution" for item in report["not_delivered"])


def test_capability_catalog_marks_parallel_as_not_delivered(temp_project_dir):
    report = build_capability_report(temp_project_dir)
    parallel = next(item for item in report["not_delivered"] if item.id == "runtime.parallel_execution")

    assert parallel.available is False
    assert "sequential" in parallel.detail
    assert "max_parallel 1" in parallel.detail
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_capabilities.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'bali_agent.capabilities'
```

- [ ] **Step 3: Implement minimal catalog**

Create `bali_agent/capabilities.py`:

```python
# -*- coding: utf-8 -*-
"""Structured capability catalog for Bali-Agent operational audits."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

from bali_agent.adapters import ADAPTERS
from bali_agent.core.agent_manager import verify

CapabilityStatus = Literal["delivered", "contract_dependent", "host_dependent", "not_delivered"]


@dataclass(frozen=True)
class Capability:
    id: str
    title: str
    status: CapabilityStatus
    available: bool
    detail: str
    evidence: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def build_capability_report(root: Path) -> dict[str, list[Capability]]:
    agent_root = root / ".agent"
    runtime_script = agent_root / "runtime" / "bali_runtime.py"
    manifest = agent_root / "subagent.config.yaml"
    memory = agent_root / "memory.md"
    output_runtime = agent_root / "output" / "runtime"
    runtime_manifests = list(output_runtime.glob("*/run_manifest.json")) if output_runtime.is_dir() else []
    verify_problems = verify(root)

    delivered = [
        Capability("cli.installed_structure", "CLI installed structure", "delivered", agent_root.is_dir(), ".agent directory", [".agent/"]),
        Capability(
            "team.core_manifest",
            "Core team and manifest",
            "delivered",
            not verify_problems and manifest.is_file(),
            "verify passes" if not verify_problems else "; ".join(verify_problems[:3]),
            [".agent/subagent.config.yaml", ".agent/team/"],
        ),
        Capability("runtime.script", "Bali Runtime script", "delivered", runtime_script.is_file(), ".agent/runtime/bali_runtime.py", [".agent/runtime/bali_runtime.py"]),
        Capability("memory.curated_file", "Curated memory file", "delivered", memory.is_file(), ".agent/memory.md", [".agent/memory.md"]),
        Capability(
            "runtime.manifests",
            "Runtime manifests",
            "delivered",
            bool(runtime_manifests),
            "run_manifest.json found" if runtime_manifests else "run_manifest.json not found",
            [".agent/output/runtime/*/run_manifest.json"],
        ),
    ]

    contract_dependent = [
        Capability("runtime.native_or_fallback", "Native subagent orchestration", "contract_dependent", runtime_script.is_file(), "requires native adapter or Bali Runtime", [".agent/runtime/bali_runtime.py"]),
        Capability("runtime.dynamic_routing_plan", "Dynamic routing plan", "contract_dependent", runtime_script.is_file(), "requires Orchestrator JSON routing_plan", ["bali_agent/templates/runtime/bali_runtime.py"]),
        Capability("runtime.reviewer_fail_closed", "Reviewer fail-closed gate", "contract_dependent", runtime_script.is_file(), "requires structured Reviewer JSON", ["bali_agent/templates/runtime/bali_runtime.py"]),
    ]

    host_dependent = []
    for name, adapter_cls in ADAPTERS.items():
        try:
            valid, problems = adapter_cls(root).verify()
            detail = "adapter verify passes" if valid else "; ".join(problems[:2])
        except Exception as exc:
            valid = False
            detail = str(exc)
        host_dependent.append(
            Capability(f"adapter.{name}", f"{name} native adapter", "host_dependent", valid, detail, ["bali_agent/adapters/"])
        )

    not_delivered = [
        Capability("runtime.parallel_execution", "Parallel agent execution", "not_delivered", False, "runtime requires execution_mode sequential and max_parallel 1", ["bali_agent/templates/runtime/bali_runtime.py"]),
        Capability("host.universal_native_isolation", "Guaranteed native isolation in every host", "not_delivered", False, "Bali materializes files; host executes native isolation", ["bali_agent/adapters/"]),
        Capability("model.mandatory_multi_model", "Mandatory multi-model execution", "not_delivered", False, "model_policy is declarative unless host/wrapper supports it", [".agent/subagent.config.yaml"]),
    ]

    return {
        "delivered": delivered,
        "contract_dependent": contract_dependent,
        "host_dependent": host_dependent,
        "not_delivered": not_delivered,
    }
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_capabilities.py -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Commit**

```powershell
git add bali_agent/capabilities.py tests/test_capabilities.py
git commit -m "feat: add capability catalog"
```

---

### Task 2: Capability Report JSON And Strict Mode

**Files:**
- Modify: `bali_agent/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `build_capability_report(root: Path) -> dict[str, list[Capability]]`
- Produces: `capability_report(root: Path, as_json: bool = False, strict: bool = False) -> int`
- Produces CLI flags: `bali --root <project> capability-report --json --strict`

- [ ] **Step 1: Write failing CLI tests**

Append to `tests/test_cli.py`:

```python
def test_capability_report_json_output(temp_project_dir, capsys):
    from bali_agent.cli import capability_report
    import json

    res = capability_report(temp_project_dir, as_json=True)

    assert res == 0
    data = json.loads(capsys.readouterr().out)
    assert "delivered" in data
    assert "not_delivered" in data
    assert any(item["id"] == "runtime.parallel_execution" for item in data["not_delivered"])


def test_capability_report_strict_fails_when_not_delivered_exists(temp_project_dir, capsys):
    from bali_agent.cli import capability_report

    res = capability_report(temp_project_dir, strict=True)

    assert res == 1
    assert "Parallel agent execution" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_cli.py::test_capability_report_json_output tests/test_cli.py::test_capability_report_strict_fails_when_not_delivered_exists -q
```

Expected:

```text
TypeError: capability_report() got an unexpected keyword argument 'as_json'
```

- [ ] **Step 3: Refactor `capability_report`**

In `bali_agent/cli.py`, import the catalog:

```python
from bali_agent.capabilities import build_capability_report
```

Replace the current `capability_report` function with:

```python
def capability_report(root: Path, as_json: bool = False, strict: bool = False) -> int:
    """Print an operational capability report without enforcing a setup gate by default."""
    report = build_capability_report(root)

    if as_json:
        print(json.dumps(
            {section: [item.to_dict() for item in items] for section, items in report.items()},
            indent=2,
            ensure_ascii=False,
        ))
    else:
        print("Bali Capability Report")
        print(f"Root: {root}")
        for section, items in report.items():
            title = section.replace("_", "-").title()
            print("")
            print(f"[{title}]")
            for item in items:
                if item.status == "not_delivered":
                    state = "not implemented"
                else:
                    state = "available" if item.available else "unavailable"
                print(f"- {item.title}: {state} ({item.detail})")

    if strict:
        unavailable_delivered = [item for item in report["delivered"] if not item.available]
        not_delivered = list(report["not_delivered"])
        return 1 if unavailable_delivered or not_delivered else 0
    return 0
```

Update parser registration:

```python
    capability = sub.add_parser("capability-report")
    capability.add_argument("--json", action="store_true", dest="as_json")
    capability.add_argument("--strict", action="store_true")
```

Update dispatch:

```python
    elif args.command == "capability-report":
        sys.exit(capability_report(root, as_json=args.as_json, strict=args.strict))
```

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
python -m pytest tests/test_cli.py::test_capability_report_json_output tests/test_cli.py::test_capability_report_strict_fails_when_not_delivered_exists -q
```

Expected:

```text
2 passed
```

- [ ] **Step 5: Backward compatibility test**

Run:

```powershell
python -m pytest tests/test_cli.py::test_capability_report_separates_delivered_contract_host_and_missing -q
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Commit**

```powershell
git add bali_agent/cli.py tests/test_cli.py
git commit -m "feat: add capability report json and strict modes"
```

---

### Task 3: README Claim Audit Command

**Files:**
- Create: `bali_agent/readme_audit.py`
- Modify: `bali_agent/cli.py`
- Test: `tests/test_readme_audit.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `ReadmeAuditFinding` dataclass with `line: int`, `severity: str`, `message: str`, `text: str`
- Produces: `audit_readme_text(text: str) -> list[ReadmeAuditFinding]`
- Produces: `audit_readme_command(readme_path: Path, strict: bool = False) -> int`
- CLI: `bali --root <project> audit-readme --readme README.md --strict`

- [ ] **Step 1: Write failing audit tests**

Create `tests/test_readme_audit.py`:

```python
from bali_agent.readme_audit import audit_readme_text


def test_readme_audit_flags_universal_native_isolation_claim():
    findings = audit_readme_text("Bali garante isolamento nativo em qualquer host.\n")

    assert findings
    assert findings[0].severity == "error"
    assert "host" in findings[0].message.lower()


def test_readme_audit_allows_qualified_host_dependent_claim():
    findings = audit_readme_text("Bali materializa arquivos, mas a execucao nativa depende do host.\n")

    assert findings == []


def test_readme_audit_flags_mandatory_multi_model_claim():
    findings = audit_readme_text("Bali sempre usa modelos diferentes por agente.\n")

    assert findings
    assert "multi-modelo" in findings[0].message.lower() or "modelo" in findings[0].message.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_readme_audit.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'bali_agent.readme_audit'
```

- [ ] **Step 3: Implement README scanner**

Create `bali_agent/readme_audit.py`:

```python
# -*- coding: utf-8 -*-
"""README claim scanner for unsupported Bali-Agent promises."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadmeAuditFinding:
    line: int
    severity: str
    message: str
    text: str


BLOCKED_PATTERNS = [
    (
        ("garante", "isolamento", "qualquer host"),
        "Do not claim guaranteed native isolation in every host; say native execution depends on the host or Bali Runtime.",
    ),
    (
        ("sempre", "modelos diferentes"),
        "Do not claim mandatory multi-modelo; model_policy is declarative unless the host or wrapper supports it.",
    ),
    (
        ("paralelismo real", "funcional"),
        "Do not claim real parallel execution; runtime currently requires sequential execution and max_parallel 1.",
    ),
    (
        ("autonomo completo",),
        "Do not claim complete autonomy; routing depends on LLM JSON contracts and host/runtime configuration.",
    ),
]

ALLOWING_QUALIFIERS = (
    "depende do host",
    "depende da ferramenta",
    "depende do adapter",
    "depende do runtime",
    "nao e promessa fechada",
    "nao garantido",
    "not delivered",
)


def _has_all(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(needle in lowered for needle in needles)


def _has_qualifier(text: str) -> bool:
    lowered = text.lower()
    return any(qualifier in lowered for qualifier in ALLOWING_QUALIFIERS)


def audit_readme_text(text: str) -> list[ReadmeAuditFinding]:
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _has_qualifier(line):
            continue
        for needles, message in BLOCKED_PATTERNS:
            if _has_all(line, needles):
                findings.append(ReadmeAuditFinding(line_number, "error", message, line.strip()))
    return findings


def audit_readme_file(path: Path) -> list[ReadmeAuditFinding]:
    return audit_readme_text(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Wire CLI command**

In `bali_agent/cli.py`, import:

```python
from bali_agent.readme_audit import audit_readme_file
```

Add parser:

```python
    audit_readme = sub.add_parser("audit-readme")
    audit_readme.add_argument("--readme", default="README.md")
    audit_readme.add_argument("--strict", action="store_true")
```

Add function:

```python
def audit_readme_command(root: Path, readme: str = "README.md", strict: bool = False) -> int:
    readme_path = Path(readme)
    if not readme_path.is_absolute():
        readme_path = root / readme_path
    if not readme_path.is_file():
        print(f"README nao encontrado: {readme_path}", file=sys.stderr)
        return 2

    findings = audit_readme_file(readme_path)
    if not findings:
        print("README audit OK: nenhuma promessa sem qualificacao encontrada.")
        return 0

    print("README audit encontrou promessas que precisam de ajuste:")
    for finding in findings:
        print(f"- line {finding.line}: {finding.message}")
        print(f"  texto: {finding.text}")
    return 1 if strict else 0
```

Add dispatch:

```python
    elif args.command == "audit-readme":
        sys.exit(audit_readme_command(root, readme=args.readme, strict=args.strict))
```

- [ ] **Step 5: Add CLI integration test**

Append to `tests/test_cli.py`:

```python
def test_audit_readme_command_strict_fails_on_unqualified_claim(tmp_path, capsys):
    from bali_agent.cli import audit_readme_command

    readme = tmp_path / "README.md"
    readme.write_text("Bali garante isolamento nativo em qualquer host.\n", encoding="utf-8")

    res = audit_readme_command(tmp_path, strict=True)

    assert res == 1
    assert "promessas" in capsys.readouterr().out


def test_audit_readme_command_passes_current_readme(capsys):
    from pathlib import Path
    from bali_agent.cli import audit_readme_command

    res = audit_readme_command(Path.cwd(), readme="README.md", strict=True)

    assert res == 0
    assert "README audit OK" in capsys.readouterr().out
```

- [ ] **Step 6: Run tests**

Run:

```powershell
python -m pytest tests/test_readme_audit.py tests/test_cli.py::test_audit_readme_command_strict_fails_on_unqualified_claim tests/test_cli.py::test_audit_readme_command_passes_current_readme -q
```

Expected:

```text
5 passed
```

- [ ] **Step 7: Commit**

```powershell
git add bali_agent/readme_audit.py bali_agent/cli.py tests/test_readme_audit.py tests/test_cli.py
git commit -m "feat: add readme promise audit"
```

---

### Task 4: README Rewrite With Capability IDs

**Files:**
- Modify: `README.md`
- Test: `tests/test_readme_audit.py`

**Interfaces:**
- Consumes: capability ids from `bali_agent/capabilities.py`
- Produces: README sections that reference capability ids in comments or text labels

- [ ] **Step 1: Add README coverage test**

Append to `tests/test_readme_audit.py`:

```python
from pathlib import Path


def test_current_readme_names_critical_capability_limits():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "runtime.parallel_execution" in text
    assert "host.universal_native_isolation" in text
    assert "model.mandatory_multi_model" in text
    assert "BALI_SUBAGENT_RUNNER" in text
    assert "routing_plan" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_readme_audit.py::test_current_readme_names_critical_capability_limits -q
```

Expected:

```text
AssertionError
```

- [ ] **Step 3: Rewrite critical README copy**

In `README.md`, adjust the opening paragraph to:

```markdown
Bali-Agent e um kit CLI/runtime para instalar, materializar e executar fluxos de subagentes em projetos de software. Ele entrega time base, contratos, adapters, runtime sequencial, memoria curada e artefatos verificaveis. Ele nao promete autonomia universal: execucao real depende do Bali Runtime configurado ou do suporte nativo do host.
```

In `README.md`, replace or add a short section under `## Compatibilidade Real`:

```markdown
### Capability IDs Criticos

Estes ids existem para impedir promessa solta no README:

| Capability id | Estado atual | Como falar disso |
|---|---|---|
| `runtime.parallel_execution` | Not delivered | O runtime e sequencial: `execution_mode: sequential` e `max_parallel: 1`. |
| `host.universal_native_isolation` | Not delivered | Bali materializa adapters; isolamento nativo depende do host. |
| `model.mandatory_multi_model` | Not delivered | `model_policy` e declarativo; troca real de modelo depende do host/wrapper. |
| `runtime.dynamic_routing_plan` | Contract-dependent | O Orchestrator precisa devolver `routing_plan` JSON valido. |
| `runtime.native_or_fallback` | Contract-dependent | Use host nativo quando existir; caso contrario use Bali Runtime com runner configurado. |
```

In `README.md`, adjust runtime wording:

```markdown
O Bali Runtime executa etapas isoladas quando `BALI_SUBAGENT_RUNNER` esta configurado. Sem runner, `run --dry-run` continua util para planejar e auditar a cadeia, mas `run` nao executa trabalho inteligente.
```

- [ ] **Step 4: Run README audit tests**

Run:

```powershell
python -m pytest tests/test_readme_audit.py -q
```

Expected:

```text
4 passed
```

- [ ] **Step 5: Run CLI README strict audit**

Run:

```powershell
python -m bali_agent.cli --root . audit-readme --readme README.md --strict
```

Expected:

```text
README audit OK: nenhuma promessa sem qualificacao encontrada.
```

- [ ] **Step 6: Commit**

```powershell
git add README.md tests/test_readme_audit.py
git commit -m "docs: align readme with capability truth"
```

---

### Task 5: Final Evaluation Script

**Files:**
- Create: `scripts/evaluate_runtime_truth.ps1`
- Test: `tests/test_cli.py`
- Modify: `README.md`

**Interfaces:**
- Produces executable local gate script for Windows/PowerShell.
- Consumes CLI commands from prior tasks.

- [ ] **Step 1: Write script existence test**

Append to `tests/test_cli.py`:

```python
def test_runtime_truth_evaluation_script_documents_required_commands():
    from pathlib import Path

    script = Path("scripts/evaluate_runtime_truth.ps1")
    text = script.read_text(encoding="utf-8")

    assert "python -m pytest -q" in text
    assert "capability-report --json" in text
    assert "audit-readme --readme README.md --strict" in text
    assert "py_compile" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest tests/test_cli.py::test_runtime_truth_evaluation_script_documents_required_commands -q
```

Expected:

```text
FileNotFoundError
```

- [ ] **Step 3: Create evaluation script**

Create `scripts/evaluate_runtime_truth.ps1`:

```powershell
$ErrorActionPreference = "Stop"

python -m pytest -q
python -m py_compile bali_agent\cli.py bali_agent\capabilities.py bali_agent\readme_audit.py bali_agent\templates\runtime\bali_runtime.py

$tmp = Join-Path $env:TEMP ('bali-final-audit-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
    python -m bali_agent.cli --root $tmp init
    python -m bali_agent.cli --root $tmp verify
    python -m bali_agent.cli --root $tmp capability-report --json
    python -m bali_agent.cli --root . audit-readme --readme README.md --strict
}
finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force
    }
}

Write-Host "Runtime truth evaluation passed."
```

- [ ] **Step 4: Document the gate**

Add to README under `## Testes`:

```markdown
Auditoria completa de honestidade README/runtime:

```powershell
.\scripts\evaluate_runtime_truth.ps1
```

Esse gate roda testes, compilacao, inicializacao em projeto temporario, `capability-report --json` e `audit-readme --strict`.
```

- [ ] **Step 5: Run targeted test**

Run:

```powershell
python -m pytest tests/test_cli.py::test_runtime_truth_evaluation_script_documents_required_commands -q
```

Expected:

```text
1 passed
```

- [ ] **Step 6: Run the evaluation script**

Run:

```powershell
.\scripts\evaluate_runtime_truth.ps1
```

Expected:

```text
Runtime truth evaluation passed.
```

- [ ] **Step 7: Commit**

```powershell
git add scripts/evaluate_runtime_truth.ps1 README.md tests/test_cli.py
git commit -m "test: add runtime truth evaluation gate"
```

---

### Task 6: Docs SDD And Product Contract Update

**Files:**
- Modify: `docs/PLAN-runtime-honesty-and-delivery.md`
- Modify: `docs/SDD-runtime-honesty-and-delivery.md`
- Test: manual docs audit with `audit-readme`

**Interfaces:**
- Consumes final commands from Task 5.
- Produces durable engineering record for why these audit commands exist.

- [ ] **Step 1: Update plan doc**

Append to `docs/PLAN-runtime-honesty-and-delivery.md`:

```markdown
## 9. Extensao: Loop de Auditoria README/Runtime

Depois da auditoria senior, o projeto passa a tratar honestidade de README como contrato testavel.

Novos entregaveis:

- Catalogo estruturado em `bali_agent/capabilities.py`.
- `capability-report --json` para automacoes.
- `audit-readme --strict` para bloquear promessas sem qualificacao.
- `scripts/evaluate_runtime_truth.ps1` como gate completo.

O objetivo nao e deixar o README menos ambicioso; e separar com precisao entrega comprovada, dependencia contratual, dependencia de host e trabalho ainda nao entregue.
```

- [ ] **Step 2: Update SDD doc**

Append to `docs/SDD-runtime-honesty-and-delivery.md`:

```markdown
## 10. Capability Catalog

`bali_agent/capabilities.py` e a fonte estruturada para status de capacidades. O README deve se alinhar aos ids desse catalogo.

Categorias:

- `delivered`: existe evidencia local por arquivo, comando ou teste.
- `contract_dependent`: o codigo suporta o fluxo, mas depende de LLM/runner/JSON valido.
- `host_dependent`: Bali materializa configuracao, mas a execucao e do host.
- `not_delivered`: explicitamente fora da entrega atual.

## 11. README Audit

`audit-readme --strict` bloqueia frases que transformam dependencia em garantia. Ele nao substitui revisao humana, mas pega promessas obvias como isolamento nativo universal, paralelismo real entregue e multi-modelo obrigatorio.
```

- [ ] **Step 3: Run docs sanity checks**

Run:

```powershell
python -m bali_agent.cli --root . audit-readme --readme README.md --strict
python -m pytest tests/test_readme_audit.py -q
```

Expected:

```text
README audit OK: nenhuma promessa sem qualificacao encontrada.
4 passed
```

- [ ] **Step 4: Commit**

```powershell
git add docs/PLAN-runtime-honesty-and-delivery.md docs/SDD-runtime-honesty-and-delivery.md
git commit -m "docs: document runtime truth audit loop"
```

---

### Task 7: Final Senior Re-Audit And Retry Loop

**Files:**
- No mandatory code files.
- Optional: create `docs/runtime-truth-audit-result.md` if the user wants a durable report.

**Interfaces:**
- Consumes: `scripts/evaluate_runtime_truth.ps1`
- Produces: final pass/fail report and retry decisions.

- [ ] **Step 1: Run final gate pass 1**

Run:

```powershell
.\scripts\evaluate_runtime_truth.ps1
```

Expected:

```text
Runtime truth evaluation passed.
```

- [ ] **Step 2: Run senior audit command set manually**

Run:

```powershell
python -m pytest -q
python -m bali_agent.cli --root . capability-report
python -m bali_agent.cli --root . audit-readme --readme README.md --strict
```

Expected:

```text
pytest passed
capability-report prints current repo state honestly
README audit OK
```

- [ ] **Step 3: Interpret failure rules**

If `pytest` fails:

```text
Send back to cli-test-engineer with exact failing test and traceback.
```

If `capability-report --json` is invalid:

```text
Send back to runtime-contract-engineer.
```

If `audit-readme --strict` fails:

```text
Send back to docs-truth-auditor and product-copy-editor.
```

If adapter wording overclaims:

```text
Send back to adapter-host-skeptic.
```

If any audit command executes shell, LLM, host tools, or reads secrets:

```text
Send back to security-risk-reviewer.
```

- [ ] **Step 4: Run final gate pass 2 from fresh shell**

Open a new PowerShell in repo root and run:

```powershell
.\scripts\evaluate_runtime_truth.ps1
```

Expected:

```text
Runtime truth evaluation passed.
```

- [ ] **Step 5: Commit final report if created**

If `docs/runtime-truth-audit-result.md` exists:

```powershell
git add docs/runtime-truth-audit-result.md
git commit -m "docs: record runtime truth audit result"
```

If no report file exists, skip commit.

---

## Self-Review

Spec coverage:

- Detailed adjustment plan: covered by Tasks 1-7.
- Agent team that works back and forth: covered by Delivery Team and Iteration Loop.
- Re-run evaluation after fixes: covered by Task 7 and final gate.
- If evaluation fails, put team back to work: covered by Task 7 failure routing.
- Evidence-based honesty between README/runtime/tests: covered by capability catalog, README audit, JSON report, and evaluation script.

Placeholder scan:

- No `TBD`, `TODO`, `implement later`, or vague test instructions remain.
- Every task has explicit files, commands, expected outputs, and commit steps.

Type consistency:

- `Capability`, `build_capability_report`, `ReadmeAuditFinding`, `audit_readme_text`, `audit_readme_file`, and `audit_readme_command` are consistently named across tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-01-readme-runtime-truth-audit-loop.md`.

Recommended execution mode: Subagent-Driven. Dispatch one fresh worker per task, review each task, run the gate, then repeat only failed categories until the gate passes twice.
