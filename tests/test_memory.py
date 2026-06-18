# -*- coding: utf-8 -*-
"""Unit tests for the memory indexing and retrieval module."""

import os
from pathlib import Path
import pytest

from templates.core.memory import remember, search_memory, _memory_secret_hit

def test_memory_secret_hit():
    assert _memory_secret_hit(["Some normal text", "sk-1234567890abcdef1234567890abcdef"]) == "api token"
    assert _memory_secret_hit(["Private key here", "-----BEGIN RSA PRIVATE KEY-----"]) == "private key"
    assert _memory_secret_hit(["Normal string"]) is None

def test_remember_and_search(temp_project_dir):
    # Test valid memory saving
    res = remember(
        temp_project_dir,
        kind="decision",
        title="Decisão de Banco de Dados",
        summary="Escolhemos SQLite para indexação local leve.",
        decisions="Usar sqlite3 sem dependências nativas.",
        files="templates/core/memory.py"
    )
    assert res == 0
    
    # Check that memory.md file was updated
    memory_md = temp_project_dir / ".agent" / "memory.md"
    assert memory_md.is_file()
    md_content = memory_md.read_text(encoding="utf-8")
    assert "Decisão de Banco de Dados" in md_content
    
    # Test memory search
    search_res = search_memory(temp_project_dir, "Banco de Dados")
    assert "Decisão de Banco de Dados" in search_res
    assert "Escolhemos SQLite" in search_res
    
    # Test secret hit rejection
    res_secret = remember(
        temp_project_dir,
        kind="decision",
        title="Senha secreta",
        summary="A api key sk-1234567890abcdef1234567890abcdef foi adicionada."
    )
    assert res_secret == 2 # Rejected due to secret hit
