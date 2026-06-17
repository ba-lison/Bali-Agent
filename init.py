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
  [BALI-SUBAGENT AI] -- TIME DE AGENTES HÍBRIDOS (V2)
======================================================================
  Orquestração de engenharia moderna baseada em agentes autônomos.
  LLM-Agnostic | Security-First | Human-in-the-Loop
======================================================================
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        print("[BALI-SUBAGENT AI] -- TIME DE AGENTES HÍBRIDOS (V2)")

def get_target_directory():
    print("Este script inicializa o Bali-Subagent AI no diretório do seu projeto.")
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
        print(f"[!] Aviso: Bali-Subagent v2 já está inicializado neste projeto.")
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
        print("SUCCESS: BALI-SUBAGENT AI INICIALIZADO COM SUCESSO!")
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
        print(f"\nBali-Subagent AI inicializado com sucesso em {target_dir}")
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
