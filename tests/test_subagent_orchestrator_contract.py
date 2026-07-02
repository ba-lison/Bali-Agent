# -*- coding: utf-8 -*-
"""Product-positioning contract for Bali as a subagent orchestrator."""

from pathlib import Path


PRODUCT_CONTRACT_FILES = [
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/adapters.md"),
    Path("protocols/subagents.md"),
    Path("bali_agent/protocols/subagents.md"),
    Path("agents/_setup/AGENT.md"),
    Path("bali_agent/agents/_setup/AGENT.md"),
    Path("templates/runtime/bali_runtime.py"),
    Path("bali_agent/templates/runtime/bali_runtime.py"),
]


def test_product_contract_does_not_present_bali_as_generic_llm_command_wrapper():
    forbidden_terms = [
        "BALI_LLM_COMMAND",
        "fallback universal",
        "API crua",
        "raw API",
        "other CLIs",
    ]

    for path in PRODUCT_CONTRACT_FILES:
        text = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            assert term not in text, f"{path} still contains {term!r}"


def test_readme_leads_with_subagent_orchestration_contract():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "orquestrador universal de subagentes" in text or "orquestrador de subagentes" in text
    assert "paperclip" not in text.lower()
    assert "executor generico" not in text.lower()
    assert "executor genérico" not in text.lower()
