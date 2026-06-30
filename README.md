# Bali-Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/ba-lison/Bali-Agent/blob/main/LICENSE)
[![CI](https://github.com/ba-lison/Bali-Agent/actions/workflows/ci.yml/badge.svg)](https://github.com/ba-lison/Bali-Agent/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.2.0-green.svg)](https://github.com/ba-lison/Bali-Agent/blob/main/CHANGELOG.md)

Bali-Agent is a subagent-first framework for software engineering work. It gives every project a real agent team: an Orchestrator, a product spine, execution specialists, review gates, security rules, and durable project memory.

The goal is not "many models at any cost." The goal is real delegated work. If a host can run different models per subagent, Bali can route by model policy. If it cannot, every subagent uses the host default model and the workflow still works.

## Core Idea

```text
Human
  -> Orchestrator
      -> Discovery / PRD / SDD when product or architecture changes
      -> Recruiter when the project needs a new recurring specialist
      -> Planner for task decomposition
      -> Specialists for execution
      -> QA / Security when needed
      -> Reviewer for final gate
      -> Memory Curator for project learning
  -> Human
```

The Orchestrator is the single contact point with the human. It does not implement code. It coordinates subagents, validates their output, sends work back when it is incomplete, and returns only reviewed results.

## What A Subagent Means

A Bali subagent is not a role played in the same chat context. A real subagent has its own definition, scope, prompt, context boundary, and execution path.

Bali supports three kinds of subagents:

| Type | Examples | Lifecycle |
|---|---|---|
| Core team | `orchestrator`, `discovery`, `prd-writer`, `sdd-architect`, `reviewer` | Always present in every project |
| Project-fixed specialists | `spec-supabase`, `spec-cloudflare`, `spec-lgpd` | Persist in that project and handle recurring work |
| Temporary agents | `temp-debug-timeout`, `temp-pdf-audit` | Created for one run and discarded afterward |

Agent-as-tool is a different pattern. Use agent-as-tool for narrow, stateless operations. Use subagents for delegated project work with context, handoff, and review.

## The Required Core Team

Every initialized Bali project has this team in `.agent/team/`:

- `orchestrator`: the hub and only human-facing coordinator.
- `discovery`: interviews the user and discovers existing-project context.
- `prd-writer`: turns discovery into product requirements.
- `sdd-architect`: turns PRD into technical architecture and implementation design.
- `planner`: decomposes approved work into ordered tasks.
- `implementer`: general implementation specialist.
- `qa`: test and verification specialist.
- `security`: security and data-risk specialist.
- `reviewer`: mandatory quality gate.
- `recruiter`: creates or promotes project-fixed specialists.
- `memory-curator`: updates working context and durable memory.
- `docs`: documentation and knowledge specialist.

`spec-implementer` is still created as a legacy fallback for the current runtime path, so older flows keep working while the new core team contract lands.

## Product Spine

Discovery, PRD, and SDD sit above execution. They are not optional decorations.

```text
Discovery -> PRD Writer -> SDD Architect
```

Use the Product Spine for:

- new projects;
- large features;
- product behavior changes;
- architecture or data model changes;
- integrations, auth, permissions, billing, AI, deploy, or security changes;
- existing projects when the repo context is unclear.

Small tasks can use a shorter path, but real project work still goes through a specialist and Reviewer.

## Lifecycle

### New Project

```text
1. Install Bali in the target repo.
2. Discovery interviews the user.
3. PRD Writer creates the product requirements.
4. SDD Architect creates the technical design.
5. Recruiter creates project-fixed specialists for recurring domains.
6. Planner breaks the work into executable tasks.
7. Specialists implement.
8. QA and Security validate when relevant.
9. Reviewer approves or rejects.
10. Memory Curator updates project memory.
```

### Existing Project

```text
1. Bali preserves the repo's existing rules and governance.
2. Discovery reads repo context, docs, working context, and memory.
3. Orchestrator classifies the request.
4. Product Spine runs if the request changes product or architecture.
5. Existing specialists handle matching scopes.
6. Recruiter creates a fixed specialist only when the need is recurring.
7. Temporary agents handle one-off investigations.
8. Reviewer gates the result.
9. Memory Curator records what should survive future sessions.
```

## Host And Adapter Model

Bali keeps one project team and materializes it for each host.

| Host | Native path | Notes |
|---|---|---|
| Claude Code | `.claude/agents/*.md` | Uses native subagents when the surface has Agent/Task tooling. Hooks remain useful for context reinjection. |
| Codex | `.codex/agents/*.toml` | Uses project custom agents when available. |
| OpenCode | `.opencode/agents/*.md` | Uses `mode: subagent`. |
| Antigravity | `.antigravity/skills/` or `.agents/skills/` | Uses `define_subagent` and background subagents with safe queueing. |
| Cursor | Cursor rules plus Bali Runtime | Rules provide context; Runtime provides isolation when native subagents are unavailable. |
| Ollama / raw API / other CLIs | Bali Runtime | Uses `BALI_LLM_COMMAND` or provider settings to run isolated agent calls. |

The important question is not "desktop or API?" The important question is: does the host expose a real isolated subagent or tool-calling mechanism? If yes, use the native adapter. If not, use Bali Runtime. If neither exists, fail closed instead of pretending.

## Model Policy

Multi-model routing is optional. A project can declare preferences by agent class:

```yaml
model_policy:
  default: host-default
  agents:
    orchestrator:
      preferred: strong-reasoning
      fallback: host-default
    reviewer:
      preferred: strong-reasoning
      fallback: host-default
    implementer:
      preferred: strong-coding
      fallback: host-default
```

If the host supports per-agent model selection, the adapter can use this. If not, every agent uses the current host model.

## Installation

Requirements:

- Python 3.11+
- `pyyaml`

Install Bali-Agent locally:

```bash
git clone https://github.com/ba-lison/Bali-Agent.git
cd Bali-Agent
pip install -e .
```

Initialize a target project:

```bash
bali init /path/to/project
```

Verify the installation:

```bash
bali --root /path/to/project verify
```

## CLI

```bash
bali --root /path/to/project <command>
```

| Command | Purpose |
|---|---|
| `init` | Installs `.agent/`, runtime, templates, protocols, team files, memory files, and adapters. |
| `verify` | Validates required team, manifest, runtime, memory, and adapter contract. |
| `verify-adapter <name>` | Checks one adapter such as `claude`, `codex`, or `antigravity`. |
| `list-agents` | Lists agents registered in `.agent/team/`. |
| `create-agent --id spec-name --scope "..."` | Creates a project-fixed specialist. |
| `run "task"` | Runs the Orchestrator flow. |
| `run --workflow greenfield "task"` | Runs the greenfield Product Spine flow. |
| `remember` | Adds a curated memory entry. |
| `inspect-runs` | Shows recorded runtime traces. |

Examples:

```bash
bali --root . verify
bali --root . create-agent --id spec-supabase --scope "Supabase auth, RLS, storage, migrations"
bali --root . run "fix the login redirect bug"
bali --root . remember --kind decision --title "Use Supabase RLS" --summary "Auth data stays protected by database policy"
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `BALI_LLM_PROVIDER` | Provider name: `openai`, `anthropic`, `gemini`, or `ollama`. |
| `BALI_LLM_MODEL` | Model name used by the runtime provider. |
| `BALI_API_KEY` | Provider API key, or use provider-specific env vars. |
| `BALI_LLM_ENDPOINT` | Optional custom endpoint. |
| `BALI_LLM_COMMAND` | Shell command template for CLI/local models using `{prompt_file}`, `{output_file}`, and `{agent}`. |
| `BALI_SUBAGENT_DEPTH` | Internal recursion depth for spawned subagents. Max intended depth is 2. |

## What `bali init` Installs

```text
.agent/
  subagent.config.yaml       # team manifest, product spine, model policy
  working-context.md         # live project state
  memory.md                  # curated durable memory
  task.md                    # current task checklist
  run.py                     # bootstrapper that delegates to runtime
  verify_setup.py            # setup verifier
  .gitignore                 # ignores runtime outputs and secrets
  hooks/
    prevent_secrets.py
  runtime/
    bali_runtime.py
  team/
    orchestrator.md
    discovery.md
    prd-writer.md
    sdd-architect.md
    planner.md
    implementer.md
    qa.md
    security.md
    reviewer.md
    recruiter.md
    memory-curator.md
    docs.md
    spec-implementer.md
  protocols/
    subagents.md
    routing.md
    memory.md
    handoff.md
    quality-gates.md
    approval-gates.md
  agents/
  templates/
  skills/
    AUDIT.md
```

Adapters may also create host-specific folders:

```text
.claude/agents/*.md
.codex/agents/*.toml
.opencode/agents/*.md
.antigravity/skills/
.agents/skills/
.cursor/rules/bali-agent.mdc
```

## Manifest Shape

The manifest is the source of truth for the team:

```yaml
runtime_authority: "bali-runtime"
subagents_policy:
  role_play_permitido: false
  fallback_obrigatorio: "adapter-nativo-ou-bali-runtime"

time:
  core:
    - orchestrator
    - discovery
    - prd-writer
    - sdd-architect
    - planner
    - implementer
    - qa
    - security
    - reviewer
    - recruiter
    - memory-curator
    - docs
  product_spine:
    - discovery
    - prd-writer
    - sdd-architect
  project_fixed: []
  temporary_policy:
    max_per_task: 3
    promote_after_reuse_count: 3

model_policy:
  default: host-default
```

## Memory

Bali separates live state from durable learning.

| File | Meaning |
|---|---|
| `.agent/working-context.md` | Current status, active handoff, recent progress, risks, next action. Not a history log. |
| `.agent/memory.md` | Curated decisions, incidents, reusable lessons, project-specific conventions. |
| `.agent/memory.db` | SQLite FTS5 index used by memory search. Ignored by git. |

Memory is automatic in the lifecycle. At the end of relevant tasks, gates, decisions, incidents, PRs, or commits, the Orchestrator calls `memory-curator`.

The Memory Curator:

- updates `working-context.md` for live state;
- writes to `memory.md` only when there is reusable learning;
- rejects raw logs;
- blocks secrets, tokens, keys, and unnecessary personal data.

## Security

Bali keeps the previous security model and makes it part of the runtime contract.

### Filesystem Safety

- Paths are normalized before access.
- Traversal and sibling-prefix attacks are blocked with safe path checks.
- Sensitive paths such as `.env`, `.git`, and secret folders are blocked.

### Command Safety

Commands are classified and executed without shell string composition. The command policy is subcommand-aware:

| Executable | Allowed examples | Blocked examples |
|---|---|---|
| `pytest` | direct test runs | none by default |
| `npm` | `test`, `run` | `install`, `ci`, `publish`, `exec` |
| `cargo` | `test`, `check`, `build` | `run`, `install` |
| `go` | `test`, `build`, `vet`, `fmt` | `run`, `install`, `get` |
| `git` | `status`, `diff`, `log`, `show` | `push`, `commit`, `reset`, `checkout` |
| `pip` | none | all, by default |

Chaining operators such as `;`, `&&`, pipes, and command substitution are blocked in runtime tool execution.

### Tool Registry

Tools are default-deny:

- `allowed_tools: []` means no tools.
- `allowed_tools: ["read_file", "search_memory"]` means only those tools.
- `allowed_tools: ["*"]` is an explicit opt-in to all registered tools.

### Reviewer Fail-Closed

Reviewer output must be valid structured JSON. If the Reviewer output is malformed, missing required fields, approves with blockers, or skips required checks, the runtime fails closed instead of silently approving.

### Secret Protection

- `prevent_secrets.py` is installed into `.agent/hooks/`.
- Memory writes reject obvious secret patterns.
- Runtime outputs and memory database files are ignored by `.agent/.gitignore`.

## Runtime And Observability

Bali Runtime is the universal fallback when native subagents are unavailable.

It records run artifacts under `.agent/output/` or runtime-specific run folders, including prompts, outputs, traces, failure events, handoffs, and dry-run output.

The runtime supports:

- `verify`
- `list-agents`
- `create-agent`
- `run`
- `remember`

When provider mode is used, execution routes through `.agent/templates/run.py` to avoid recursive bootstrap loops.

## Tests

Run the full suite:

```bash
python -m pytest -q
```

Compile key Python modules:

```bash
python -m py_compile bali_agent/cli.py bali_agent/adapters/claude.py bali_agent/core/agent_manager.py
```

Important suites:

| Suite | Covers |
|---|---|
| `tests/test_cli.py` | `bali init`, runtime delegation, manifest creation. |
| `tests/test_claude_adapter.py` | Claude native `.claude/agents` materialization. |
| `tests/test_agent_manager.py` | Team validation, specialist creation, manifest policy checks. |
| `tests/test_runtime_orchestration.py` | Dynamic routing plans, retries, temporary/permanent specialists. |
| `tests/test_runner_security.py` | Tool permissions, command policy, Reviewer fail-closed behavior. |
| `tests/test_memory.py` | Curated memory and secret blocking. |
| `tests/test_security.py` | Path safety and command sanitization. |

## Current Product Direction

Bali is now organized around this hierarchy:

```text
Product Spine:
  Discovery -> PRD -> SDD

Team Spine:
  Recruiter -> Core Team + Project Specialists

Execution Spine:
  Planner -> Specialists -> QA/Security -> Reviewer

Learning Spine:
  Memory Curator -> working-context.md + memory.md
```

This keeps the original security, memory, runtime, adapter, and review work intact, while making the product identity clearer: Bali is a persistent subagent team for each project.

## License

MIT. Copyright (c) 2025-2026 Alison Cruz.
