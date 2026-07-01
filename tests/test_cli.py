# -*- coding: utf-8 -*-
"""Unit tests for the CLI commands."""

import pytest
import re
import shutil
import tempfile
import sys
from pathlib import Path
from bali_agent.cli import init_command, verify_command, inspect_runs, capability_report
import templates.verify_setup as verify_setup


def test_verify_setup_reports_unsupported_python(monkeypatch, tmp_path):
    monkeypatch.setattr(verify_setup.sys, "version_info", (3, 10, 9, "final", 0))

    problems = verify_setup.verify(tmp_path)

    assert any("Python 3.11+" in problem for problem in problems)

def test_cli_init_command():
    temp_dir = tempfile.mkdtemp()
    proj_path = Path(temp_dir)
    
    try:
        # Run init command
        res = init_command(proj_path)
        assert res == 0
        
        # Verify folders exist
        assert (proj_path / ".agent").is_dir()
        assert (proj_path / ".agent" / "subagent.config.yaml").is_file()
        assert (proj_path / ".agent" / "team" / "orchestrator.md").is_file()
        core_team = [
            "orchestrator",
            "discovery",
            "prd-writer",
            "sdd-architect",
            "planner",
            "implementer",
            "qa",
            "security",
            "reviewer",
            "recruiter",
            "memory-curator",
            "docs",
        ]
        for agent_id in core_team:
            assert (proj_path / ".agent" / "team" / f"{agent_id}.md").is_file()
        assert (proj_path / ".agent" / "runtime" / "bali_runtime.py").is_file()
        assert (proj_path / ".agent" / "verify_setup.py").is_file()
        assert (proj_path / ".agent" / "run.py").is_file()
        assert (proj_path / ".agent" / ".gitignore").is_file()

        run_text = (proj_path / ".agent" / "run.py").read_text(encoding="utf-8")
        assert ".agent/runtime/bali_runtime.py" in run_text

        manifest_text = (proj_path / ".agent" / "subagent.config.yaml").read_text(encoding="utf-8")
        assert 'runtime_authority: "bali-runtime"' in manifest_text
        assert "product_spine:" in manifest_text
        assert "model_policy:" in manifest_text
        assert "project_fixed:" in manifest_text
        assert "temporary_policy:" in manifest_text
        assert "skills_policy:" in manifest_text
        assert 'store: ".agent/skills"' in manifest_text
        assert 'audit_log: ".agent/skills/AUDIT.md"' in manifest_text
        assert (proj_path / ".agent" / "skills" / "AUDIT.md").is_file()
        
        # Verify verifying setup works
        v_res = verify_command(proj_path)
        assert v_res == 0
    finally:
        shutil.rmtree(temp_dir)

def test_cli_run_delegates_to_installed_runtime(temp_project_dir, monkeypatch):
    import bali_agent.cli as cli

    runtime = temp_project_dir / ".agent" / "runtime" / "bali_runtime.py"
    runtime.write_text("# runtime", encoding="utf-8")
    calls = []

    class Completed:
        returncode = 0

    class BombRunner:
        def __init__(self, root):
            self.root = root

        def run_agent(self, agent_id, prompt):
            raise AssertionError("bali run should delegate to installed Bali Runtime")

    def fake_run(command, *args, **kwargs):
        calls.append(command)
        return Completed()

    monkeypatch.setattr(cli, "Runner", BombRunner)
    monkeypatch.setattr(cli, "subprocess", type("Subprocess", (), {"run": fake_run}), raising=False)

    res = cli.run_command(
        temp_project_dir,
        "Corrigir logins",
        workflow="operate",
        specialist="spec-implementer",
        dry_run=True,
    )

    assert res == 0
    assert calls
    assert calls[0] == [
        sys.executable,
        str(runtime),
        "--root",
        str(temp_project_dir),
        "run",
        "--workflow",
        "operate",
        "--dry-run",
        "--specialist",
        "spec-implementer",
        "Corrigir logins",
    ]


