# Task 1 Report

Implemented the capability catalog source of truth in `bali_agent/capabilities.py` and added coverage in `tests/test_capabilities.py`.

What changed:
- Added `CapabilityStatus` and the frozen `Capability` dataclass.
- Added `build_capability_report(root: Path) -> dict[str, list[Capability]]`.
- Wired the catalog to `bali_agent.core.agent_manager.verify(root)` and `bali_agent.adapters.ADAPTERS`.
- Added stable report sections for delivered, contract-dependent, host-dependent, and not-delivered capabilities.
- Added a parallel-execution entry marked as not delivered with sequential/max_parallel evidence in the detail text.

Verification:
- `python -m pytest tests/test_capabilities.py -q`
- `python -m pytest -q`

Commit:
- `f01d13a feat: add capability catalog`

Notes:
- The working tree still contains an unrelated pre-existing untracked `.superpowers/` directory entry; I did not modify it.

Fix follow-up:
- `bali_agent.cli.capability_report(root)` now consumes `build_capability_report(root)` instead of a separate hard-coded catalog, while keeping the same section labels and human-facing status text.
- `tests/test_capabilities.py` now asserts the report entries are `Capability` objects, that each bucket's items carry the matching status, and that `id`, `title`, `detail`, and `evidence` are populated.
- Verified with `python -m pytest tests/test_capabilities.py tests/test_cli.py -q` -> `11 passed`.
