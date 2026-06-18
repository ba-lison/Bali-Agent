# -*- coding: utf-8 -*-
"""Surface adapters registration."""

from bali_agent.adapters.claude import ClaudeAdapter
from bali_agent.adapters.codex import CodexAdapter
from bali_agent.adapters.opencode import OpenCodeAdapter
from bali_agent.adapters.cursor import CursorAdapter
from bali_agent.adapters.gemini import GeminiAdapter
from bali_agent.adapters.antigravity import AntigravityAdapter
from bali_agent.adapters.ollama import OllamaAdapter

ADAPTERS = {
    "claude-code": ClaudeAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
    "cursor": CursorAdapter,
    "gemini": GeminiAdapter,
    "antigravity": AntigravityAdapter,
    "ollama": OllamaAdapter,
    "bali-runtime": OllamaAdapter
}
