#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess

# Extensões perigosas que nunca devem ser comitadas
PERIGOUS_EXTENSIONS = ('.env', '.pem', '.key', '.pkcs12', '.pfx', '.p12')

# Padrões comuns de chaves de API expostas
SECRET_PATTERNS = {
    "OpenAI / Anthropic API Key": re.compile(r"sk-[a-zA-Z0-9_-]{32,}"),
    "Google / Gemini API Key": re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Generic Private Key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    "Database URL with Credentials": re.compile(r"postgresql://[a-zA-Z0-9_:-]+@[a-zA-Z0-9.-]+:[0-9]+/"),
}

def print_banner(message):
    border = "=" * 70
    banner = f"""
{border}
  [AGENT SHIELD] -- COMITÊ DE SEGURANÇA BALI-AGENT
{border}
  {message}
{border}
"""
    print(banner, file=sys.stderr)

def get_staged_files():
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], 
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in res.stdout.split('\n') if f.strip()]
    except Exception as e:
        print(f"[!] Erro ao listar arquivos do git: {e}", file=sys.stderr)
        return []

def scan_file(filepath):
    # Ignora arquivos binários ou muito grandes
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return None
        
    # Verifica extensão perigosa pelo nome
    basename = os.path.basename(filepath)
    if basename.endswith(PERIGOUS_EXTENSIONS) or basename == '.env':
        return f"Arquivo de credenciais bloqueado para commit: {filepath}"
        
    # Tenta ler e auditar o conteúdo
    try:
        # Se for um arquivo de texto, lê
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for name, pattern in SECRET_PATTERNS.items():
            match = pattern.search(content)
            if match:
                # Extrai a linha do match para mostrar no aviso (mascarando a chave)
                matched_text = match.group(0)
                masked_text = matched_text[:6] + "..." + matched_text[-4:] if len(matched_text) > 10 else "..."
                return f"Detectada assinatura de {name} ({masked_text}) no arquivo: {filepath}"
    except Exception:
        pass # Ignora falhas de leitura
        
    return None

def main():
    staged_files = get_staged_files()
    violations = []
    
    for filepath in staged_files:
        violation = scan_file(filepath)
        if violation:
            violations.append(violation)
            
    if violations:
        print_banner("COMMIT BLOQUEADO: Risco de vazamento de credenciais!")
        for violation in violations:
            print(f"  [!] {violation}", file=sys.stderr)
        print("\n  Por favor, remova os segredos ou arquivos do commit antes de prosseguir.", file=sys.stderr)
        print("  Dica: adicione arquivos sensíveis no seu .gitignore.", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
        sys.exit(1)
        
    sys.exit(0)

if __name__ == '__main__':
    main()
