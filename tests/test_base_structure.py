from pathlib import Path
import json
import subprocess
import sys
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


def test_real_subagents_protocol_sections():
    txt = _read("protocols/subagents.md")
    for h in ["# Protocolo de Subagentes Reais", "## Objetivo Master",
              "## Ordem de resolução", "## Falha fechada"]:
        assert h in txt, f"seção ausente em subagents.md: {h!r}"
    assert "role-play" in txt
    assert "Bali Runtime" in txt


def test_memory_protocol_sections():
    txt = _read("protocols/memory.md")
    for h in ["# Protocolo de Memoria Curada", "## Quando Registrar", "## O Que Registrar", "## O Que Nao Registrar"]:
        assert h in txt, f"secao ausente em memory.md: {h!r}"
    assert ".agent/memory.md" in txt


def test_memory_contract_separates_working_state_from_curated_history():
    protocol = _read("protocols/memory.md")
    working = _read("templates/working-context.md")
    readme = _read("README.md")

    assert "## Fonte de Verdade" in protocol
    assert "working-context.md" in protocol
    assert "memory.md" in protocol
    assert "estado vivo" in protocol
    assert "historico curado" in protocol
    assert "nao e historico" in working.lower()
    assert "todo o contexto historico" not in working.lower()
    assert "estado vivo" in readme
    assert "historico curado" in readme


def test_manifest_template_valid():
    data = yaml.safe_load(_read("templates/subagent.config.yaml"))
    assert isinstance(data, dict)
    assert data.get("modo") in ("operate", "greenfield")
    assert "espinha" in data["time"]
    assert {"orchestrator", "planner", "reviewer"}.issubset(set(data["time"]["espinha"]))
    assert "base" in data["time"]
    assert {"discovery", "prd-writer", "sdd-architect"}.issubset(set(data["time"]["base"]))
    assert data["subagents_policy"]["role_play_permitido"] is False
    assert "bali-runtime" in data["subagents_policy"]["fallback_obrigatorio"]
    assert "enforcement_adapters" in data
    assert "bali-runtime" in data["enforcement_adapters"]
    for adapter in ("claude-code", "codex", "opencode", "cursor", "gemini", "antigravity", "ollama"):
        assert adapter in data["enforcement_adapters"]


def test_core_templates_are_project_agnostic():
    checked = [
        "AGENTS.md",
        "README.md",
        "init.py",
        "agents/_setup/AGENT.md",
        "protocols/subagents.md",
        "templates/project-AGENTS.md",
        "templates/subagent.config.yaml",
    ]
    forbidden = ["Movebo", "movebo", "TotalCAD"]
    offenders = []
    for rel in checked:
        txt = _read(rel)
        for phrase in forbidden:
            if phrase in txt:
                offenders.append(f"{rel} -> {phrase}")
    assert not offenders, f"core do framework vazando regra especifica de projeto: {offenders}"


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
        "templates/adapters/antigravity.md",
        "templates/adapters/claude-code.md",
        "templates/adapters/codex.md",
        "templates/adapters/cursor.md",
        "templates/adapters/gemini.md",
        "templates/adapters/ollama.md",
        "templates/adapters/opencode.md",
        "templates/claude_hook.py",
        "templates/claude-settings.json",
        "templates/cursor-rule.mdc",
        "templates/gemini-settings.json",
        "templates/runtime/bali_runtime.py",
        "templates/memory.md",
        "templates/working-context.md",
        "templates/pull_request_template.md",
        "templates/prevent_secrets.py",
        "templates/git-pre-commit-shell",
        "templates/task.md",
        "templates/verify_setup.py",
    ]
    missing = [f for f in expected if not (REPO / f).is_file()]
    assert not missing, f"templates de enforcamento/segurança ausentes: {missing}"


def test_master_objective_requires_real_subagents():
    primary_docs = ["README.md", "AGENTS.md", "templates/project-AGENTS.md"]
    forbidden = [
        "Simulado",
        "simulado",
        "um único modelo vestindo chapéus",
        "um unico modelo vestindo chapeus",
        "qualquer LLM pode assumir qualquer papel",
    ]
    for rel in primary_docs:
        txt = _read(rel)
        for phrase in forbidden:
            assert phrase not in txt, f"{rel} ainda aceita subagents simulados: {phrase!r}"
        assert "Objetivo Master" in txt or "objetivo master" in txt.lower()
        assert "subagentes reais" in txt.lower() or "subagents reais" in txt.lower()


