from bali_agent.readme_audit import audit_readme_text


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
