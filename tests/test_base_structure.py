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


def test_routing_protocol_sections():
    txt = _read("protocols/routing.md")
    for h in ["# Protocolo de Roteamento", "## Triagem", "## Processo proporcional",
              "## Modo Operate", "## Modo Greenfield"]:
        assert h in txt, f"seção ausente em routing.md: {h!r}"


def test_manifest_template_valid():
    data = yaml.safe_load(_read("templates/subagent.config.yaml"))
    assert isinstance(data, dict)
    assert data.get("modo") in ("operate", "greenfield")
    assert "espinha" in data["time"]
    assert {"orchestrator", "planner", "reviewer"}.issubset(set(data["time"]["espinha"]))
    assert "enforcement_adapters" in data


def test_constitution_template():
    txt = _read("templates/project-AGENTS.md").lower()
    assert "nunca trabalha sozinho" in txt
    assert ".agent/subagent.config.yaml" in txt
    assert ".agent/team/" in txt
    assert "reviewer" in txt


def test_base_entrypoint_points_to_spine():
    txt = _read("AGENTS.md")
    assert "agents/_spine/orchestrator/AGENT.md" in txt
    assert "agents/_spine/planner/AGENT.md" in txt
    assert "agents/_spine/reviewer/AGENT.md" in txt
    # não pode mais referenciar NENHUM caminho antigo (prefixo de diretório),
    # incluindo a seção 7 que cita agents/reviewer/checklists/...
    for stale in ["agents/orchestrator/", "agents/task-decomposer/", "agents/reviewer/"]:
        assert stale not in txt, f"caminho antigo ainda no AGENTS.md: {stale}"


def test_readme_structure_mentions_spine():
    txt = _read("README.md")
    assert "_spine/" in txt, "README deve descrever a nova pasta _spine/"
    assert "protocols/routing.md" in txt or "routing.md" in txt


def test_setup_agent_exists():
    expected = [
        "agents/_setup/AGENT.md",
        "agents/_setup/stack-detection.md",
        "agents/_setup/interview.md",
    ]
    missing = [f for f in expected if not (REPO / f).is_file()]
    assert not missing, f"arquivos do setup agent ausentes: {missing}"


def test_specialists_exist():
    expected = [
        "agents/_specialists/_TEMPLATE.md",
        "agents/_specialists/frontend.md",
        "agents/_specialists/backend.md",
        "agents/_specialists/database.md",
        "agents/_specialists/devops.md",
        "agents/_specialists/security.md",
        "agents/_specialists/testing.md",
        "agents/_specialists/docs.md",
        "agents/_specialists/implementer.md",
    ]
    missing = [f for f in expected if not (REPO / f).is_file()]
    assert not missing, f"arquivos de especialistas ausentes: {missing}"
    assert not (REPO / "agents/implementer").exists(), "agents/implementer deveria ter virado _specialists/implementer.md"


def test_templates_exist():
    expected = [
        "templates/claude_hook.py",
        "templates/claude-settings.json",
        "templates/cursor-rule.mdc",
        "templates/gemini-settings.json",
        "templates/working-context.md",
        "templates/prevent_secrets.py",
        "templates/git-pre-commit-shell",
    ]
    missing = [f for f in expected if not (REPO / f).is_file()]
    assert not missing, f"templates de enforcamento/segurança ausentes: {missing}"


def test_installer_flow(tmp_path):
    import sys
    sys.path.append(str(REPO))
    import init

    # Cenário 1: Instalação em pasta vazia (sem Git)
    init.initialize_project(str(REPO), str(tmp_path))

    # Verifica se os arquivos e diretórios corretos foram criados
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "README.md").is_file()
    assert (tmp_path / ".agent").is_dir()
    assert (tmp_path / ".agent/working-context.md").is_file()
    assert (tmp_path / ".agent/hooks/prevent_secrets.py").is_file()
    assert (tmp_path / ".agent/agents/_spine/orchestrator/AGENT.md").is_file()
    assert (tmp_path / ".agent/protocols/routing.md").is_file()
    assert (tmp_path / ".agent/templates/subagent.config.yaml").is_file()
    
    # E garante que as pastas antigas ou indesejadas NÃO foram copiadas para a raiz
    assert not (tmp_path / "agents").exists(), "A pasta agents base nao deveria ser criada na raiz do projeto (deve ficar dentro de .agent/)"

    # Cenário 2: Instalação em projeto Brownfield (com Git e arquivos customizados do usuário)
    user_project = tmp_path / "user_project"
    user_project.mkdir()
    
    # Simula pasta .git do projeto do usuário
    (user_project / ".git").mkdir()
    
    user_readme = user_project / "README.md"
    user_readme.write_text("User Custom README content", encoding="utf-8")
    
    user_agents = user_project / "AGENTS.md"
    user_agents.write_text("User Custom AGENTS rules", encoding="utf-8")

    # Inicializa o framework nesse projeto pré-existente
    init.initialize_project(str(REPO), str(user_project))

    # Garante que os arquivos originais do usuário NÃO foram sobrescritos
    assert user_readme.read_text(encoding="utf-8") == "User Custom README content"
    assert user_agents.read_text(encoding="utf-8") == "User Custom AGENTS rules"

    # E garante que o bootstrap foi salvo na pasta .agent/ para referência
    assert (user_project / ".agent/bootstrap-AGENTS.md").is_file()
    
    # E garante que o Git Hook foi instalado com sucesso em .git/hooks/pre-commit
    assert (user_project / ".git/hooks/pre-commit").is_file()


