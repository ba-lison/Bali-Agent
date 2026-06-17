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


def test_orchestrator_routes_any_task():
    txt = _read("agents/_spine/orchestrator/AGENT.md")
    # Deve operar nos dois modos e rotear QUALQUER pedido pelo time
    for marker in ["Modo Operate", "Modo Greenfield", ".agent/subagent.config.yaml",
                   "nunca trabalha sozinho", "protocols/routing.md"]:
        assert marker in txt, f"marcador ausente no orchestrator: {marker!r}"


def test_planner_decomposes():
    txt = _read("agents/_spine/planner/AGENT.md")
    for marker in ["Planner", "tasks atômicas", "critério de conclusão"]:
        assert marker in txt, f"marcador ausente no planner: {marker!r}"
    # garante que o antigo caminho não sobrou
    assert not (REPO / "agents/task-decomposer").exists(), "task-decomposer deveria ter virado _spine/planner"


def test_reviewer_in_spine():
    assert (REPO / "agents/_spine/reviewer/AGENT.md").is_file()
    assert (REPO / "agents/_spine/reviewer/checklists/pr-checklist.md").is_file()
    assert (REPO / "agents/_spine/reviewer/checklists/security-checklist.md").is_file()
    assert not (REPO / "agents/reviewer").exists(), "reviewer deveria estar em _spine"


def test_no_stale_agent_paths():
    # nenhum arquivo do framework deve apontar para os caminhos antigos da espinha
    stale = ["agents/orchestrator/", "agents/task-decomposer/", "agents/reviewer/"]
    offenders = []
    for md in (REPO / "agents").rglob("*.md"):
        txt = md.read_text(encoding="utf-8")
        for s in stale:
            if s in txt:
                offenders.append(f"{md.relative_to(REPO)} -> {s}")
    assert not offenders, f"referências a caminhos antigos: {offenders}"
