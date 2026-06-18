# -*- coding: utf-8 -*-
"""HandoffBus module for message passing between subagents."""

import os
import json
import time
from pathlib import Path
from typing import List

def _handoff_bus_load(bus_path: Path) -> List[dict]:
    """Load handoff messages from file."""
    if not bus_path.is_file():
        return []
    try:
        with bus_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def _handoff_bus_save(bus_path: Path, messages: List[dict]) -> None:
    """Save handoff messages atomically via a temporary file."""
    bus_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = bus_path.with_suffix(".json.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, bus_path)
    except Exception as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        raise e

def _handoff_bus_send(bus_path: Path, from_agent: str, to_agent: str, content: str) -> str:
    """Send a message to another agent via the HandoffBus."""
    messages = _handoff_bus_load(bus_path)
    msg_id = f"{int(time.time() * 1000)}-{from_agent}-{to_agent}"
    entry = {
        "id": msg_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "from": from_agent,
        "to": to_agent,
        "content": content,
        "read": False,
    }
    messages.append(entry)
    _handoff_bus_save(bus_path, messages)
    return f"Mensagem enviada para '{to_agent}' (id={msg_id})."

def _handoff_bus_receive(bus_path: Path, agent_name: str) -> str:
    """Receive and mark as read all pending messages for agent_name."""
    messages = _handoff_bus_load(bus_path)
    pending = [m for m in messages if m.get("to") == agent_name and not m.get("read")]
    if not pending:
        return "Nenhuma mensagem pendente no HandoffBus."
    
    # Mark as read
    for m in messages:
        if m.get("to") == agent_name and not m.get("read"):
            m["read"] = True
            
    _handoff_bus_save(bus_path, messages)
    
    lines = []
    for m in pending:
        lines.append(f"[{m['timestamp']}] DE {m['from']}: {m['content']}")
    return "\n".join(lines)
