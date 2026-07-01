from pathlib import Path

from bali_agent.readme_audit import audit_readme_text


def test_current_readme_names_critical_capability_limits():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "runtime.parallel_execution" in text
    assert "host.universal_native_isolation" in text
    assert "model.mandatory_multi_model" in text
    assert "BALI_SUBAGENT_RUNNER" in text
    assert "routing_plan" in text


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
