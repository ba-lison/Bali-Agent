# -*- coding: utf-8 -*-
"""Context module handling Sliding Window token budgets and Context Manifest generation."""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from bali_agent.security.secret_scanner import scan_content_for_secrets

class ContextPacker:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.runs_dir = root_dir / ".agent" / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count based on string length (average ~4 chars per token)."""
        return len(text or "") // 4
        
    def pack_context(self, agent_id: str, messages: List[Dict[str, Any]], max_tokens: int, run_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Prunes, redacts, and tracks files included in the context window.
        
        Returns the optimized messages and the manifest data.
        """
        redactions = 0
        included_files = []
        excluded_files = []
        
        # Redact messages in-place and extract source file usage if present
        cleaned_messages = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, list):
                # Handle structured blocks (e.g. Anthropic)
                new_blocks = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if scan_content_for_secrets(text):
                            redactions += 1
                            # Redact sensitive lines
                            from bali_agent.core.policy import ToolPolicy
                            text = ToolPolicy(self.root_dir).redact(agent_id, text)
                        new_blocks.append({"type": "text", "text": text})
                    else:
                        new_blocks.append(block)
                cleaned_messages.append({"role": m["role"], "content": new_blocks})
            else:
                content_str = str(content)
                if scan_content_for_secrets(content_str):
                    redactions += 1
                    from bali_agent.core.policy import ToolPolicy
                    content_str = ToolPolicy(self.root_dir).redact(agent_id, content_str)
                cleaned_messages.append({"role": m["role"], "content": content_str})
                
            # Parse messages for files referenced
            for word in str(content).split():
                if "/" in word or "." in word:
                    cleaned_word = word.strip(".,;:\"'()[]{}<>")
                    if os.path.exists(os.path.join(self.root_dir, cleaned_word)):
                        if ".env" in cleaned_word or "secrets" in cleaned_word:
                            if cleaned_word not in excluded_files:
                                excluded_files.append(cleaned_word)
                        else:
                            if cleaned_word not in included_files:
                                included_files.append(cleaned_word)

        # Sliding window history trimming if needed
        from bali_agent.core.llm_client import _trim_history
        final_messages = _trim_history(cleaned_messages)
        
        # Calculate tokens
        total_text = "".join(str(m.get("content", "")) for m in final_messages)
        estimated_tokens = self._estimate_tokens(total_text)
        
        manifest = {
            "run_id": run_id,
            "agent": agent_id,
            "included_files": included_files,
            "excluded_files": excluded_files,
            "token_budget": max_tokens,
            "estimated_tokens_used": estimated_tokens,
            "redactions": redactions
        }
        
        # Save context_manifest.json to runs directory
        run_folder = self.runs_dir / run_id
        run_folder.mkdir(parents=True, exist_ok=True)
        try:
            with (run_folder / "context_manifest.json").open("w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
        return final_messages, manifest


