# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
