from pathlib import Path

from bali_agent.capabilities import build_capability_report


def test_capability_report_has_stable_sections(temp_project_dir):
    report = build_capability_report(temp_project_dir)

    assert set(report) == {
        "delivered",
        "contract_dependent",
        "host_dependent",
        "not_delivered",
    }
    assert any(item.id == "cli.installed_structure" for item in report["delivered"])
    assert any(item.id == "runtime.dynamic_routing_plan" for item in report["contract_dependent"])
    assert any(item.id == "runtime.parallel_execution" for item in report["not_delivered"])


def test_capability_catalog_marks_parallel_as_not_delivered(temp_project_dir):
    report = build_capability_report(temp_project_dir)
    parallel = next(item for item in report["not_delivered"] if item.id == "runtime.parallel_execution")

    assert parallel.available is False
    assert "sequential" in parallel.detail
    assert "max_parallel 1" in parallel.detail
