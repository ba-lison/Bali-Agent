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
  [DEVSQUAD AI] -- TIME DE AGENTES SDLC
======================================================================
  Orquestração de engenharia moderna baseada em agentes autônomos.
  LLM-Agnostic | Security-First | Human-in-the-Loop
======================================================================
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        # Se mesmo com texto simples falhar, print simplificado
        print("[DEVSQUAD AI] -- TIME DE AGENTES SDLC")

def get_target_directory():
    print("Este script inicializa o DevSquad AI no diretório do seu projeto.")
    print("Os agentes, protocolos, templates e guias de governança serão copiados.")
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
    
    # Criar diretório de destino se não existir
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
            print(f"[*] Diretório criado: {target_dir}")
        except Exception as e:
            print(f"[!] Erro ao criar diretório de destino: {e}")
            sys.exit(1)
            
    # Pastas e arquivos para copiar
    items_to_copy = [
        ("agents", "dir"),
        ("protocols", "dir"),
        ("templates", "dir"),
        ("examples", "dir"),
        ("AGENTS.md", "file"),
        ("README.md", "file")
    ]
    
    for item, item_type in items_to_copy:
        src_path = os.path.join(src_dir, item)
        dest_path = os.path.join(target_dir, item)
        
        if not os.path.exists(src_path):
            print(f"[!] Aviso: Fonte não encontrada: {src_path}")
            continue
            
        try:
            if item_type == "dir":
                if os.path.exists(dest_path):
                    # Se o diretório já existe, copiar os arquivos de forma recursiva
                    for root, dirs, files in os.walk(src_path):
                        rel_path = os.path.relpath(root, src_path)
                        target_root = os.path.join(dest_path, rel_path)
                        
                        if not os.path.exists(target_root):
                            os.makedirs(target_root)
                            
                        for file in files:
                            src_file = os.path.join(root, file)
                            dest_file = os.path.join(target_root, file)
                            shutil.copy2(src_file, dest_file)
                else:
                    shutil.copytree(src_path, dest_path)
                print(f"[x] Pasta copiada: {item}/")
            else:
                shutil.copy2(src_path, dest_path)
                print(f"[x] Arquivo copiado: {item}")
        except Exception as e:
            print(f"[!] Erro ao copiar {item}: {e}")
            
    # Garantir criação do output/.gitkeep
    output_dir = os.path.join(target_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    gitkeep_path = os.path.join(output_dir, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w", encoding="utf-8") as f:
            f.write("")
    print("[x] Pasta de outputs configurada: output/")

def print_success_instructions(target_dir):
    try:
        print("\n" + "=" * 70)
        print("SUCCESS: DEVSQUAD AI INICIALIZADO COM SUCESSO!")
        print("=" * 70)
        print(f"\nDiretorio: {target_dir}\n")
        print("Proximos passos para comecar:")
        print("1. Abra o diretorio do seu projeto na sua IDE favorita (Cursor, VS Code, etc.).")
        print("2. Abra o arquivo AGENTS.md na raiz do seu projeto no chat do seu assistente de IA.")
        print("3. Digite o seguinte comando no chat para iniciar seu novo projeto:")
        print("   > Novo projeto: [breve descricao do que voce quer construir]")
        print("\n4. O Orchestrator assumira a execucao e guiara voce por todas as fases do SDLC.")
        print("=" * 70 + "\n")
    except UnicodeEncodeError:
        print(f"\nDevSquad AI inicializado com sucesso em {target_dir}")
        print("Abra AGENTS.md e digite 'Novo projeto: [descricao]' no chat.")

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
