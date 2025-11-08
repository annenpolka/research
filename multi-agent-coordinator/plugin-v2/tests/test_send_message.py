#!/usr/bin/env python3
"""Tests for send_message.py"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts"))

import send_message


class TestSendMessage(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.swarm_dir = Path(self.test_dir) / ".claude/swarm"
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

        # Patch SWARM_DIR
        send_message.SWARM_DIR = self.swarm_dir

        # Set test agent name
        os.environ["CLAUDE_AGENT_NAME"] = "TestAgent"

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir)
        if "CLAUDE_AGENT_NAME" in os.environ:
            del os.environ["CLAUDE_AGENT_NAME"]

    def test_send_message_creates_file(self):
        """Test that send_message creates messages.jsonl file."""
        send_message.send_message("RecipientAgent", "Test Subject", "Test Body")

        messages_file = self.swarm_dir / "messages.jsonl"
        self.assertTrue(messages_file.exists())

    def test_send_message_content(self):
        """Test that message has correct content."""
        send_message.send_message("RecipientAgent", "Test Subject", "Test Body", "high")

        messages_file = self.swarm_dir / "messages.jsonl"
        with open(messages_file, "r") as f:
            message = json.loads(f.read().strip())

        self.assertEqual(message["from"], "TestAgent")
        self.assertEqual(message["to"], "RecipientAgent")
        self.assertEqual(message["subject"], "Test Subject")
        self.assertEqual(message["body"], "Test Body")
        self.assertEqual(message["priority"], "high")
        self.assertFalse(message["read"])
        self.assertIn("id", message)
        self.assertIn("timestamp", message)

    def test_send_multiple_messages(self):
        """Test sending multiple messages appends correctly."""
        send_message.send_message("Agent1", "Subject1", "Body1")
        send_message.send_message("Agent2", "Subject2", "Body2")

        messages_file = self.swarm_dir / "messages.jsonl"
        with open(messages_file, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        msg1 = json.loads(lines[0])
        msg2 = json.loads(lines[1])

        self.assertEqual(msg1["to"], "Agent1")
        self.assertEqual(msg2["to"], "Agent2")

    def test_broadcast_message(self):
        """Test sending broadcast message to 'all'."""
        send_message.send_message("all", "", "Broadcast message")

        messages_file = self.swarm_dir / "messages.jsonl"
        with open(messages_file, "r") as f:
            message = json.loads(f.read().strip())

        self.assertEqual(message["to"], "all")

    def test_get_agent_id_from_env(self):
        """Test that agent ID is read from environment variable."""
        agent_id = send_message.get_agent_id()
        self.assertEqual(agent_id, "TestAgent")

    def test_get_agent_id_creates_session(self):
        """Test that agent ID is generated and saved if not in env."""
        if "CLAUDE_AGENT_NAME" in os.environ:
            del os.environ["CLAUDE_AGENT_NAME"]

        agent_id = send_message.get_agent_id()

        self.assertTrue(agent_id.startswith("agent-"))

        session_file = self.swarm_dir / ".session"
        self.assertTrue(session_file.exists())
        self.assertEqual(session_file.read_text().strip(), agent_id)


if __name__ == "__main__":
    unittest.main()
