#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import math
import subprocess

# Extensões perigosas que nunca devem ser comitadas
PERIGOUS_EXTENSIONS = ('.pem', '.key', '.pkcs12', '.pfx', '.p12')

# Padrões comuns de chaves de API expostas
SECRET_PATTERNS = {
    "OpenAI / Anthropic API Key": re.compile(r"sk-[a-zA-Z0-9_-]{32,}"),
    "Google / Gemini API Key": re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
    "AWS Access Key ID": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub Personal Access Token": re.compile(r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{82}"),
    "Stripe Live API Key": re.compile(r"(sk|rk)_(live|test)_[a-zA-Z0-9]{24,}"),
    "Slack Token": re.compile(r"xox[bapr]-[0-9]{11,13}-[0-9]{11,13}-[a-zA-Z0-9]{24}"),
    "Generic Private Key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
}

# Regex to match key/secret assignments like KEY = "value" or "key": "value" or KEY=value
# Group 1: key name, Group 2: quotes (optional), Group 3: value
ASSIGNMENT_PATTERN = re.compile(
    r'(?i)(key|secret|token|password|passwd|pwd|credential|auth|private|token)[a-zA-Z0-9_\-\.\:\s]*'
    r'[=:][\s]*'
    r'([\'"]?)([a-zA-Z0-9_\-\+\/\\=!@#$%^&*()]{10,})\2'
)

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

def calculate_entropy(s):
    if not s:
        return 0.0
    freq = {}
    for char in s:
        freq[char] = freq.get(char, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / len(s)
        entropy -= p * math.log2(p)
    return entropy

def is_high_entropy_secret(value):
    if len(value) < 10:
        return False
        
    val_lower = value.lower()
    placeholders = [
        'placeholder', 'example', 'dummy', 'template', 'your', 'insert', 
        'change', 'todo', 'xxxx', '123456', 'mock', 'fake', 'secret_here', 
        'token_here', 'password_here', 'key_here', 
        'process.env', '${', '{{', '}}'
    ]
    for p in placeholders:
        if p in val_lower:
            return False
            
    if len(set(value)) <= 3:
        return False

    entropy = calculate_entropy(value)
    
    # Check if hex-encoded
    is_hex = all(c in '0123456789abcdefABCDEF-_' for c in value)
    
    if is_hex:
        return len(value) >= 16 and entropy > 3.2
    else:
        return len(value) >= 12 and entropy > 3.5

def is_sensitive_db_url(url):
    # Match user:password in DB URL: postgresql://user:password@host:port/db
    match = re.search(r"[a-zA-Z0-9_+.-]+://([^:@\n]+):([^:@\n]+)@", url)
    if not match:
        return False
    user, password = match.group(1), match.group(2)
    common_dev_credentials = {'postgres', 'root', 'admin', 'password', 'pass', '123456', 'secret', 'db_pass', 'user'}
    if user.lower() in common_dev_credentials and password.lower() in common_dev_credentials:
        return False
    return is_high_entropy_secret(password) or len(password) > 8

def scan_file(filepath):
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return None
        
    # Ignora arquivos ou caminhos de testes
    normalized_path = filepath.replace('\\', '/').lower()
    if 'tests/' in normalized_path or 'test_' in normalized_path:
        return None
        
    basename = os.path.basename(filepath).lower()
    
    # Bloqueia chaves e certificados por extensão
    if basename.endswith(PERIGOUS_EXTENSIONS):
        return f"Arquivo de credenciais bloqueado para commit: {filepath}"
        
    # Tenta ler e auditar o conteúdo
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # 1. Verifica padrões estáticos conhecidos
        for name, pattern in SECRET_PATTERNS.items():
            match = pattern.search(content)
            if match:
                matched_text = match.group(0)
                masked_text = matched_text[:6] + "..." + matched_text[-4:] if len(matched_text) > 10 else "..."
                return f"Detectada assinatura de {name} ({masked_text}) no arquivo: {filepath}"
                
        # 2. Verifica URLs de banco de dados
        # Procura padrões de URL com credenciais
        db_urls = re.findall(r"[a-zA-Z0-9_+.-]+://[a-zA-Z0-9_:-]+@[a-zA-Z0-9.-]+:[0-9]+/\S*", content)
        for url in db_urls:
            if is_sensitive_db_url(url):
                return f"Detectada URL de banco de dados com credenciais sensíveis no arquivo: {filepath}"
                
        # 3. Verifica atribuições de segredos e alta entropia por linha
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            # Procura por atribuições de variáveis
            match = ASSIGNMENT_PATTERN.search(line)
            if match:
                var_name, _, value = match.groups()
                if is_high_entropy_secret(value):
                    masked_val = value[:3] + "..." + value[-3:] if len(value) > 6 else "..."
                    return f"Possível segredo de alta entropia detectado na linha {i} (variável '{var_name}', valor '{masked_val}') do arquivo: {filepath}"
                    
            # Se for um arquivo .env real (não exemplo/template) e contiver atribuições que parecem segredos genéricos
            if '.env' in basename:
                harmless_suffixes = ('.example', '.template', '.dist', '.sample', '.defaults')
                if not basename.endswith(harmless_suffixes):
                    # Em arquivos .env reais, qualquer atribuição de chave/senha longa e não-placeholder deve ser considerada sensível
                    env_match = re.match(r"^\s*([a-zA-Z0-9_-]+)\s*=\s*(['\"]?)(.*?)\2\s*$", line)
                    if env_match:
                        var_name, _, value = env_match.groups()
                        if len(value) > 8 and is_high_entropy_secret(value):
                            return f"Arquivo .env contém credencial sensível na linha {i} (variável '{var_name}')"
                            
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