def test_installer_flow(tmp_path):
    import sys
    sys.path.append(str(REPO))
    import init
    from templates import verify_setup

    # Cenário 1: Instalação em pasta vazia (sem Git)
    init.initialize_project(str(REPO), str(tmp_path))

    # Verifica se os arquivos e diretórios corretos foram criados
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "README.md").is_file()
    assert (tmp_path / ".agent").is_dir()
    assert (tmp_path / ".agent/working-context.md").is_file()
    assert (tmp_path / ".agent/memory.md").is_file()
    assert (tmp_path / ".github/pull_request_template.md").is_file()
    assert (tmp_path / ".agent/hooks/prevent_secrets.py").is_file()
    assert (tmp_path / ".agent/subagent.config.yaml").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert "@AGENTS.md" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert (tmp_path / ".agent/team/orchestrator.md").is_file()
    assert (tmp_path / ".agent/team/discovery.md").is_file()
    assert (tmp_path / ".agent/team/prd-writer.md").is_file()
    assert (tmp_path / ".agent/team/sdd-architect.md").is_file()
    assert (tmp_path / ".agent/team/planner.md").is_file()
    assert (tmp_path / ".agent/team/reviewer.md").is_file()
    assert (tmp_path / ".agent/team/spec-implementer.md").is_file()
    assert (tmp_path / ".agent/runtime/bali_runtime.py").is_file()
    for adapter in ("antigravity", "claude-code", "codex", "cursor", "gemini", "ollama", "opencode"):
        assert (tmp_path / f".agent/adapters/{adapter}.md").is_file()
    assert (tmp_path / ".claude/agents/orchestrator.md").is_file()
    assert (tmp_path / ".claude/agents/discovery.md").is_file()
    assert (tmp_path / ".claude/agents/prd-writer.md").is_file()
    assert (tmp_path / ".claude/agents/sdd-architect.md").is_file()
    assert (tmp_path / ".claude/agents/planner.md").is_file()
    assert (tmp_path / ".claude/agents/reviewer.md").is_file()
    assert (tmp_path / ".claude/agents/spec-implementer.md").is_file()
    assert (tmp_path / ".codex/config.toml").is_file()
    assert (tmp_path / ".codex/agents/orchestrator.toml").is_file()
    assert (tmp_path / ".codex/agents/discovery.toml").is_file()
    assert (tmp_path / ".codex/agents/prd-writer.toml").is_file()
    assert (tmp_path / ".codex/agents/sdd-architect.toml").is_file()
    assert (tmp_path / ".codex/agents/planner.toml").is_file()
    assert (tmp_path / ".codex/agents/reviewer.toml").is_file()
    assert (tmp_path / ".codex/agents/spec-implementer.toml").is_file()
    assert (tmp_path / ".opencode/agents/orchestrator.md").is_file()
    assert (tmp_path / ".opencode/agents/discovery.md").is_file()
    assert (tmp_path / ".opencode/agents/prd-writer.md").is_file()
    assert (tmp_path / ".opencode/agents/sdd-architect.md").is_file()
    assert (tmp_path / ".opencode/agents/planner.md").is_file()
    assert (tmp_path / ".opencode/agents/reviewer.md").is_file()
    assert (tmp_path / ".opencode/agents/spec-implementer.md").is_file()
    opencode_config = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert ".agent/protocols/subagents.md" in opencode_config["instructions"]
    assert ".agent/protocols/routing.md" in opencode_config["instructions"]
    claude_settings = json.loads((tmp_path / ".claude/settings.json").read_text(encoding="utf-8"))
    assert "SessionStart" in claude_settings["hooks"]
    assert "UserPromptSubmit" in claude_settings["hooks"]
    assert (tmp_path / ".cursor/rules/bali-agent.mdc").is_file()
    assert (tmp_path / ".gemini/settings.json").is_file()
    assert (tmp_path / ".antigravity/skills/bali-agent/SKILL.md").is_file()
    assert (tmp_path / ".agent/agents/_spine/orchestrator/AGENT.md").is_file()
    assert (tmp_path / ".agent/protocols/routing.md").is_file()
    assert (tmp_path / ".agent/templates/subagent.config.yaml").is_file()
    assert verify_setup.verify(str(tmp_path)) == []

    list_result = subprocess.run(
        [sys.executable, str(tmp_path / ".agent/runtime/bali_runtime.py"), "--root", str(tmp_path), "list-agents"],
        capture_output=True, text=True, check=True
    )
    assert "orchestrator" in list_result.stdout
    assert "planner" in list_result.stdout
    assert "reviewer" in list_result.stdout
    assert "spec-implementer" in list_result.stdout

    create_result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "create-agent",
            "--id",
            "spec-payments",
            "--scope",
            "Especialista reutilizavel em pagamentos, checkout e webhooks.",
        ],
        capture_output=True, text=True, check=True
    )
    assert "Subagente criado" in create_result.stdout
    assert (tmp_path / ".agent/team/spec-payments.md").is_file()
    assert (tmp_path / ".claude/agents/spec-payments.md").is_file()
    assert (tmp_path / ".codex/agents/spec-payments.toml").is_file()
    assert (tmp_path / ".opencode/agents/spec-payments.md").is_file()
    assert "spec-payments" in (tmp_path / ".agent/subagent.config.yaml").read_text(encoding="utf-8")
    assert "spec-payments" in (tmp_path / ".agent/output/subagents-created.md").read_text(encoding="utf-8")

    remember_result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "remember",
            "--kind",
            "task",
            "--title",
            "setup validado",
            "--summary",
            "time base e adapters verificados",
            "--files",
            ".agent/team, .agent/adapters",
            "--tests",
            "verify_setup OK",
        ],
        capture_output=True, text=True, check=True
    )
    assert "Memoria curada atualizada" in remember_result.stdout
    assert "setup validado" in (tmp_path / ".agent/memory.md").read_text(encoding="utf-8")
    assert "**ID:**" in (tmp_path / ".agent/memory.md").read_text(encoding="utf-8")

    referenced_memory_result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "remember",
            "--kind",
            "commit",
            "--title",
            "estrutura de memoria",
            "--ref",
            "abc1234",
            "--summary",
            "limita working-context ao estado vivo e memory ao historico curado",
            "--tests",
            "pytest tests/test_base_structure.py",
        ],
        capture_output=True, text=True, check=True
    )
    assert "Memoria curada atualizada" in referenced_memory_result.stdout
    memory_text = (tmp_path / ".agent/memory.md").read_text(encoding="utf-8")
    assert "- **Ref:** abc1234" in memory_text

    secret_memory_result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "remember",
            "--kind",
            "task",
            "--title",
            "segredo",
            "--summary",
            "nao salvar token sk-test1234567890abcdef",
        ],
        capture_output=True, text=True
    )
    assert secret_memory_result.returncode != 0
    assert "segredo" in secret_memory_result.stderr.lower()
    assert "sk-test1234567890abcdef" not in (tmp_path / ".agent/memory.md").read_text(encoding="utf-8")

    dry_run_result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "run",
            "--dry-run",
            "criar tela de login",
        ],
        capture_output=True, text=True, check=True
    )
    assert "Bali Runtime dry-run" in dry_run_result.stdout
    assert "reviewer" in dry_run_result.stdout

    greenfield_result = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "run",
            "--dry-run",
            "--workflow",
            "greenfield",
            "criar produto novo",
        ],
        capture_output=True, text=True, check=True
    )
    assert "discovery" in greenfield_result.stdout
    assert "prd-writer" in greenfield_result.stdout
    assert "sdd-architect" in greenfield_result.stdout

    specialist_dry_run = subprocess.run(
        [
            sys.executable,
            str(tmp_path / ".agent/runtime/bali_runtime.py"),
            "--root",
            str(tmp_path),
            "run",
            "--dry-run",
            "--specialist",
            "spec-payments",
            "validar checkout",
        ],
        capture_output=True, text=True, check=True
    )
    assert "spec-payments" in specialist_dry_run.stdout
    
    # E garante que as pastas antigas ou indesejadas NÃO foram copiadas para a raiz
    assert not (tmp_path / "agents").exists(), "A pasta agents base nao deveria ser criada na raiz do projeto (deve ficar dentro de .agent/)"

    # Cenário 2: Instalação em projeto Brownfield (com Git e arquivos customizados do usuário)
    user_project = tmp_path / "user_project"
    user_project.mkdir()
    
    # Simula pasta .git do projeto do usuário
    (user_project / ".git").mkdir()
    (user_project / ".claude").mkdir()
    (user_project / ".claude/settings.json").write_text(
        '{"hooks":{"Notification":[{"matcher":"","hooks":[{"type":"command","command":"echo keep"}]}]}}',
        encoding="utf-8"
    )
    
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
    assert (user_project / "CLAUDE.md").is_file()
    assert "@AGENTS.md" in (user_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "@.agent/bootstrap-AGENTS.md" in (user_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert (user_project / ".agent/team/orchestrator.md").is_file()
    assert (user_project / ".agent/subagent.config.yaml").is_file()
    merged_settings = json.loads((user_project / ".claude/settings.json").read_text(encoding="utf-8"))
    assert "Notification" in merged_settings["hooks"]
    assert "SessionStart" in merged_settings["hooks"]
    assert "UserPromptSubmit" in merged_settings["hooks"]
    
    # E garante que o Git Hook foi instalado com sucesso em .git/hooks/pre-commit
    assert (user_project / ".git/hooks/pre-commit").is_file()


def test_verify_setup_logic(tmp_path):
    import sys
    if str(REPO) not in sys.path:
        sys.path.append(str(REPO))
    from templates import verify_setup

    # 1. Sem .agent -> reporta problema
    assert verify_setup.verify(str(tmp_path))

    # 2. Setup completo -> zero problemas
    proj = tmp_path / "ok"
    agent = proj / ".agent"
    team = agent / "team"
    team.mkdir(parents=True)
    (agent / "subagent.config.yaml").write_text(
        "modo: operate\ntime:\n  espinha: [orchestrator, planner, reviewer]\n"
        "subagents_policy:\n  role_play_permitido: false\n  fallback_obrigatorio: adapter-nativo-ou-bali-runtime\n"
        "enforcement_adapters:\n  - bali-runtime\n  - claude-code\n  - codex\n  - opencode\n  - cursor\n  - gemini\n  - antigravity\n", encoding="utf-8")
    for m in ("orchestrator.md", "discovery.md", "prd-writer.md", "sdd-architect.md", "planner.md", "reviewer.md", "spec-x.md"):
        (team / m).write_text("x", encoding="utf-8")
    (agent / "working-context.md").write_text("x", encoding="utf-8")
    (agent / "memory.md").write_text("x", encoding="utf-8")
    (agent / "runtime").mkdir()
    (agent / "runtime" / "bali_runtime.py").write_text("x", encoding="utf-8")
    adapters = agent / "adapters"
    adapters.mkdir()
    for adapter in ("antigravity.md", "claude-code.md", "codex.md", "cursor.md", "gemini.md", "ollama.md", "opencode.md"):
        (adapters / adapter).write_text("x", encoding="utf-8")
    (agent / "hooks").mkdir()
    (agent / "hooks" / "claude_hook.py").write_text("x", encoding="utf-8")
    (proj / ".claude").mkdir()
    (proj / ".claude" / "settings.json").write_text(
        '{"hooks":{"SessionStart":[],"UserPromptSubmit":[]}}',
        encoding="utf-8"
    )
    (proj / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    (proj / ".claude" / "agents").mkdir()
    for m in ("orchestrator.md", "discovery.md", "prd-writer.md", "sdd-architect.md", "planner.md", "reviewer.md", "spec-x.md"):
        (proj / ".claude" / "agents" / m).write_text("x", encoding="utf-8")
    (proj / ".codex" / "agents").mkdir(parents=True)
    (proj / ".codex" / "config.toml").write_text("[agents]\n", encoding="utf-8")
    for m in ("orchestrator.toml", "discovery.toml", "prd-writer.toml", "sdd-architect.toml", "planner.toml", "reviewer.toml", "spec-x.toml"):
        (proj / ".codex" / "agents" / m).write_text("x", encoding="utf-8")
    (proj / ".opencode" / "agents").mkdir(parents=True)
    (proj / "opencode.json").write_text(
        '{"instructions":["AGENTS.md",".agent/protocols/subagents.md",".agent/protocols/routing.md"]}',
        encoding="utf-8"
    )
    for m in ("orchestrator.md", "discovery.md", "prd-writer.md", "sdd-architect.md", "planner.md", "reviewer.md", "spec-x.md"):
        (proj / ".opencode" / "agents" / m).write_text("x", encoding="utf-8")
    (proj / ".cursor" / "rules").mkdir(parents=True)
    (proj / ".cursor" / "rules" / "bali-agent.mdc").write_text("x", encoding="utf-8")
    (proj / ".gemini").mkdir()
    (proj / ".gemini" / "settings.json").write_text("{}", encoding="utf-8")
    (proj / ".antigravity" / "skills" / "bali-agent").mkdir(parents=True)
    (proj / ".antigravity" / "skills" / "bali-agent" / "SKILL.md").write_text("x", encoding="utf-8")
    assert verify_setup.verify(str(proj)) == []

    # 3. Falta o hook declarado -> reporta
    (agent / "hooks" / "claude_hook.py").unlink()
    assert any("claude-code" in p for p in verify_setup.verify(str(proj)))

    # 4. Falta espelho nativo de subagentes -> reporta
    (agent / "hooks" / "claude_hook.py").write_text("x", encoding="utf-8")
    (proj / ".claude" / "agents" / "reviewer.md").unlink()
    assert any(".claude" in p and "reviewer" in p for p in verify_setup.verify(str(proj)))


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

