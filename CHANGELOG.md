# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-06-18

### Security (Critical)
- **sandbox**: Replaced `startswith()` with `os.path.commonpath()` in `_safe_path()` to
  correctly block sibling-directory prefix attacks (e.g. `/tmp/proj` vs `/tmp/project-evil`).
- **command_policy**: Replaced executable-level allowlist with **subcommand-level allowlist**.
  - `python -c`, `python3 -c` → blocked (arbitrary code execution).
  - `npm exec`, `npm install`, `npm i`, `npm ci`, `npm publish` → blocked (supply-chain risk).
  - `pip install` (all variants) → blocked entirely.
  - `cargo run`, `cargo install` → blocked.
  - `go run`, `go install`, `go get` → blocked.
  - `git push`, `git commit`, `git reset`, `git checkout` → blocked.
  - Safe subcommands (`pytest`, `mypy`, `npm test`, `npm run`, `cargo test`, `go test`, `git status/diff/log`) → allowed.
- **tool_registry**: Changed `get_allowed_schemas()` to **default-deny**.
  - `allowed_tools: []` → returns zero schemas (previously returned all tools).
  - `allowed_tools: ["*"]` → grants all tools (explicit opt-in required).
- **runner**: Enforced `can_spawn_agents` flag before `invoke_subagent` execution.
  Agents with `can_spawn_agents: false` are now hard-blocked at the runtime level.
- **runner**: Reviewer gate is now **fail-closed**.
  - Missing JSON in reviewer response → `ValueError` (was silently ignored).
  - Invalid/malformed JSON → `ValueError` (was silently ignored).
  - Missing `approved` key → `ValueError`.
  - Non-boolean `approved` → `ValueError`.
  - JSON extractor upgraded from lazy regex to brace-counting algorithm (handles nested objects).
- **path_policy**: Replaced substring matching with `os.path.realpath()` normalisation and
  component-level pattern matching to defeat `../` tricks and symlink traversal.
- **adapters**: Added `capability_status: verified | declared` field to all adapter
  capabilities, distinguishing what is actively checked vs. just documented.

### Added
- `tests/test_runner_security.py` — 57 new test cases covering all critical security fixes:
  sandbox commonpath, sibling-prefix attack, subcommand policy (python/npm/pip/cargo/go/git),
  path policy realpath, tool_registry default-deny, can_spawn_agents enforcement,
  and Reviewer gate fail-closed scenarios.
- `.github/workflows/ci.yml` — GitHub Actions CI running `pytest` + `mypy` on
  Python 3.11 and 3.12 on every push/PR to `main`.

### Changed
- `pyproject.toml`: Added `[tool.mypy]` configuration with `disallow_untyped_defs = true`
  and `[tool.pytest.ini_options]` for consistent test discovery.

## [2.2.0] - 2026-06-18

### Added
- Unified CLI command line entry point `bali`.
- Subagent Config schema parser supporting strict YAML definitions (`subagent.config.yaml`).
- `ToolPolicy` authorization engine with risk classifications R0-R4.
- Execution tracing log (`trace.jsonl`) and context manifest (`context_manifest.json`) output under `.agent/runs/`.
- File sandbox resolver (`_safe_path`) preventing directory traversals.
- Secret and credential scanner block on file writes and prompt packer redactions.
- Fully modular package structure under `bali_agent/`.
- Dynamic and deterministic test suite covering core security and runtime features under `tests/`.
- Semantic package metadata (`pyproject.toml`).

### Changed
- Refactored `init.py` to copy the modular `bali_agent` runtime to `.agent/` and set up git pre-commit safety hooks automatically.
- Unified parallel runtimes `bali_runtime.py` and `run.py` into a single canonical engine.
- Replaced insecure command executions (`shell=True`) with tokenized subprocess calls (`shell=False`).

## [2.1.0] - 2026-06-17

### Added
- Memory SQLite indexer using FTS5 virtual tables.
- Sliding window history trimming to manage token budgets on long sessions.
- Handoff bus for atomic subagent coordinate signals.
- Specialists agent templates in `team/`.

## [1.0.0] - 2025-10-15

### Added
- Initial framework design with role-play prompt files.
- Claude Code and Codex template adapters.
- Basic `init.py` installer.
