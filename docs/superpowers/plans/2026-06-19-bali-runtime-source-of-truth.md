# Bali Runtime Source Of Truth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Bali Runtime the authority for project execution and allow agents to create auditable project-local skills.

**Architecture:** The installed `.agent/run.py` bootstrapper delegates to `.agent/runtime/bali_runtime.py`, and `bali run` delegates to the installed runtime when available. Runtime remains responsible for selecting the native/agentic execution path. Skill creation is exposed as a runtime tool that writes only under `.agent/skills/` and appends an audit log.

**Tech Stack:** Python 3.11+, pytest, existing Bali-Agent CLI/templates/runtime architecture.

## Global Constraints

- Subagents are real: no role-play fallback.
- Bali Runtime is the source of truth; IDE/CLI adapters mirror or invoke it.
- Orchestrator may answer trivial requests directly.
- Any technical project work must use subagents plus Reviewer.
- Skills may be created automatically by agents, but must be project-local and auditable.
- Do not add third-party dependencies.

---

### Task 1: Installed Runtime Bootstrap

**Files:**
- Modify: `bali_agent/cli.py`
- Modify: `templates/runtime/bali_runtime.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: existing `init_command(target_dir: Path) -> int`
- Produces: installed `.agent/runtime/bali_runtime.py` and `.agent/run.py` that invokes it

- [ ] **Step 1: Write failing init test**

Add assertions to `tests/test_cli.py::test_cli_init_command`:

```python
assert (proj_path / ".agent" / "runtime" / "bali_runtime.py").is_file()
run_text = (proj_path / ".agent" / "run.py").read_text(encoding="utf-8")
assert ".agent/runtime/bali_runtime.py" in run_text
manifest_text = (proj_path / ".agent" / "subagent.config.yaml").read_text(encoding="utf-8")
assert 'runtime_authority: "bali-runtime"' in manifest_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py::test_cli_init_command -q`

Expected: FAIL because `.agent/runtime/bali_runtime.py` is not installed and the bootstrapper still calls `bali run`.

- [ ] **Step 3: Implement runtime bootstrap install**

Update `init_command` to create `.agent/runtime/`, copy `templates/runtime/bali_runtime.py` there, add `runtime_authority: "bali-runtime"` to the manifest, and write `.agent/run.py` as a thin subprocess wrapper around `.agent/runtime/bali_runtime.py run`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py::test_cli_init_command -q`

Expected: PASS.

### Task 2: Runtime Provider Path Avoids Bootstrap Recursion

**Files:**
- Modify: `templates/runtime/bali_runtime.py`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: `run_task(root, task, dry_run=False, specialist_name=None, workflow="operate")`
- Produces: provider mode routes to `.agent/templates/run.py`, not `.agent/run.py`

- [ ] **Step 1: Write failing provider routing test**

Add a test that sets `BALI_SUBAGENT_PROVIDER`, monkeypatches `subprocess.run`, invokes `run_task`, and asserts the command path ends with `.agent/templates/run.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_integration.py::test_runtime_provider_uses_templates_run_bridge -q`

Expected: FAIL because runtime currently selects `.agent/run.py`.

- [ ] **Step 3: Implement provider route**

Change `templates/runtime/bali_runtime.py` so provider mode prefers `root / ".agent" / "templates" / "run.py"` and only falls back to repository-local `templates/run.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_integration.py::test_runtime_provider_uses_templates_run_bridge -q`

Expected: PASS.

### Task 3: Auditable Skill Creation Tool

**Files:**
- Create: `templates/core/skills.py`
- Create: `bali_agent/templates/core/skills.py`
- Modify: `templates/core/tools.py`
- Modify: `templates/core/agent_loop.py`
- Modify: `bali_agent/core/tool_registry.py`
- Modify: `bali_agent/core/runner.py`
- Test: `tests/test_skills.py`

**Interfaces:**
- Produces: `create_or_update_skill(root: Path, skill_id: str, title: str, body: str, reason: str, agent: str) -> str`
- Produces tool name: `create_skill`

- [ ] **Step 1: Write failing skill tests**

Create tests that assert:

```python
result = create_or_update_skill(root, "render-debugging", "Render Debugging", body, "needed for recurring render incidents", "orchestrator")
assert (root / ".agent" / "skills" / "render-debugging" / "SKILL.md").is_file()
assert "render-debugging" in (root / ".agent" / "skills" / "AUDIT.md").read_text(encoding="utf-8")
```

Also assert invalid ids like `"../escape"` raise `ValueError`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_skills.py -q`

Expected: FAIL because the module/tool does not exist.

- [ ] **Step 3: Implement project-local skill manager**

Add `templates/core/skills.py` and package mirror with strict id validation, writes under `.agent/skills/<id>/SKILL.md`, and append-only `.agent/skills/AUDIT.md`.

- [ ] **Step 4: Wire runtime tools**

Expose `create_skill` in `templates/core/agent_loop.py`, `templates/core/tools.py`, `bali_agent/core/tool_registry.py`, and `bali_agent/core/runner.py`.

- [ ] **Step 5: Run tests to verify green**

Run: `python -m pytest tests/test_skills.py tests/test_integration.py tests/test_cli.py -q`

Expected: PASS.

### Task 4: Full Regression

**Files:**
- No production edits unless tests expose integration failures.

**Interfaces:**
- Consumes: all changes above
- Produces: verified package state

- [ ] **Step 1: Run full suite**

Run: `python -m pytest -q`

Expected: 0 failures.

- [ ] **Step 2: Inspect git diff**

Run: `git diff --check`

Expected: no whitespace errors.

## Self-Review

- Spec coverage: covers runtime as authority, bootstrap route, provider recursion prevention, and auditable auto-created skills.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: skill manager signature is consistent across tests and runtime wiring.
