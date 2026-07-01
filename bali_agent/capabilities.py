# -*- coding: utf-8 -*-
"""Structured capability catalog for Bali-Agent operational audits."""

from __future__ import annotations

from dataclasses import asdict, dataclass
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
        Capability(
            "cli.installed_structure",
            "CLI installed structure",
            "delivered",
            agent_root.is_dir(),
            ".agent directory",
            [".agent/"],
        ),
        Capability(
            "team.core_manifest",
            "Core team and manifest",
            "delivered",
            not verify_problems and manifest.is_file(),
            "verify passes" if not verify_problems else "; ".join(verify_problems[:3]),
            [".agent/subagent.config.yaml", ".agent/team/"],
        ),
        Capability(
            "runtime.script",
            "Bali Runtime script",
            "delivered",
            runtime_script.is_file(),
            ".agent/runtime/bali_runtime.py",
            [".agent/runtime/bali_runtime.py"],
        ),
        Capability(
            "memory.curated_file",
            "Curated memory file",
            "delivered",
            memory.is_file(),
            ".agent/memory.md",
            [".agent/memory.md"],
        ),
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
        Capability(
            "runtime.native_or_fallback",
            "Native subagent orchestration",
            "contract_dependent",
            runtime_script.is_file(),
            "requires native adapter or Bali Runtime",
            [".agent/runtime/bali_runtime.py"],
        ),
        Capability(
            "runtime.dynamic_routing_plan",
            "Dynamic routing plan",
            "contract_dependent",
            runtime_script.is_file(),
            "requires Orchestrator JSON routing_plan",
            ["bali_agent/templates/runtime/bali_runtime.py"],
        ),
        Capability(
            "runtime.reviewer_fail_closed",
            "Reviewer fail-closed gate",
            "contract_dependent",
            runtime_script.is_file(),
            "requires structured Reviewer JSON",
            ["bali_agent/templates/runtime/bali_runtime.py"],
        ),
    ]

    host_dependent = []
    for name, adapter_cls in ADAPTERS.items():
        try:
            valid, problems = adapter_cls(root).verify()
            detail = "adapter verify passes" if valid else "; ".join(problems[:2])
        except Exception as exc:  # pragma: no cover - defensive for host-specific adapters
            valid = False
            detail = str(exc)
        host_dependent.append(
            Capability(
                f"adapter.{name}",
                f"{name} native adapter",
                "host_dependent",
                valid,
                detail,
                ["bali_agent/adapters/"],
            )
        )

    not_delivered = [
        Capability(
            "runtime.parallel_execution",
            "Parallel agent execution",
            "not_delivered",
            False,
            "runtime requires execution_mode sequential and max_parallel 1",
            ["bali_agent/templates/runtime/bali_runtime.py"],
        ),
        Capability(
            "host.universal_native_isolation",
            "Guaranteed native isolation in every host",
            "not_delivered",
            False,
            "Bali materializes files; host executes native isolation",
            ["bali_agent/adapters/"],
        ),
        Capability(
            "model.mandatory_multi_model",
            "Mandatory multi-model execution",
            "not_delivered",
            False,
            "model_policy is declarative unless host/wrapper supports it",
            [".agent/subagent.config.yaml"],
        ),
    ]

    return {
        "delivered": delivered,
        "contract_dependent": contract_dependent,
        "host_dependent": host_dependent,
        "not_delivered": not_delivered,
    }