def test_cli_run_dry_run_fallback_does_not_call_runner(tmp_path, monkeypatch, capsys):
    import bali_agent.cli as cli

    calls = []

    class BombRunner:
        def __init__(self, root):
            self.root = root

        def run_agent(self, agent_id, prompt):
            calls.append((agent_id, prompt))
            raise AssertionError("dry-run fallback must not call Runner.run_agent")

    monkeypatch.setattr(cli, "Runner", BombRunner)

    res = cli.run_command(tmp_path, "Criar modulo", workflow="greenfield", dry_run=True)

    output = capsys.readouterr().out
    assert res == 0
    assert calls == []
    assert "Bali Runtime dry-run" in output
    assert "Workflow: greenfield" in output
    assert "Agentes: orchestrator, discovery, prd-writer, sdd-architect, planner, spec-implementer, reviewer" in output


def test_inspect_runs_reads_runtime_output_directory(temp_project_dir, capsys):
    run_dir = temp_project_dir / ".agent" / "output" / "runtime" / "20260630-120000"
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        """{
  "workflow": "greenfield",
  "task": "Criar produto",
  "status": "completed",
  "steps": [{"agent": "prd-writer"}, {"agent": "reviewer"}],
  "artifacts": ["artifacts/prd.md", "artifacts/sdd.md"]
}""",
        encoding="utf-8",
    )

    res = inspect_runs(temp_project_dir)

    output = capsys.readouterr().out
    assert res == 0
    assert "Run ID: 20260630-120000" in output
    assert "Workflow: greenfield" in output
    assert "Status: completed" in output
    assert "Agentes: prd-writer, reviewer" in output
    assert "Artefatos: artifacts/prd.md, artifacts/sdd.md" in output


def test_inspect_runs_reports_dry_run_output(temp_project_dir, capsys):
    run_dir = temp_project_dir / ".agent" / "output" / "runtime" / "20260701-120000"
    run_dir.mkdir(parents=True)
    (run_dir / "dry-run.txt").write_text(
        """Bali Runtime dry-run
Workflow: greenfield
Task: Criar modulo de login
Chain:
1. orchestrator
2. discovery
3. prd-writer
Run dir: .agent/output/runtime/20260701-120000""",
        encoding="utf-8",
    )

    res = inspect_runs(temp_project_dir)

    output = capsys.readouterr().out
    assert res == 0
    assert "Run ID: 20260701-120000" in output
    assert "Tipo: dry-run" in output
    assert "Workflow: greenfield" in output
    assert "Tarefa: Criar modulo de login" in output
    assert "Agentes: orchestrator, discovery, prd-writer" in output


def test_capability_report_separates_delivered_contract_host_and_missing(temp_project_dir, capsys, monkeypatch):
    monkeypatch.delenv("BALI_SUBAGENT_RUNNER", raising=False)
    monkeypatch.delenv("BALI_SUBAGENT_PROVIDER", raising=False)

    res = capability_report(temp_project_dir)

    output = capsys.readouterr().out
    assert res == 0
    assert "Bali Capability Report" in output
    assert "[Delivered]" in output
    assert "[Contract-dependent]" in output
    assert "[Host-dependent]" in output
    assert "[Not delivered]" in output
    assert "Bali Runtime script: available" in output
    assert "Native subagent orchestration: available" in output
    assert "Runtime with external LLM command" not in output
    assert "BALI_LLM_COMMAND" not in output
    assert "Parallel agent execution: not implemented" in output


def test_capability_report_requires_real_runtime_manifest(temp_project_dir, capsys):
    run_dir = temp_project_dir / ".agent" / "output" / "runtime" / "20260701-120000"
    run_dir.mkdir(parents=True)
    (run_dir / "dry-run.txt").write_text("Bali Runtime dry-run\n", encoding="utf-8")

    res = capability_report(temp_project_dir)

    output = capsys.readouterr().out
    assert res == 0
    assert "Runtime manifests: unavailable" in output
    assert "run_manifest.json not found" in output


