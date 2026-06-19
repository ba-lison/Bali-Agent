# -*- coding: utf-8 -*-
"""Project-local skill creation with an append-only audit trail."""

import datetime as _dt
import re
from pathlib import Path

SKILL_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


def _validate_skill_id(skill_id: str) -> str:
    skill_id = (skill_id or "").strip()
    if not SKILL_ID_RE.fullmatch(skill_id):
        raise ValueError("skill_id invalido. Use apenas minusculas, numeros e hifens.")
    return skill_id


def create_or_update_skill(
    root: Path,
    skill_id: str,
    title: str,
    body: str,
    reason: str,
    agent: str,
) -> str:
    """Create or update a project-local skill and append an audit entry."""
    safe_id = _validate_skill_id(skill_id)
    root_abs = Path(root).resolve()
    skills_dir = root_abs / ".agent" / "skills"
    skill_dir = skills_dir / safe_id
    skill_path = skill_dir / "SKILL.md"
    audit_path = skills_dir / "AUDIT.md"

    skill_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    safe_title = (title or safe_id).strip()
    safe_body = (body or "").strip()
    safe_reason = (reason or "sem motivo informado").strip()
    safe_agent = (agent or "unknown").strip()

    content = "\n".join(
        [
            f"# {safe_title}",
            "",
            f"Skill id: `{safe_id}`",
            "",
            "## When to use",
            safe_reason,
            "",
            "## Instructions",
            safe_body,
            "",
        ]
    )
    skill_path.write_text(content, encoding="utf-8")

    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    if not audit_path.exists():
        audit_path.write_text("# Skill Audit\n\n", encoding="utf-8")
    with audit_path.open("a", encoding="utf-8") as audit:
        audit.write(f"- {stamp} `{safe_id}` by `{safe_agent}`: {safe_reason}\n")

    return f"Skill criada/atualizada: .agent/skills/{safe_id}/SKILL.md"
