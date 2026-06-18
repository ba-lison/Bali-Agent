#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bali Runtime: fallback universal para subagentes reais.

Este runtime existe para ambientes sem subagentes nativos. Ele executa cada
agente como uma etapa isolada, com prompt e output próprios. Qualquer LLM/CLI
pode ser plugado via BALI_LLM_COMMAND.

Exemplo:
  BALI_LLM_COMMAND='ollama run llama3.1 < {prompt_file}' \
    python .agent/runtime/bali_runtime.py run "corrigir login"
"""

import argparse
import datetime as _dt
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time as _time


SPINE = ("orchestrator", "planner", "reviewer")
BASE_AGENTS = ("discovery", "prd-writer", "sdd-architect")
SPEC_ID_RE = re.compile(r"^spec-[a-z0-9][a-z0-9-]*$")
MEMORY_SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("api token", re.compile(r"\b(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,})\b")),
    ("inline credential", re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*=\s*\S+")),
)


def _root(path):
    return Path(path).resolve()


def _agent_dir(root):
    return root / ".agent" / "team"


def _runtime_dir(root):
    return root / ".agent" / "runtime"


def _output_dir(root):
    return root / ".agent" / "output" / "runtime"


def _agent_output_dir(root):
    return root / ".agent" / "output"


def _memory_path(root):
    return root / ".agent" / "memory.md"


def _agent_files(root):
    team = _agent_dir(root)
    if not team.is_dir():
        return {}
    agents = {}
    for path in sorted(team.glob("*.md")):
        agents[path.stem] = path
    return agents


def _read(path):
    return path.read_text(encoding="utf-8")


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _escape_yaml(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "entry"


def _memory_secret_hit(values):
    text = "\n".join(value for value in values if value)
    for name, pattern in MEMORY_SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None


def verify(root):
    problems = []
    agent_root = root / ".agent"
    if not agent_root.is_dir():
        problems.append("Pasta .agent ausente")
        return problems

    manifest = agent_root / "subagent.config.yaml"
    if not manifest.is_file():
        problems.append("Manifesto ausente: .agent/subagent.config.yaml")
    else:
        manifest_text = _read(manifest)
        if "role_play_permitido: false" not in manifest_text:
            problems.append("Manifesto deve conter subagents_policy.role_play_permitido: false")
        if "bali-runtime" not in manifest_text:
            problems.append("Manifesto deve exigir fallback com bali-runtime")
        if "enforcement_adapters:" not in manifest_text:
            problems.append("Manifesto deve declarar enforcement_adapters")
        elif "- bali-runtime" not in manifest_text:
            problems.append("Manifesto deve incluir bali-runtime em enforcement_adapters")

    agents = _agent_files(root)
    for name in SPINE:
        if name not in agents:
            problems.append(f"Subagente obrigatorio ausente: .agent/team/{name}.md")
    for name in BASE_AGENTS:
        if name not in agents:
            problems.append(f"Agente base ausente: .agent/team/{name}.md")
    if not any(name.startswith("spec-") for name in agents):
        problems.append("Nenhum especialista real encontrado em .agent/team/spec-*.md")

    if not (_runtime_dir(root) / "bali_runtime.py").is_file():
        problems.append("Bali Runtime ausente: .agent/runtime/bali_runtime.py")
    if not _memory_path(root).is_file():
        problems.append("Memoria curada ausente: .agent/memory.md")

    return problems


def list_agents(root):
    problems = verify(root)
    if problems:
        for problem in problems:
            print(f"[!] {problem}", file=sys.stderr)
        return 1
    for name, path in _agent_files(root).items():
        print(f"{name}\t{path.relative_to(root)}")
    return 0


def _select_specialist(agents, requested=None):
    if requested:
        if requested not in agents:
            raise ValueError(f"Especialista solicitado nao existe: {requested}")
        if not requested.startswith("spec-"):
            raise ValueError(f"Especialista solicitado deve comecar com spec-: {requested}")
        return requested
    for name in sorted(agents):
        if name.startswith("spec-"):
            return name
    return "spec-implementer"


def _append_specialist_to_manifest(root, agent_id, scope):
    manifest = root / ".agent" / "subagent.config.yaml"
    if not manifest.is_file():
        return False

    text = _read(manifest)
    if f"id: {agent_id}" in text or f'id: "{agent_id}"' in text:
        return False

    block = (
        f"    - id: {agent_id}\n"
        f"      arquivo: .agent/team/{agent_id}.md\n"
        f"      escopo: \"{_escape_yaml(scope)}\"\n"
    )
    marker = "  especialistas:\n"
    marker_at = text.find(marker)
    if marker_at == -1:
        addition = (
            "\ntime:\n"
            "  especialistas:\n"
            f"{block}"
        )
        _write(manifest, text.rstrip() + "\n" + addition)
        return True

    insert_start = marker_at + len(marker)
    next_top_level = re.search(r"(?m)^\S", text[insert_start:])
    insert_at = len(text) if next_top_level is None else insert_start + next_top_level.start()
    updated = text[:insert_at].rstrip() + "\n" + block + text[insert_at:]
    _write(manifest, updated)
    return True


def _mirror_claude_agent(root, agent_path):
    native_dir = root / ".claude" / "agents"
    if not native_dir.is_dir():
        return False
    dest = native_dir / agent_path.name
    _write(dest, _read(agent_path))
    return True


def _toml_multiline(value):
    return '"""' + value.replace('"""', '\\"\\"\\"') + '"""'