def test_prevent_secrets_logic(tmp_path):
    import sys
    if str(REPO) not in sys.path:
        sys.path.append(str(REPO))
    from templates import prevent_secrets

    # 1. Arquivo de extensão perigosa (.pem) deve ser bloqueado
    pem_file = tmp_path / "key.pem"
    pem_file.write_text("some content", encoding="utf-8")
    assert prevent_secrets.scan_file(str(pem_file)) is not None

    # 2. Arquivo .env.example com dados fictícios / placeholders deve ser PERMITIDO
    env_example = tmp_path / ".env.example"
    env_example.write_text("STRIPE_KEY=your_stripe_key_placeholder\nDB_PASS=my_dev_password", encoding="utf-8")
    assert prevent_secrets.scan_file(str(env_example)) is None

    # 3. Arquivo .env.local.template com placeholders deve ser PERMITIDO
    env_template = tmp_path / ".env.local.template"
    env_template.write_text("OPENAI_API_KEY=insert-openai-key-here", encoding="utf-8")
    assert prevent_secrets.scan_file(str(env_template)) is None

    # 4. Arquivo .env com valores limpos/inofensivos (PORT, NODE_ENV, etc.) deve ser PERMITIDO
    env_clean = tmp_path / ".env"
    env_clean.write_text("PORT=3000\nNODE_ENV=development\nDEBUG=true", encoding="utf-8")
    assert prevent_secrets.scan_file(str(env_clean)) is None

    # 5. Arquivo .env com chave secreta real (ex: Stripe live key ou alta entropia) deve ser BLOQUEADO
    env_blocked = tmp_path / ".env.local"
    env_blocked.write_text("STRIPE_KEY=" + "sk_live_" + "51Nz8h273hd892h183a9d8a9e2\n", encoding="utf-8")
    assert prevent_secrets.scan_file(str(env_blocked)) is not None

    # 6. Arquivo .env com senha de alta entropia deve ser BLOQUEADO
    env_high_entropy = tmp_path / ".env"
    env_high_entropy.write_text("DB_PASSWORD=" + "9f3d8a9e2c1b" + "4a7d6e5f8b9c0a1b2c3d\n", encoding="utf-8")
    assert prevent_secrets.scan_file(str(env_high_entropy)) is not None

    # 7. Arquivo python (.py) contendo chave OpenAI real deve ser BLOQUEADO
    py_blocked = tmp_path / "main.py"
    py_blocked.write_text("api_key = '" + "sk-" + "proj-" + "AbCdEfGhIjKlMnOpQrStUvWxYz12345678901234'", encoding="utf-8")
    assert prevent_secrets.scan_file(str(py_blocked)) is not None

    # 8. Banco de dados URL com credenciais locais/placeholders deve ser PERMITIDO
    db_local = tmp_path / "config.json"
    db_local.write_text('{"db_url": "postgresql://postgres:postgres@localhost:5432/my_dev_db"}', encoding="utf-8")
    assert prevent_secrets.scan_file(str(db_local)) is None

    # 9. Banco de dados URL com senha real de alta entropia deve ser BLOQUEADO
    db_blocked = tmp_path / "config.json"
    db_blocked.write_text('{"db_url": "postgresql://postgres:' + '9f3d8a9e2c1b' + '@production-db.com:5432/my_prod_db"}', encoding="utf-8")
    assert prevent_secrets.scan_file(str(db_blocked)) is not None

