# -*- coding: utf-8 -*-
"""Base adapter class defining the contract for native surface integrations."""

from pathlib import Path
from typing import Tuple, List

class BaseAdapter:
    def __init__(self, name: str, target_dir: Path):
        self.name = name
        self.target_dir = target_dir

    def verify(self) -> Tuple[bool, List[str]]:
        """Verify the completeness of this adapter's settings and native agents."""
        raise NotImplementedError()

    def setup(self) -> None:
        """Create necessary settings files and native templates for this adapter."""
        raise NotImplementedError()

    def get_capabilities(self) -> dict:
        """Return a dictionary of capabilities supported by this adapter."""
        raise NotImplementedError()