def test_capability_report_json_output(temp_project_dir, capsys):
    from bali_agent.cli import capability_report
    import json

    res = capability_report(temp_project_dir, as_json=True)

    assert res == 0
    data = json.loads(capsys.readouterr().out)
    assert "delivered" in data
    assert "not_delivered" in data
    assert any(item["id"] == "runtime.parallel_execution" for item in data["not_delivered"])


def test_capability_report_strict_fails_when_not_delivered_exists(temp_project_dir, capsys):
    from bali_agent.cli import capability_report

    res = capability_report(temp_project_dir, strict=True)

    assert res == 1
    assert "Parallel agent execution" in capsys.readouterr().out


def test_pre_commit_hook_template_supports_installed_and_source_repo_paths():
    template_paths = [
        Path("templates/git-pre-commit-shell"),
        Path("bali_agent/templates/git-pre-commit-shell"),
    ]

    for path in template_paths:
        content = path.read_text(encoding="utf-8")
        assert ".agent/hooks/prevent_secrets.py" in content
        assert "templates/prevent_secrets.py" in content
        assert "bali_agent/templates/prevent_secrets.py" in content


def test_audit_readme_command_strict_fails_on_unqualified_claim(tmp_path, capsys):
    from bali_agent.cli import audit_readme_command

    readme = tmp_path / "README.md"
    readme.write_text("Bali garante isolamento nativo em qualquer host.\n", encoding="utf-8")

    res = audit_readme_command(tmp_path, readme="README.md", strict=True)

    assert res == 1
    assert "promessas" in capsys.readouterr().out


def test_audit_readme_command_passes_current_readme(capsys):
    from pathlib import Path
    from bali_agent.cli import audit_readme_command

    res = audit_readme_command(Path.cwd(), readme="README.md", strict=True)

    assert res == 0
    assert "README audit OK" in capsys.readouterr().out


def test_runtime_truth_evaluation_script_documents_required_commands():
    from pathlib import Path

    script = Path("scripts/evaluate_runtime_truth.ps1")
    text = script.read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", text)

    assert "$scriptRoot = $PSScriptRoot" in normalized
    assert "$repoRoot = Split-Path -Parent $scriptRoot" in normalized
    assert "Push-Location $repoRoot" in normalized
    assert "Pop-Location" in normalized
    assert "function Invoke-Step" in normalized
    assert "$LASTEXITCODE" in normalized
    assert "throw" in normalized
    assert not re.search(r"(?m)^\s*python\s", text)
    assert re.search(r"Invoke-Step python @\('-m', 'pytest', '-q'\)", normalized)
    assert re.search(
        r"Invoke-Step python @\('-m', 'py_compile', 'bali_agent\\cli\.py', 'bali_agent\\capabilities\.py', "
        r"'bali_agent\\readme_audit\.py', 'bali_agent\\templates\\runtime\\bali_runtime\.py'\)",
        normalized,
    )
    assert re.search(r"Invoke-Step python @\('-m', 'bali_agent\.cli', '--root', \$tmp, 'init'\)", normalized)
    assert re.search(r"Invoke-Step python @\('-m', 'bali_agent\.cli', '--root', \$tmp, 'verify'\)", normalized)
    assert re.search(r"Invoke-Step python @\('-m', 'bali_agent\.cli', '--root', \$tmp, 'capability-report', '--json'\)", normalized)
    assert re.search(r"Invoke-Step python @\('-m', 'bali_agent\.cli', '--root', '\.', 'audit-readme', '--readme', 'README\.md', '--strict'\)", normalized)
    assert re.search(
        r"try \{.*finally \{.*if \(\$null -ne \$tmp -and \(Test-Path -LiteralPath \$tmp\)\) \{.*Remove-Item -LiteralPath \$tmp -Recurse -Force",
        text,
        re.S,
    )
