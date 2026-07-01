from pathlib import Path

from bali_agent.readme_audit import audit_readme_text


def _read_capability_rows(text: str) -> dict[str, tuple[str, str, str]]:
    rows: dict[str, tuple[str, str, str]] = {}
    in_capability_table = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "| Capability id | Estado atual | Como falar disso |":
            in_capability_table = True
            continue

        if not in_capability_table:
            continue

        if not line.startswith("|"):
            break

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        if set(cells[0]) <= {"-"}:
            continue

        rows[cells[0].strip("`")] = (cells[0], cells[1], cells[2])

    return rows


def _paragraph_containing(text: str, fragment: str) -> str:
    for paragraph in text.split("\n\n"):
        if fragment in paragraph:
            return paragraph
    raise AssertionError(fragment)


def test_current_readme_names_critical_capability_limits():
    text = Path("README.md").read_text(encoding="utf-8")
    rows = _read_capability_rows(text)

    capability_expectations = {
        "runtime.parallel_execution": (
            "Not delivered",
            ("sequencial", "max_parallel: 1"),
        ),
        "host.universal_native_isolation": (
            "Not delivered",
            ("isolamento nativo", "depende do host"),
        ),
        "model.mandatory_multi_model": (
            "Not delivered",
            ("model_policy", "declarativo", "host/wrapper"),
        ),
        "runtime.dynamic_routing_plan": (
            "Contract-dependent",
            ("routing_plan", "JSON valido"),
        ),
        "runtime.native_or_fallback": (
            "Contract-dependent",
            ("Bali Runtime", "runner"),
        ),
    }

    for capability_id, (expected_state, required_phrases) in capability_expectations.items():
        assert capability_id in rows, capability_id
        row_id, state, guidance = rows[capability_id]
        assert row_id == f"`{capability_id}`"
        assert state == expected_state
        for phrase in required_phrases:
            assert phrase in guidance, (capability_id, phrase, guidance)

    runtime_paragraph = _paragraph_containing(text, "BALI_SUBAGENT_RUNNER")
    assert "BALI_SUBAGENT_RUNNER" in runtime_paragraph
    assert "run --dry-run" in runtime_paragraph
    assert "nao executa trabalho inteligente" in runtime_paragraph


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


def test_readme_audit_flags_bare_negation_claim_with_mandatory_multi_model():
    findings = audit_readme_text("Bali nao e limitado: sempre usa modelos diferentes por agente.\n")

    assert findings
    assert any("multi-modelo" in finding.message.lower() or "modelo" in finding.message.lower() for finding in findings)


def test_readme_audit_flags_real_parallelism_claim():
    findings = audit_readme_text("paralelismo real ja funciona.\n")

    assert findings
    assert "parallel" in findings[0].message.lower()


def test_readme_audit_flags_complete_autonomy_claim():
    findings = audit_readme_text("Bali e autonomo completo.\n")

    assert findings
    assert "autonomy" in findings[0].message.lower() or "autonom" in findings[0].message.lower()
