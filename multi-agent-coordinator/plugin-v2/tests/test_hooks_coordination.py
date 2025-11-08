#!/usr/bin/env python3
"""Tests for hook event dispatch."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add plugin root to path to import hooks module
sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks import coordination


class TestHookDispatch(unittest.TestCase):
    """Verify that hook events follow the Claude Code schema."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.prev_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Ensure fresh swarm directory inside the temp workspace
        self.swarm_dir = Path(".claude/swarm")
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

        # Force coordinator to use the temp swarm directory
        coordination.SWARM_DIR = self.swarm_dir

        os.environ["CLAUDE_AGENT_NAME"] = "HookTester"

    def tearDown(self):
        os.chdir(self.prev_cwd)
        shutil.rmtree(self.test_dir)
        os.environ.pop("CLAUDE_AGENT_NAME", None)

    def test_session_start_event_records_agent(self):
        """SessionStart events should register the agent and return context."""
        event = {
            "hook_event_name": "SessionStart",
            "hook_context": {
                "session_id": "session-123"
            }
        }

        result = coordination.process_hook_event(event)

        self.assertTrue(result["success"])
        self.assertIn("context_message", result)

        agents_file = self.swarm_dir / "agents.jsonl"
        self.assertTrue(agents_file.exists())

        last_line = agents_file.read_text().strip().splitlines()[-1]
        record = json.loads(last_line)
        self.assertEqual(record["session_id"], "session-123")
        self.assertEqual(record["id"], "HookTester")


if __name__ == "__main__":
    unittest.main()
