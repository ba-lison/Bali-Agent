# -*- coding: utf-8 -*-
"""Scanner for identifying private API tokens and credentials in file writes or logs."""

import re
from typing import List, Optional

SECRET_PATTERNS = {
    "OpenAI / Anthropic API Key": re.compile(r"sk-[a-zA-Z0-9_-]{32,}"),
    "Google / Gemini API Key": re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
    "AWS Access Key ID": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub Token": re.compile(r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{82}"),
    "Stripe Token": re.compile(r"(sk|rk)_(live|test)_[a-zA-Z0-9]{24,}"),
    "Generic Private Key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

def scan_content_for_secrets(content: str) -> Optional[str]:
    """Scan content for sensitive tokens or keys and return the category if found."""
    if not content:
        return None
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(content):
            return name
    return None
