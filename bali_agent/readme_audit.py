# -*- coding: utf-8 -*-
"""README claim scanner for unsupported Bali-Agent promises."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class ReadmeAuditFinding:
    line: int
    severity: str
    message: str
    text: str


_PATTERNS = [
    (
        re.compile(r"(?<!nao\s)\bgarante\b.*\bisolamento nativo\b", re.IGNORECASE),
        "Do not claim guaranteed native isolation in every host; say native execution depends on the host or Bali Runtime.",
    ),
    (
        re.compile(r"\bisolamento nativo\b.*\b(?:qualquer host|todos os hosts|independente do host|universal)\b", re.IGNORECASE),
        "Do not claim universal native isolation; native execution still depends on the host or Bali Runtime.",
    ),
    (
        re.compile(r"\b(?:sempre|obrigatoriamente|mandatory)\b.*\bmodel[oa]s?\b.*\b(?:diferentes|por agente|cada agente)\b", re.IGNORECASE),
        "Do not claim mandatory multi-modelo; model_policy is declarative unless the host or wrapper supports it.",
    ),
    (
        re.compile(r"\bcada agente\b.*\btem\b.*\bseu proprio modelo\b", re.IGNORECASE),
        "Do not claim mandatory multi-modelo; model_policy is declarative unless the host or wrapper supports it.",
    ),
    (
        re.compile(r"\bparalelismo real\b.*\b(?:ja funciona|funciona|garante|entregue|ativo)\b", re.IGNORECASE),
        "Do not claim real parallel execution; runtime currently requires sequential execution and max_parallel 1.",
    ),
    (
        re.compile(r"\bexecucao paralela\b.*\b(?:real|de verdade)\b", re.IGNORECASE),
        "Do not claim real parallel execution; runtime currently requires sequential execution and max_parallel 1.",
    ),
    (
        re.compile(r"\b(?:Bali|orquestrador)\s+e\s+autonom[oa]\s+complet[oa]\b", re.IGNORECASE),
        "Do not claim complete autonomy; routing depends on LLM JSON contracts and host/runtime configuration.",
    ),
    (
        re.compile(r"\b(?:Bali|orquestrador)\s+tem\s+autonomia\s+completa\b", re.IGNORECASE),
        "Do not claim complete autonomy; routing depends on LLM JSON contracts and host/runtime configuration.",
    ),
]

_QUALIFIERS = (
    "depende do host",
    "depende da ferramenta",
    "depende do adapter",
    "depende do runtime",
    "nao e promessa fechada",
    "nao garantido",
    "not delivered",
)


def _has_qualifier(text: str) -> bool:
    lowered = text.lower()
    return any(qualifier in lowered for qualifier in _QUALIFIERS)


def audit_readme_text(text: str) -> list[ReadmeAuditFinding]:
    findings: list[ReadmeAuditFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered_line = line.lower()
        if _has_qualifier(lowered_line):
            continue
        for pattern, message in _PATTERNS:
            if pattern.search(lowered_line):
                findings.append(
                    ReadmeAuditFinding(
                        line=line_number,
                        severity="error",
                        message=message,
                        text=line.strip(),
                    )
                )
                break
    return findings


def audit_readme_file(path: Path) -> list[ReadmeAuditFinding]:
    return audit_readme_text(path.read_text(encoding="utf-8"))
