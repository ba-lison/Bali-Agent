# -*- coding: utf-8 -*-
"""README claim scanner for unsupported Bali-Agent promises."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadmeAuditFinding:
    line: int
    severity: str
    message: str
    text: str


_PATTERNS = [
    (
        ("garante", "isolamento", "qualquer host"),
        "Do not claim guaranteed native isolation in every host; say native execution depends on the host or Bali Runtime.",
    ),
    (
        ("sempre", "modelo"),
        "Do not claim mandatory multi-modelo; model_policy is declarative unless the host or wrapper supports it.",
    ),
    (
        ("sempre", "modelos"),
        "Do not claim mandatory multi-modelo; model_policy is declarative unless the host or wrapper supports it.",
    ),
    (
        ("paralelismo real", "garante"),
        "Do not claim real parallel execution; runtime currently requires sequential execution and max_parallel 1.",
    ),
    (
        ("autonomo completo", "orquestrador"),
        "Do not claim complete autonomy; routing depends on LLM JSON contracts and host/runtime configuration.",
    ),
]

_QUALIFIERS = (
    "depende do host",
    "depende da ferramenta",
    "depende do adapter",
    "depende do runtime",
    "nao e",
    "nao e promessa fechada",
    "nao garantido",
    "not delivered",
)


def _has_all(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(needle in lowered for needle in needles)


def _has_qualifier(text: str) -> bool:
    lowered = text.lower()
    return any(qualifier in lowered for qualifier in _QUALIFIERS)


def audit_readme_text(text: str) -> list[ReadmeAuditFinding]:
    findings: list[ReadmeAuditFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _has_qualifier(line):
            continue
        for needles, message in _PATTERNS:
            if _has_all(line, needles):
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
