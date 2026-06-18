# -*- coding: utf-8 -*-
"""Memory module with sqlite-backed search indexation and secret detection."""

import os
import sys
import re
import sqlite3
import datetime as _dt
from pathlib import Path
from typing import List, Optional, Union

MEMORY_SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("api token", re.compile(r"\b(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{20,})\b")),
    ("inline credential", re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*=\s*\S+")),
)

def _memory_secret_hit(values: List[Optional[str]]) -> Optional[str]:
    """Check values for secrets and credentials."""
    text = "\n".join(value for value in values if value)
    for name, pattern in MEMORY_SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None

def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "entry"

def _init_db(db_path: Path) -> None:
    """Initialize SQLite database with full-text search table (FTS5 if available, standard table otherwise)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        # Check if FTS5 is enabled
        cursor.execute("SELECT sqlite_compileoption_used('SQLITE_ENABLE_FTS5');")
        fts_available = cursor.fetchone()[0] == 1
        
        if fts_available:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS entries USING fts5(
                    id, kind, title, summary, ref, files, tests, risks, decisions, stamp UNINDEXED
                );
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY,
                    kind TEXT,
                    title TEXT,
                    summary TEXT,
                    ref TEXT,
                    files TEXT,
                    tests TEXT,
                    risks TEXT,
                    decisions TEXT,
                    stamp TEXT
                );
            """)
        conn.commit()
    except Exception:
        # Fallback to standard table on any failure
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id TEXT PRIMARY KEY,
                kind TEXT,
                title TEXT,
                summary TEXT,
                ref TEXT,
                files TEXT,
                tests TEXT,
                risks TEXT,
                decisions TEXT,
                stamp TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()

