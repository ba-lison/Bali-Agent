from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

def _read(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")

def test_spine_files_exist():
    expected = [
        "agents/_spine/orchestrator/AGENT.md",
        "agents/_spine/planner/AGENT.md",
        "agents/_spine/reviewer/AGENT.md",
    ]
    missing = [f for f in expected if not (REPO / f).is_file()]
    assert not missing, f"arquivos da espinha ausentes: {missing}"
