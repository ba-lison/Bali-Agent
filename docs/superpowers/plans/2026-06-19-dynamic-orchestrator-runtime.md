# Dynamic Orchestrator Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace fixed fallback chains with Orchestrator-authored dynamic execution plans using real isolated subagent calls.

**Architecture:** Bali Runtime first invokes the Orchestrator as an isolated agent. The Orchestrator returns a JSON routing plan describing classification, specialist lifecycle decisions, execution steps, reviewer gates, and retry policy. Runtime materializes permanent or temporary agents, executes each step in its own LLM/CLI call, sends outputs through Reviewer gates, retries failed steps with feedback, and only prints the approved final result.

**Tech Stack:** Python 3.11+, pytest, existing `templates/runtime/bali_runtime.py` fallback command execution.

## Global Constraints

- Bali Runtime remains the source of truth.
- Orchestrator may answer trivial requests directly.
- Non-trivial work must use real subagent calls plus Reviewer.
- Missing recurring specialties become permanent `spec-*` agents in `.agent/team/`.
- One-off specialties become temporary agents under the run directory and are not registered in the project team.
- Reviewer rejection triggers retry with feedback up to the plan's retry limit.
- No third-party dependencies.

---

### Task 1: Routing Plan Parsing

**Files:**
- Modify: `templates/runtime/bali_runtime.py`
- Modify mirror: `bali_agent/templates/runtime/bali_runtime.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Produces: `_extract_json_object(text: str) -> dict`
- Produces: `_parse_routing_plan(text: str) -> dict`

- [ ] **Step 1: Write failing parsing tests**

Test that a JSON object embedded in Orchestrator prose is extracted and that invalid/missing plans raise `ValueError`.

- [ ] **Step 2: Run parsing tests and watch them fail**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_parse_routing_plan_from_orchestrator_output -q`

- [ ] **Step 3: Implement parsing helpers**

Add brace-counting JSON extraction, validate `classification`, `steps`, and `reviewer` fields for non-trivial work.

- [ ] **Step 4: Run parsing tests and watch them pass**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_parse_routing_plan_from_orchestrator_output -q`

### Task 2: Dynamic Step Execution

**Files:**
- Modify: `templates/runtime/bali_runtime.py`
- Modify mirror: `bali_agent/templates/runtime/bali_runtime.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Consumes: `_run_llm(command_template, prompt_path, output_path, agent_name)`
- Produces: dynamic call order from Orchestrator plan

- [ ] **Step 1: Write failing dynamic execution test**

Patch `_run_llm` so Orchestrator emits a small-task plan with only `spec-implementer` and `reviewer`. Assert Planner is not called.

- [ ] **Step 2: Run test and watch it fail**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_runtime_executes_orchestrator_dynamic_plan -q`

- [ ] **Step 3: Implement dynamic execution**

Change `run_task` to invoke Orchestrator first, parse the plan, then execute the plan's steps instead of `_build_chain`.

- [ ] **Step 4: Run dynamic execution test**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_runtime_executes_orchestrator_dynamic_plan -q`

### Task 3: Reviewer Retry Loop

**Files:**
- Modify: `templates/runtime/bali_runtime.py`
- Modify mirror: `bali_agent/templates/runtime/bali_runtime.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Produces: `_reviewer_approved(text: str) -> tuple[bool, str]`

- [ ] **Step 1: Write failing retry test**

Simulate specialist output rejected once by Reviewer and approved on retry. Assert specialist and reviewer are each called twice.

- [ ] **Step 2: Run retry test and watch it fail**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_runtime_retries_step_when_reviewer_rejects -q`

- [ ] **Step 3: Implement retry loop**

For steps with `review: true`, call Reviewer, parse `approved`, and retry with blocker feedback up to `max_retries`.

- [ ] **Step 4: Run retry test**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_runtime_retries_step_when_reviewer_rejects -q`

### Task 4: Specialist Lifecycle

**Files:**
- Modify: `templates/runtime/bali_runtime.py`
- Modify mirror: `bali_agent/templates/runtime/bali_runtime.py`
- Test: `tests/test_runtime_orchestration.py`

**Interfaces:**
- Permanent agents use existing `create_agent(root, id, scope, overwrite=False)`.
- Temporary agents are written under `.agent/output/runtime/<run-id>/temp-agents/<id>.md`.

- [ ] **Step 1: Write failing lifecycle tests**

Assert permanent missing `spec-payments` is registered in `.agent/team/`, while temporary `spec-one-shot` is not.

- [ ] **Step 2: Run lifecycle tests and watch them fail**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_runtime_materializes_permanent_and_temporary_specialists -q`

- [ ] **Step 3: Implement lifecycle materialization**

Materialize agents declared by Orchestrator before executing steps and merge temporary paths into the runtime agent map.

- [ ] **Step 4: Run lifecycle tests**

Run: `python -m pytest tests/test_runtime_orchestration.py::test_runtime_materializes_permanent_and_temporary_specialists -q`

### Task 5: Regression

**Files:**
- No production edits unless tests expose integration failures.

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_runtime_orchestration.py tests/test_integration.py tests/test_cli.py -q`

- [ ] **Step 2: Run full suite**

Run: `python -m pytest -q`

- [ ] **Step 3: Check whitespace**

Run: `git diff --check`

## Self-Review

- Spec coverage: covers dynamic routing, retries, and fixed/temporary specialist lifecycle.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: helper names and plan keys are consistent across tasks.