def _add_entry_to_db(db_path: Path, entry_id: str, kind: str, title: str, summary: str,
                      ref: str, files: str, tests: str, risks: str, decisions: str, stamp: str) -> None:
    _init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        # Insert or replace
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries' AND sql LIKE '%fts5%';")
        is_fts = cursor.fetchone() is not None
        
        if is_fts:
            # FTS5 does not have direct REPLACE/PRIMARY KEY, delete old if any, then insert
            cursor.execute("DELETE FROM entries WHERE id = ?;", (entry_id,))
            cursor.execute("""
                INSERT INTO entries (id, kind, title, summary, ref, files, tests, risks, decisions, stamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (entry_id, kind, title, summary, ref, files, tests, risks, decisions, stamp))
        else:
            cursor.execute("""
                INSERT OR REPLACE INTO entries (id, kind, title, summary, ref, files, tests, risks, decisions, stamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (entry_id, kind, title, summary, ref, files, tests, risks, decisions, stamp))
        conn.commit()
    except Exception as e:
        print(f"[!] Erro ao salvar no SQLite: {e}", file=sys.stderr)
    finally:
        conn.close()

def remember(root: Path, kind: str, title: str, summary: str,
             ref: Optional[str] = None, files: Optional[str] = None,
             tests: Optional[str] = None, risks: Optional[str] = None,
             decisions: Optional[str] = None) -> int:
    """Record a curated entry in memory.md and index it in memory.db."""
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
    
    # 1. Update memory.md
    entry = [
        f"\n## {stamp} - {kind}: {title}",
        "",
        f"- **ID:** {entry_id}",
    ]
    if ref:
        entry.append(f"- **Ref:** {ref}")
    entry.append(f"- **Resumo:** {summary}")
    if decisions:
        entry.append(f"- **Decisoes:** {decisions}")
    if files:
        entry.append(f"- **Arquivos/artefatos:** {files}")
    if tests:
        entry.append(f"- **Verificacao:** {tests}")
    if risks:
        entry.append(f"- **Riscos/pendencias:** {risks}")
    entry.append("")

    memory_md = root / ".agent" / "memory.md"
    memory_md.parent.mkdir(parents=True, exist_ok=True)
    if not memory_md.exists():
        memory_md.write_text("# Memoria Curada do Projeto\n", encoding="utf-8")
    with memory_md.open("a", encoding="utf-8") as f:
        f.write("\n".join(entry))

    # 2. Index in memory.db
    db_path = root / ".agent" / "memory.db"
    _add_entry_to_db(
        db_path, entry_id, kind, title, summary,
        ref or "", files or "", tests or "", risks or "", decisions or "", stamp
    )
    print(f"Memoria curada atualizada e indexada: {memory_md.relative_to(root)}")
    return 0

def search_memory(root: Path, query: str) -> str:
    """Search for relevant entries in memory.db using SQLite FTS5 or simple text matching."""
    db_path = root / ".agent" / "memory.db"
    memory_md = root / ".agent" / "memory.md"
    
    if not db_path.exists():
        # Fallback to reading file if database doesn't exist
        if not memory_md.exists():
            return "Nenhuma memória histórica gravada ainda."
        return _search_fallback_file(memory_md, query)
        
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        # Determine if using FTS5 table
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries' AND sql LIKE '%fts5%';")
        is_fts = cursor.fetchone() is not None
        
        if is_fts:
            # Query FTS5 table using MATCH
            clean_query = " OR ".join(f'"{q}"' for q in query.split() if q)
            if not clean_query:
                clean_query = f'"{query}"'
            cursor.execute("""
                SELECT stamp, kind, title, id, ref, summary, decisions, files, tests, risks
                FROM entries
                WHERE entries MATCH ?
                LIMIT 5;
            """, (clean_query,))
        else:
            # Query standard table using LIKE or simple token scoring
            words = [w for w in query.split() if len(w) >= 3]
            if words:
                like_clauses = " OR ".join(["summary LIKE ? OR title LIKE ? OR decisions LIKE ?"] * len(words))
                params = []
                for w in words:
                    params.extend([f"%{w}%", f"%{w}%", f"%{w}%"])
                query_sql = f"""
                    SELECT stamp, kind, title, id, ref, summary, decisions, files, tests, risks
                    FROM entries
                    WHERE {like_clauses}
                    LIMIT 5;
                """
                cursor.execute(query_sql, params)
            else:
                cursor.execute("""
                    SELECT stamp, kind, title, id, ref, summary, decisions, files, tests, risks
                    FROM entries
                    WHERE summary LIKE ? OR title LIKE ?
                    LIMIT 5;
                """, (f"%{query}%", f"%{query}%"))
                
        rows = cursor.fetchall()
        if not rows:
            return f"Nenhuma entrada histórica encontrada na busca por: '{query}'"
            
        results = []
        for r in rows:
            stamp, kind, title, entry_id, ref, summary, decisions, files, tests, risks = r
            entry = [
                f"## {stamp} - {kind}: {title}",
                f"- **ID:** {entry_id}",
            ]
            if ref:
                entry.append(f"- **Ref:** {ref}")
            entry.append(f"- **Resumo:** {summary}")
            if decisions:
                entry.append(f"- **Decisoes:** {decisions}")
            if files:
                entry.append(f"- **Arquivos/artefatos:** {files}")
            if tests:
                entry.append(f"- **Verificacao:** {tests}")
            if risks:
                entry.append(f"- **Riscos/pendencias:** {risks}")
            results.append("\n".join(entry))
            
        return "\n\n".join(results)
    except Exception as e:
        print(f"[!] Erro ao buscar no SQLite ({e}). Usando fallback de arquivo.", file=sys.stderr)
        return _search_fallback_file(memory_md, query)
    finally:
        conn.close()

def _search_fallback_file(memory_md: Path, query: str) -> str:
    """Alternative search parser that scans the memory.md markdown directly."""
    if not memory_md.exists():
        return "Nenhuma memória histórica gravada ainda."
    try:
        content = memory_md.read_text(encoding="utf-8")
        entries = content.split("## ")
        matching_entries = []
        for entry in entries:
            if not entry.strip():
                continue
            if query.lower() in entry.lower():
                matching_entries.append("## " + entry.strip())
        if not matching_entries:
            return f"Nenhuma entrada histórica encontrada na busca por: '{query}'"
        return "\n\n".join(matching_entries[:5])
    except Exception as e:
        return f"Erro ao acessar memória: {e}"