def _agent_description(agent_id):
    if agent_id == "orchestrator":
        return "Orquestra qualquer pedido e cria subagentes quando faltar especialidade."
    if agent_id == "discovery":
        return "Conduz entrevista, requisitos e contexto de negocio para greenfield/brownfield."
    if agent_id == "prd-writer":
        return "Transforma Discovery em PRD claro, acionavel e validavel."
    if agent_id == "sdd-architect":
        return "Transforma PRD aprovado em SDD tecnico com arquitetura e trade-offs."
    if agent_id == "planner":
        return "Decompoe trabalho nao-trivial em plano executavel por subagentes."
    if agent_id == "reviewer":
        return "Revisa entregas antes da conclusao, focando bugs, riscos e testes."
    return f"Especialista Bali-Agent reutilizavel: {agent_id}."


def _mirror_codex_agent(root, agent_path):
    native_dir = root / ".codex" / "agents"
    if not native_dir.is_dir():
        return False
    agent_id = agent_path.stem
    body = _read(agent_path)
    content = "\n".join([
        f'name = "{agent_id}"',
        f'description = "{_agent_description(agent_id)}"',
        f"developer_instructions = {_toml_multiline(body)}",
        "",
    ])
    _write(native_dir / f"{agent_id}.toml", content)
    return True


def _mirror_opencode_agent(root, agent_path):
    native_dir = root / ".opencode" / "agents"
    if not native_dir.is_dir():
        return False
    agent_id = agent_path.stem
    body = _read(agent_path)
    content = "\n".join([
        "---",
        f"description: {_agent_description(agent_id)}",
        "mode: subagent",
        "---",
        "",
        body,
        "",
    ])
    _write(native_dir / agent_path.name, content)
    return True


