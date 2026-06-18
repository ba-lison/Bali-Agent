# -*- coding: utf-8 -*-
"""Session and checkpoint manager for maintaining agent conversation memory."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

class SessionManager:
    def __init__(self, root_dir: Path):
        self.sessions_dir = root_dir / ".agent" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
    def load_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Load session messages from checkpoint file."""
        checkpoint_path = self.sessions_dir / f"{session_id}.json"
        if checkpoint_path.is_file():
            try:
                with checkpoint_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                return []
        return []
        
    def save_session(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Save session messages atomically using a temp file."""
        checkpoint_path = self.sessions_dir / f"{session_id}.json"
        tmp_path = checkpoint_path.with_suffix(".json.tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, checkpoint_path)
        except Exception:
            if tmp_path.is_file():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
