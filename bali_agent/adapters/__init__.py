# -*- coding: utf-8 -*-
"""Surface adapters registration."""

from bali_agent.adapters.claude import ClaudeAdapter
from bali_agent.adapters.codex import CodexAdapter
from bali_agent.adapters.opencode import OpenCodeAdapter
from bali_agent.adapters.cursor import CursorAdapter
from bali_agent.adapters.antigravity import AntigravityAdapter

ADAPTERS = {
    "claude-code": ClaudeAdapter,
    "codex": CodexAdapter,
    "opencode": OpenCodeAdapter,
    "cursor": CursorAdapter,
    "antigravity": AntigravityAdapter,
}
