#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
try:
    import readline  # Melhora o input no terminal Unix/Linux
except ImportError:
    pass  # Não disponível no Windows, ignorar

def print_banner():
    banner = """
======================================================================
  [BALI-AGENT AI] -- TIME DE AGENTES HÍBRIDOS (V2)
======================================================================
  Orquestração de engenharia moderna baseada em agentes autônomos.
  LLM-Agnostic | Security-First | Human-in-the-Loop
======================================================================
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        print("[BALI-AGENT AI] -- TIME DE AGENTES HÍBRIDOS (V2)")

def get_target_directory():
    print("Este script inicializa o Bali-Agent AI no diretório do seu projeto.")
    print("Os agentes, protocolos, templates e guias serão copiados para a pasta .agent/")
    print("-" * 70)
    
    while True:
        try:
            target = input("Digite o caminho absoluto para o diretório de destino:\n> ").strip()
            if not target:
                print("O caminho não pode ser vazio. Tente novamente.")
                continue
            
            target = os.path.abspath(target)
            return target
        except KeyboardInterrupt:
            print("\nOperação cancelada pelo usuário.")
            sys.exit(0)

def initialize_project(src_dir, target_dir):
    print(f"\n[+] Iniciando cópia para: {target_dir}")
    
    agent_dir = os.path.join(target_dir, ".agent")
    
    # Checar idempotência
    manifest_path = os.path.join(agent_dir, "subagent.config.yaml")
    if os.path.exists(manifest_path):
        print(f"[!] Aviso: Bali-Agent v2 já está inicializado neste projeto.")
        # Se for interativo, perguntamos. Se não for, sobrescrevemos.
        is_interactive = sys.stdin.isatty() and not os.environ.get("PYTEST_CURRENT_TEST")
        if is_interactive:
            try:
                confirm = input("Deseja sobrescrever e atualizar a base do framework? (S/N)\n> ").strip().lower()
                if confirm not in ["s", "sim", "y", "yes"]:
                    print("Operação cancelada pelo usuário.")
                    return False
            except KeyboardInterrupt:
                print("\nOperação cancelada.")
                return False
        else:
            print("[*] Sobrescrevendo a base automaticamente (modo não-interativo/testes).")

    # Criar diretório .agent se não existir
    os.makedirs(agent_dir, exist_ok=True)
            
    # Pastas para copiar para .agent/
    dirs_to_copy = ["agents", "protocols", "templates", "examples"]
    
    for item in dirs_to_copy:
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(agent_dir, item)
        
        if not os.path.exists(src_path):
            print(f"[!] Aviso: Fonte não encontrada: {src_path}")
            continue
            
        try:
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            print(f"[x] Pasta copiada para .agent: {item}/")
        except Exception as e:
            print(f"[!] Erro ao copiar pasta {item}: {e}")
            
    # Arquivos de bootstrap para copiar para a raiz do projeto do usuário
    files_to_copy = [("AGENTS.md", "AGENTS.md"), ("README.md", "README.md")]
    
    for src_file, dest_file in files_to_copy:
        src_path = os.path.join(src_dir, src_file)
        dest_path = os.path.join(target_dir, dest_file)
        if os.path.exists(src_path):
            try:
                if os.path.exists(dest_path):
                    if dest_file == "AGENTS.md":
                        # Copia como bootstrap-AGENTS.md dentro de .agent/ para referência
                        bootstrap_dest = os.path.join(agent_dir, "bootstrap-AGENTS.md")
                        shutil.copy2(src_path, bootstrap_dest)
                        print(f"[x] AGENTS.md existente preservado na raiz. Bootstrap de referência copiado para .agent/bootstrap-AGENTS.md")
                    else:
                        print(f"[x] README.md existente preservado na raiz do projeto (não sobrescrito).")
                else:
                    shutil.copy2(src_path, dest_path)
                    print(f"[x] Arquivo copiado para raiz: {dest_file}")
            except Exception as e:
                print(f"[!] Erro ao copiar {dest_file}: {e}")
            
    # 1. Copiar working-context.md inicial para .agent/working-context.md se não existir
    dest_working_context = os.path.join(agent_dir, "working-context.md")
    if not os.path.exists(dest_working_context):
        src_working_context = os.path.join(src_dir, "templates", "working-context.md")
        if os.path.exists(src_working_context):
            try:
                shutil.copy2(src_working_context, dest_working_context)
                print("[x] Memória de trabalho criada: .agent/working-context.md")
            except Exception as e:
                print(f"[!] Erro ao copiar working-context.md: {e}")

    # 1b. Copiar checklist de tarefa inicial para .agent/task.md se não existir
    dest_task = os.path.join(agent_dir, "task.md")
    if not os.path.exists(dest_task):
        src_task = os.path.join(src_dir, "templates", "task.md")
        if os.path.exists(src_task):
            try:
                shutil.copy2(src_task, dest_task)
                print("[x] Checklist de tarefa criado: .agent/task.md")
            except Exception as e:
                print(f"[!] Erro ao copiar task.md: {e}")

    # 2. Criar .agent/hooks/ e copiar prevent_secrets.py para lá
    hooks_dir = os.path.join(agent_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    src_prevent_secrets = os.path.join(src_dir, "templates", "prevent_secrets.py")
    dest_prevent_secrets = os.path.join(hooks_dir, "prevent_secrets.py")
    if os.path.exists(src_prevent_secrets):
        try:
            shutil.copy2(src_prevent_secrets, dest_prevent_secrets)
            # Damos permissão de execução
            os.chmod(dest_prevent_secrets, 0o755)
            print("[x] Script prevent_secrets.py de segurança copiado para .agent/hooks/")
        except Exception as e:
            print(f"[!] Erro ao copiar prevent_secrets.py: {e}")

    # 2b. Copiar o hook de re-injecao da constituicao (enforcement Claude Code) para .agent/hooks/
    src_claude_hook = os.path.join(src_dir, "templates", "claude_hook.py")
    dest_claude_hook = os.path.join(hooks_dir, "claude_hook.py")
    if os.path.exists(src_claude_hook):
        try:
            shutil.copy2(src_claude_hook, dest_claude_hook)
            os.chmod(dest_claude_hook, 0o755)
            print("[x] Hook de constituicao copiado para .agent/hooks/claude_hook.py")
        except Exception as e:
            print(f"[!] Erro ao copiar claude_hook.py: {e}")

    # 2c. Instalar o settings.json do Claude Code SEM sobrescrever config existente do usuario
    src_claude_settings = os.path.join(src_dir, "templates", "claude-settings.json")
    if os.path.exists(src_claude_settings):
        claude_dir = os.path.join(target_dir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        dest_claude_settings = os.path.join(claude_dir, "settings.json")
        try:
            if os.path.exists(dest_claude_settings):
                ref_settings = os.path.join(claude_dir, "settings.bali-agent.json")
                shutil.copy2(src_claude_settings, ref_settings)
                print("[!] .claude/settings.json ja existe e NAO foi sobrescrito.")
                print('    Referencia salva em .claude/settings.bali-agent.json - copie o bloco "hooks" para o seu settings.json.')
            else:
                shutil.copy2(src_claude_settings, dest_claude_settings)
                print("[x] Enforcement Claude Code instalado: .claude/settings.json (hook por turno).")
        except Exception as e:
            print(f"[!] Erro ao instalar .claude/settings.json: {e}")

    # 2d. Copiar o verificador de setup para .agent/verify_setup.py
    src_verify = os.path.join(src_dir, "templates", "verify_setup.py")
    dest_verify = os.path.join(agent_dir, "verify_setup.py")
    if os.path.exists(src_verify):
        try:
            shutil.copy2(src_verify, dest_verify)
            os.chmod(dest_verify, 0o755)
            print("[x] Verificador de setup copiado para .agent/verify_setup.py")
        except Exception as e:
            print(f"[!] Erro ao copiar verify_setup.py: {e}")

    # 2e. Copiar o runtime engine (run.py) para .agent/run.py
    src_run = os.path.join(src_dir, "templates", "run.py")
    dest_run = os.path.join(agent_dir, "run.py")
    if os.path.exists(src_run):
        try:
            shutil.copy2(src_run, dest_run)
            os.chmod(dest_run, 0o755)
            print("[x] Engine de runtime copiado para .agent/run.py")
        except Exception as e:
            print(f"[!] Erro ao copiar run.py: {e}")

    # 3. Se for um repositório Git, injetar o pre-commit Git hook local (Agent Shield)
    git_dir = os.path.join(target_dir, ".git")
    if os.path.isdir(git_dir):
        git_hooks_dir = os.path.join(git_dir, "hooks")
        os.makedirs(git_hooks_dir, exist_ok=True)
        src_shell_hook = os.path.join(src_dir, "templates", "git-pre-commit-shell")
        dest_shell_hook = os.path.join(git_hooks_dir, "pre-commit")
        if os.path.exists(src_shell_hook):
            try:
                shutil.copy2(src_shell_hook, dest_shell_hook)
                # Damos permissão de execução ao pre-commit hook
                os.chmod(dest_shell_hook, 0o755)
                print("[x] Agent Shield ativado: Git Pre-commit Hook instalado com sucesso!")
            except Exception as e:
                print(f"[!] Erro ao configurar Git Pre-commit Hook: {e}")

    # Garantir criação do output/.gitkeep dentro de .agent/
    output_dir = os.path.join(agent_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    gitkeep_path = os.path.join(output_dir, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w", encoding="utf-8") as f:
            f.write("")
    print("[x] Pasta de outputs configurada: .agent/output/")
    return True

def print_success_instructions(target_dir):
    try:
        print("\n" + "=" * 70)
        print("SUCCESS: BALI-AGENT AI INICIALIZADO COM SUCESSO!")
        print("=" * 70)
        print(f"\nDiretório: {target_dir}\n")
        print("Próximos passos para começar:")
        print("1. Abra o diretório do seu projeto na sua IDE favorita (Cursor, VS Code, etc.).")
        print("2. Abra o chat do seu assistente de IA com o arquivo AGENTS.md aberto/anexado.")
        print("3. Digite a seguinte mensagem no chat para iniciar o setup do time:")
        print("   > Setup do time")
        print("\n4. O Setup Agent assumirá a execução, perfilando sua stack e criando o time sob medida.")
        print("=" * 70 + "\n")
    except UnicodeEncodeError:
        print(f"\nBali-Agent AI inicializado com sucesso em {target_dir}")
        print("Abra AGENTS.md e digite 'Setup do time' no chat.")

def main():
    # Caminho onde o script está localizado (raiz do repositório clonado)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    
    print_banner()
    target_dir = get_target_directory()
    
    # Confirmar antes de continuar
    print(f"\nVocê confirma a inicialização em: {target_dir}? (S/N)")
    try:
        confirm = input("> ").strip().lower()
        if confirm not in ["s", "sim", "y", "yes"]:
            print("Operação cancelada.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperação cancelada.")
        sys.exit(0)
        
    initialize_project(src_dir, target_dir)
    print_success_instructions(target_dir)

if __name__ == "__main__":
    main()
