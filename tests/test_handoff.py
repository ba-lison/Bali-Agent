# -*- coding: utf-8 -*-
"""Unit tests for the HandoffBus messaging module."""

import os
from pathlib import Path
import pytest

from templates.core.handoff_bus import _handoff_bus_send, _handoff_bus_receive

def test_handoff_bus_send_receive(temp_project_dir):
    bus_path = temp_project_dir / ".agent" / "output" / "handoff_bus.json"
    
    # Send message from orchestrator to reviewer
    send_msg = _handoff_bus_send(bus_path, "orchestrator", "reviewer", "Por favor revise o login.py")
    assert "reviewer" in send_msg
    assert bus_path.is_file()
    
    # Receive message as reviewer
    rec_msg = _handoff_bus_receive(bus_path, "reviewer")
    assert "Por favor revise o login.py" in rec_msg
    
    # Receive again (messages should be marked read, so none pending)
    rec_msg_empty = _handoff_bus_receive(bus_path, "reviewer")
    assert "Nenhuma mensagem pendente" in rec_msg_empty
