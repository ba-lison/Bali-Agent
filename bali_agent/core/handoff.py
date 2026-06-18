# -*- coding: utf-8 -*-
"""HandoffBus message-passing engine between active subagents."""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any

class HandoffBus:
    def __init__(self, root_dir: Path):
        self.bus_path = root_dir / ".agent" / "output" / "handoff_bus.json"
        
    def _load_messages(self) -> List[Dict[str, Any]]:
        if not self.bus_path.is_file():
            return []
        try:
            with self.bus_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
            
    def _save_messages(self, messages: List[Dict[str, Any]]) -> None:
        self.bus_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.bus_path.with_suffix(".json.tmp")
        try:
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.bus_path)
        except Exception as e:
            if tmp.is_file():
                try:
                    tmp.unlink()
                except Exception:
                    pass
            raise e
            
    def send(self, from_agent: str, to_agent: str, content: str) -> str:
        """Send message to recipient."""
        messages = self._load_messages()
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
        self._save_messages(messages)
        return f"Mensagem enviada para '{to_agent}' (id={msg_id})."
        
    def receive(self, agent_name: str) -> str:
        """Fetch unread messages for agent_name and mark them as read."""
        messages = self._load_messages()
        pending = [m for m in messages if m.get("to") == agent_name and not m.get("read")]
        if not pending:
            return "Nenhuma mensagem pendente no HandoffBus."
            
        for m in messages:
            if m.get("to") == agent_name and not m.get("read"):
                m["read"] = True
                
        self._save_messages(messages)
        
        lines = []
        for m in pending:
            lines.append(f"[{m['timestamp']}] DE {m['from']}: {m['content']}")
        return "\n".join(lines)