def _record_created_agent(root, agent_id, scope):
    log = _agent_output_dir(root) / "subagents-created.md"
    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    line = f"- {stamp} `{agent_id}`: {scope}\n"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text("# Subagentes Criados Dinamicamente\n\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as f:
        f.write(line)


def remember(root, kind, title, summary, ref=None, files=None, tests=None, risks=None, decisions=None):
    problems = verify(root)
    blocking = [p for p in problems if not p.startswith("Nenhum especialista real")]
    if blocking:
        for problem in blocking:
            print(f"[!] {problem}", file=sys.stderr)
        return 1

    allowed = {"task", "commit", "pr", "decision", "incident"}
    if kind not in allowed:
        print(f"[!] kind invalido: {kind}. Use um de: {', '.join(sorted(allowed))}", file=sys.stderr)
        return 2

    secret_hit = _memory_secret_hit([title, summary, ref, files, tests, risks, decisions])
    if secret_hit:
        print(f"[!] Possivel segredo detectado em memoria ({secret_hit}). Entrada nao gravada.", file=sys.stderr)
        return 2

    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    entry_id = f"{stamp.replace(':', '').replace('-', '')}-{kind}-{_slug(title)}"
    entry = [
        f"\n## {stamp} - {kind}: {title}",
        "",
        f"- **ID:** {entry_id}",
    ]
    if ref:
        entry.append(f"- **Ref:** {ref}")
    entry.extend([
        f"- **Resumo:** {summary}",
    ])
    if decisions:
        entry.append(f"- **Decisoes:** {decisions}")
    if files:
        entry.append(f"- **Arquivos/artefatos:** {files}")
    if tests:
        entry.append(f"- **Verificacao:** {tests}")
    if risks:
        entry.append(f"- **Riscos/pendencias:** {risks}")
    entry.append("")

    memory = _memory_path(root)
    if not memory.exists():
        _write(memory, "# Memoria Curada do Projeto\n")
    with memory.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))
    print(f"Memoria curada atualizada: {memory.relative_to(root)}")
    return 0


def create_agent(root, agent_id, scope, overwrite=False):
    problems = verify(root)
    blocking = [p for p in problems if not p.startswith("Nenhum especialista real")]
    if blocking:
        for problem in blocking:
            print(f"[!] {problem}", file=sys.stderr)
        return 1

    if not SPEC_ID_RE.match(agent_id):
        print("[!] id invalido. Use o formato spec-nome-do-especialista.", file=sys.stderr)
        return 2

    agent_path = _agent_dir(root) / f"{agent_id}.md"
    if agent_path.exists() and not overwrite:
        print(f"[!] Subagente ja existe: {agent_path.relative_to(root)}", file=sys.stderr)
        return 2

    body = f"""---
id: {agent_id}
tipo: especialista
created_by: bali-runtime
---

# {agent_id}

Voce e um subagente especialista real do time Bali-Agent.

## Escopo

{scope}

## Contrato

- Execute apenas tarefas dentro deste escopo.
- Registre achados, decisoes e arquivos tocados de forma objetiva.
- Nao substitua Orchestrator, Planner ou Reviewer no mesmo contexto.
- Ao concluir, entregue resultado para o Reviewer como agente separado.
"""
    _write(agent_path, body)
    _append_specialist_to_manifest(root, agent_id, scope)
    mirrors = []
    if _mirror_claude_agent(root, agent_path):
        mirrors.append(".claude/agents")
    if _mirror_codex_agent(root, agent_path):
        mirrors.append(".codex/agents")
    if _mirror_opencode_agent(root, agent_path):
        mirrors.append(".opencode/agents")
    _record_created_agent(root, agent_id, scope)

    print(f"Subagente criado: {agent_path.relative_to(root)}")
    for mirror in mirrors:
        print(f"Espelho nativo atualizado: {mirror}")
    print("Registro atualizado: .agent/output/subagents-created.md")
    return 0


def _write_prompt(run_dir, agent_name, agent_path, task, prior_output):
    prompt_path = run_dir / f"{agent_name}.prompt.md"
    body = [
        f"# Bali Runtime Agent: {agent_name}",
        "",
        "## Agent Definition",
        _read(agent_path),
        "",
        "## Task",
        task,
        "",
        "## Prior Output",
        prior_output or "(none)",
        "",
        "## Output Contract",
        "Return only this agent's result. Do not impersonate other agents.",
    ]
    prompt_path.write_text("\n".join(body), encoding="utf-8")
    return prompt_path


