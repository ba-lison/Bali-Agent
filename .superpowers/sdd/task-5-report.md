# Task 5 Report

## Summary

Implemented the final runtime-truth evaluation gate for Bali-Agent.

## Changes

- Added `scripts/evaluate_runtime_truth.ps1`.
- Added CLI coverage in `tests/test_cli.py` for the gate script contents.
- Documented the gate in `README.md` under `## Testes`.

## Behavior

The script now:

- runs the full Python test suite;
- compiles the key runtime modules;
- initializes a temporary project and runs `init`, `verify`, and `capability-report --json` there;
- runs `audit-readme --readme README.md --strict` against the repository root, not the temp project;
- cleans up the temporary directory afterward.

## Verification

- Targeted test: passed.
- Gate script: passed.
- Full test suite: passed as part of the script run.

## Notes

- The audit-readme root correction from the brief was applied explicitly.
- No open concerns.

## Follow-up Fix

Addressed the review findings from commit `1ebaa70`:

- wrapped every `python` invocation in `scripts/evaluate_runtime_truth.ps1` with `Invoke-Step` so native command failures now stop the gate;
- anchored the script to the repo root with `$PSScriptRoot`, `Split-Path -Parent`, `Push-Location`, and `Pop-Location`;
- kept temp directory cleanup inside `finally`;
- kept `audit-readme --readme README.md --strict` running with `--root .` after the repo-root push;
- strengthened `tests/test_cli.py::test_runtime_truth_evaluation_script_documents_required_commands` to check the anchor, wrapper, and fail-closed structure instead of loose substrings.

## Follow-up Verification

- `python -m pytest tests/test_cli.py::test_runtime_truth_evaluation_script_documents_required_commands -q`
- `.\scripts\evaluate_runtime_truth.ps1` from repo root
- `& 'C:\Users\suporte2\Documents\.Inovaxao_Totalcad\.agent\Bali-Agent\scripts\evaluate_runtime_truth.ps1'` from `C:\Users\suporte2\Documents\.Inovaxao_Totalcad\.agent`
