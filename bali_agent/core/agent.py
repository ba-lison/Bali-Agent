# -*- coding: utf-8 -*-
"""Agent class representing structured subagent specifications and configurations."""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

class Agent:
    def __init__(self, agent_id: str, prompt: str, config: Dict[str, Any]):
        self.id = agent_id
        self.prompt = prompt
        self.role = config.get("role", "specialist")
        self.model = config.get("model", "default")
        self.allowed_tools = config.get("allowed_tools", [])
        self.denied_paths = config.get("denied_paths", [])
        self.max_iterations = int(config.get("max_iterations", 5))
        self.max_tokens = int(config.get("max_tokens", 12000))
        self.requires_review_by = config.get("requires_review_by", "reviewer")
        self.can_spawn_agents = config.get("can_spawn_agents", False)

    @classmethod
    def load_from_file(cls, path: Path) -> "Agent":
        """Parse frontmatter and return an Agent instance."""
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo de subagente nao encontrado: {path}")
            
        content = path.read_text(encoding="utf-8")
        
        # Parse markdown frontmatter
        frontmatter = {}
        prompt = content
        
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
                prompt = content[match.end():]
            except Exception:
                frontmatter = {}
                
        agent_id = frontmatter.get("id") or path.stem
        return cls(agent_id, prompt, frontmatter)