def _run_llm(command_template, prompt_path, output_path, agent_name):
    """Executa o LLM CLI com retry exponencial para erros transitórios.

    Tentativas: 3 (delays: 2s, 4s, 8s).
    FileNotFoundError (binário não encontrado) não é retentatado — é erro fatal.
    """
    command = command_template.format(
        prompt_file=str(prompt_path),
        output_file=str(output_path),
        agent=agent_name,
    )
    max_attempts = 3
    delay = 2
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            with output_path.open("w", encoding="utf-8") as out:
                completed = subprocess.run(
                    command if os.name == "nt" else shlex.split(command),
                    shell=(os.name == "nt"),
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            if completed.returncode == 0:
                return
            last_error = RuntimeError(
                f"LLM command failed for {agent_name} (attempt {attempt}/{max_attempts}) "
                f"with exit {completed.returncode}: {completed.stderr}"
            )
            if attempt < max_attempts:
                print(
                    f"[!] {last_error}. Aguardando {delay}s antes de tentar novamente...",
                    file=sys.stderr,
                )
                _time.sleep(delay)
                delay *= 2
        except FileNotFoundError:
            # Binário não encontrado — erro fatal, não retentar
            raise
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                print(
                    f"[!] Erro inesperado ao executar LLM (attempt {attempt}/{max_attempts}): {exc}. "
                    f"Aguardando {delay}s...",
                    file=sys.stderr,
                )
                _time.sleep(delay)
                delay *= 2

    raise last_error


def _build_chain(agents, workflow, specialist):
    if workflow == "greenfield":
        return ["orchestrator", "discovery", "prd-writer", "sdd-architect", "planner", specialist, "reviewer"]
    return ["orchestrator", "planner", specialist, "reviewer"]


def validate_working_context(content):
    if not content:
        return False
    has_title = "# Working Context" in content
    has_status = ("Status Atual" in content) or ("Milestone" in content)
    has_progress = ("Progresso Recente" in content) or ("Recent Progress" in content)
    return has_title and has_status and has_progress


def save_context_auto_cli(root, task, chain, run_dir):
    context_path = root / ".agent" / "working-context.md"
    if not context_path.is_file():
        return
        
    command_template = os.environ.get("BALI_LLM_COMMAND")
    if not command_template:
        return
        
    print("[*] Iniciando persistência de contexto pós-cadeia CLI...", file=sys.stderr)
    
    backup_path = context_path.with_suffix(".md.bak")
    try:
        if context_path.is_file():
            import shutil
            shutil.copy2(context_path, backup_path)
    except Exception as e:
        print(f"[!] Falha ao criar backup do context: {e}", file=sys.stderr)
        
    history_text = f"Cadeia executada: {' -> '.join(chain)}\n\n"
    for name in chain:
        out_file = run_dir / f"{name}.output.md"
        if out_file.is_file():
            try:
                out_content = out_file.read_text(encoding="utf-8")
                if len(out_content) > 1500:
                    out_content = out_content[:1500] + "\n...(conteúdo truncado para síntese)..."
                history_text += f"=== SAÍDA DO AGENTE '{name}' ===\n{out_content}\n================================\n\n"
            except Exception:
                pass
                
    def apply_deterministic_fallback():
        print("[!] Aplicando fallback determinístico no working-context.md...", file=sys.stderr)
        try:
            current_data = ""
            for p in [backup_path, context_path]:
                if p.is_file():
                    current_data = p.read_text(encoding="utf-8")
                    break
            
            import time
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
            fallback_text = f"\n\n## Histórico Recente (Auto-Save Fallback - {timestamp})\n"
            fallback_text += "A atualização automática via LLM falhou ou veio inválida no modo CLI. Histórico de sessão:\n"
            fallback_text += f"- **Instrução Inicial:** {task}\n"
            fallback_text += f"- **Cadeia Executada:** {' -> '.join(chain)}\n"
            
            context_path.write_text(current_data.rstrip() + fallback_text, encoding="utf-8")
            print("[*] working-context.md atualizado via fallback determinístico.", file=sys.stderr)
        except Exception as e:
            print(f"[!] Falha no fallback determinístico de working-context.md: {e}", file=sys.stderr)

    system_prompt = (
        "Você é a engine de persistência do Bali-Agent. Sua única tarefa é atualizar o arquivo `.agent/working-context.md` "
        "com base nas ações e decisões tomadas no histórico recente da sessão.\n\n"
        "Retorne APENAS o conteúdo completo do arquivo `.agent/working-context.md` atualizado no formato Markdown. "
        "Não adicione comentários, explicações ou tags adicionais (como ```markdown). O arquivo deve ser editado de forma incremental, "
        "atualizando a Milestone se necessário, a Data de Atualização, o Progresso Recente (marcando [x]) e bugs conhecidos."
    )
    
    try:
        working_context = context_path.read_text(encoding="utf-8")
    except Exception:
        working_context = ""
        
    prompt = (
        f"# Prompt de Atualização de Memória de Trabalho\n\n"
        f"Histórico de Cadeia Executada:\n{history_text}\n\n"
        f"Conteúdo Atual do working-context.md:\n{working_context}\n\n"
        f"Contrato de Saída: Retorne apenas o markdown completo atualizado. Sem tags extras de markdown no início ou fim."
    )
    
    prompt_path = run_dir / "sintese.prompt.md"
    output_path = run_dir / "sintese.output.md"
    
    try:
        prompt_path.write_text(f"{system_prompt}\n\n{prompt}", encoding="utf-8")
        
        command = command_template.format(
            prompt_file=str(prompt_path),
            output_file=str(output_path),
            agent="persistence_engine",
        )
        
        with output_path.open("w", encoding="utf-8") as out:
            completed = subprocess.run(
                command if os.name == "nt" else shlex.split(command),
                shell=(os.name == "nt"),
                stdout=out,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120
            )
            
        if completed.returncode != 0:
            print(f"[!] Execução da LLM para síntese falhou: {completed.stderr}", file=sys.stderr)
            apply_deterministic_fallback()
            return
            
        updated_content = output_path.read_text(encoding="utf-8").strip()
        if not updated_content:
            print("[!] Saída vazia na síntese.", file=sys.stderr)
            apply_deterministic_fallback()
            return
            
        cleaned = updated_content
        if cleaned.startswith("```markdown"):
            cleaned = cleaned[11:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        if not validate_working_context(cleaned):
            print("[!] Falha na validação estrutural do working-context.md gerado pela LLM.", file=sys.stderr)
            apply_deterministic_fallback()
            return
            
        tmp_context_path = context_path.with_suffix(".md.tmp")
        tmp_context_path.write_text(cleaned, encoding="utf-8")
        os.replace(tmp_context_path, context_path)
        print("[*] working-context.md atualizado via CLI LLM com sucesso.", file=sys.stderr)
        
    except Exception as e:
        print(f"[!] Erro ao realizar síntese do contexto via CLI: {e}", file=sys.stderr)
        apply_deterministic_fallback()


def run_task(root, task, dry_run=False, specialist_name=None, workflow="operate"):
    problems = verify(root)
    if problems:
        for problem in problems:
            print(f"[!] {problem}", file=sys.stderr)
        return 1

    if not dry_run and os.environ.get("BALI_LLM_PROVIDER"):
        run_script = root / ".agent" / "run.py"
        if not run_script.is_file():
            run_script = root / "templates" / "run.py"
        if run_script.is_file():
            print("[*] BALI_LLM_PROVIDER detectado. Roteando para o motor agêntico com tools...", file=sys.stderr)
            completed = subprocess.run([sys.executable, str(run_script), task])
            return completed.returncode

    agents = _agent_files(root)
    try:
        specialist = _select_specialist(agents, specialist_name)
    except ValueError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2
    if workflow not in ("operate", "greenfield"):
        print("[!] workflow invalido. Use operate ou greenfield.", file=sys.stderr)
        return 2
    chain = _build_chain(agents, workflow, specialist)
    missing = [name for name in chain if name not in agents]
    if missing:
        for name in missing:
            print(f"[!] Agente da cadeia ausente: .agent/team/{name}.md", file=sys.stderr)
        return 1
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = _output_dir(root) / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        plan = [
            "Bali Runtime dry-run",
            f"Workflow: {workflow}",
            f"Task: {task}",
            "Chain:",
            *[f"{index}. {agent_name}" for index, agent_name in enumerate(chain, start=1)],
            f"Run dir: {run_dir.relative_to(root)}",
        ]
        (run_dir / "dry-run.txt").write_text("\n".join(plan), encoding="utf-8")
        print("\n".join(plan))
        return 0

    command_template = os.environ.get("BALI_LLM_COMMAND")
    if not command_template:
        print(
            "[!] BALI_LLM_COMMAND nao configurado. Defina um comando de LLM com "
            "{prompt_file}, {output_file} e {agent}, ou rode com --dry-run.",
            file=sys.stderr,
        )
        return 2

    prior = ""
    try:
        for agent_name in chain:
            prompt_path = _write_prompt(run_dir, agent_name, agents[agent_name], task, prior)
            output_path = run_dir / f"{agent_name}.output.md"
            _run_llm(command_template, prompt_path, output_path, agent_name)
            prior = _read(output_path)
    except Exception as exc:
        print(f"[!] Bali Runtime falhou: {exc}", file=sys.stderr)
        return 1

    if not dry_run:
        save_context_auto_cli(root, task, chain, run_dir)

    print(f"Bali Runtime concluido: {run_dir.relative_to(root)}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bali Runtime")
    parser.add_argument("--root", default=".", help="Raiz do projeto com .agent/")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("verify")
    sub.add_parser("list-agents")
    create = sub.add_parser("create-agent")
    create.add_argument("--id", required=True, help="ID do especialista, ex: spec-payments")
    create.add_argument("--scope", required=True, help="Escopo reutilizavel do especialista")
    create.add_argument("--overwrite", action="store_true")
    mem = sub.add_parser("remember")
    mem.add_argument("--kind", required=True, choices=["task", "commit", "pr", "decision", "incident"])
    mem.add_argument("--title", required=True)
    mem.add_argument("--ref", help="ID externo opcional: task, commit SHA, PR, issue ou incidente")
    mem.add_argument("--summary", required=True)
    mem.add_argument("--files")
    mem.add_argument("--tests")
    mem.add_argument("--risks")
    mem.add_argument("--decisions")
    run = sub.add_parser("run")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--workflow", choices=["operate", "greenfield"], default="operate")
    run.add_argument("--specialist", help="Especialista spec-* a ser chamado nesta execucao")
    run.add_argument("task", nargs="+")

    args = parser.parse_args(argv)
    root = _root(args.root)

    if args.command == "verify":
        problems = verify(root)
        if problems:
            for problem in problems:
                print(f"[!] {problem}", file=sys.stderr)
            return 1
        print("Bali Runtime OK")
        return 0
    if args.command == "list-agents":
        return list_agents(root)
    if args.command == "create-agent":
        return create_agent(root, args.id, args.scope, overwrite=args.overwrite)
    if args.command == "remember":
        return remember(
            root,
            args.kind,
            args.title,
            args.summary,
            ref=args.ref,
            files=args.files,
            tests=args.tests,
            risks=args.risks,
            decisions=args.decisions,
        )
    if args.command == "run":
        return run_task(
            root,
            " ".join(args.task),
            dry_run=args.dry_run,
            specialist_name=args.specialist,
            workflow=args.workflow,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
