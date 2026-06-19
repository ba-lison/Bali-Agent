# -*- coding: utf-8 -*-
"""Claude Code hook — re-injeta instrucoes criticas do Bali-Agent em todo prompt.

Executado via UserPromptSubmit e SessionStart.
Garante que o AGENTS.md e os protocolos essenciais nunca saiam do contexto,
mesmo em sessoes muito longas.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

CRITICAL_FILES = [
    "AGENTS.md",
    ".agent/protocols/subagents.md",
    ".agent/protocols/routing.md",
    ".agent/working-context.md",
]


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _build_context_reminder() -> str:
    """Build a short reminder with the most critical rules."""
    agents_md = _read_file(ROOT / "AGENTS.md")
    if not agents_md:
        return ""

    # Extrai apenas as regras inviolaveis e a topologia
    lines = agents_md.split("\n")
    reminder_lines = []
    in_rules = False
    for line in lines:
        if "Regras inviolaveis" in line or "Regra fundamental" in line:
            in_rules = True
        if in_rules:
            reminder_lines.append(line)
        if in_rules and line.strip() == "" and len(reminder_lines) > 5:
            # Para apos um bloco razoavel
            if any("SEMPRE" in l or "NUNCA" in l for l in reminder_lines[-10:]):
                continue
            in_rules = False

    reminder = "\n".join(reminder_lines) if reminder_lines else ""
    return reminder


def handle_session_start() -> None:
    """SessionStart: verify critical files exist."""
    missing = [f for f in CRITICAL_FILES if not (ROOT / f).is_file()]
    if missing:
        print(f"[Bali-Agent] AVISO: arquivos criticos ausentes: {missing}", file=sys.stderr)


def handle_user_prompt_submit() -> None:
    """UserPromptSubmit: re-inject critical context into every prompt."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    reminder = _build_context_reminder()
    if not reminder:
        return

    # Prepend the reminder to the user's prompt
    prompt = data.get("prompt", "")
    data["prompt"] = (
        "[BALI-AGENT CONTEXT REMINDER — estas regras sao inviolaveis e devem ser "
        "seguidas em toda resposta]\n\n"
        f"{reminder}\n\n"
        "---\n\n"
        f"{prompt}"
    )

    json.dump(data, sys.stdout)


def main() -> None:
    hook_name = sys.argv[1] if len(sys.argv) > 1 else ""
    if hook_name == "SessionStart":
        handle_session_start()
    elif hook_name == "UserPromptSubmit":
        handle_user_prompt_submit()
    else:
        # Unknown hook — pass through silently
        pass


if __name__ == "__main__":
    main()
