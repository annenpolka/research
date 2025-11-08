#!/usr/bin/env python3
"""Tests for get_messages.py"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts"))

import get_messages


class TestGetMessages(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.swarm_dir = Path(self.test_dir) / ".claude/swarm"
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

        get_messages.SWARM_DIR = self.swarm_dir
        os.environ["CLAUDE_AGENT_NAME"] = "TestAgent"

        # Create test messages
        self.messages_file = self.swarm_dir / "messages.jsonl"
        self.create_test_messages()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir)
        if "CLAUDE_AGENT_NAME" in os.environ:
            del os.environ["CLAUDE_AGENT_NAME"]

    def create_test_messages(self):
        """Create test messages in messages.jsonl."""
        messages = [
            {
                "id": "msg-1",
                "from": "Agent1",
                "to": "TestAgent",
                "subject": "Message 1",
                "body": "Body 1",
                "priority": "normal",
                "timestamp": datetime.utcnow().isoformat(),
                "read": False,
            },
            {
                "id": "msg-2",
                "from": "Agent2",
                "to": "TestAgent",
                "subject": "Message 2",
                "body": "Body 2",
                "priority": "high",
                "timestamp": datetime.utcnow().isoformat(),
                "read": True,
            },
            {
                "id": "msg-3",
                "from": "Agent3",
                "to": "OtherAgent",
                "subject": "Not for us",
                "body": "Body 3",
                "priority": "normal",
                "timestamp": datetime.utcnow().isoformat(),
                "read": False,
            },
            {
                "id": "msg-4",
                "from": "Agent4",
                "to": "all",
                "subject": "Broadcast",
                "body": "Body 4",
                "priority": "normal",
                "timestamp": datetime.utcnow().isoformat(),
                "read": False,
            },
        ]

        with open(self.messages_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

    def test_get_messages_unread_only(self):
        """Test getting only unread messages."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_messages.get_messages(unread_only=True, limit=20)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # Should show 2 messages (msg-1 and msg-4)
        self.assertIn("Message 1", output)
        self.assertIn("Broadcast", output)
        self.assertNotIn("Message 2", output)  # Read message
        self.assertNotIn("Not for us", output)  # Different recipient

    def test_get_messages_all(self):
        """Test getting all messages including read."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_messages.get_messages(unread_only=False, limit=20)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # Should show 3 messages (msg-1, msg-2, msg-4)
        self.assertIn("Message 1", output)
        self.assertIn("Message 2", output)
        self.assertIn("Broadcast", output)
        self.assertNotIn("Not for us", output)

    def test_get_messages_limit(self):
        """Test message limit."""
        # Create many messages
        with open(self.messages_file, "a") as f:
            for i in range(5, 30):
                msg = {
                    "id": f"msg-{i}",
                    "from": f"Agent{i}",
                    "to": "TestAgent",
                    "subject": f"Message {i}",
                    "body": f"Body {i}",
                    "priority": "normal",
                    "timestamp": datetime.utcnow().isoformat(),
                    "read": False,
                }
                f.write(json.dumps(msg) + "\n")

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_messages.get_messages(unread_only=True, limit=5)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # Count how many messages are shown (limited to 5)
        message_count = output.count("**From**:")
        self.assertLessEqual(message_count, 5)

    def test_get_messages_empty(self):
        """Test with no messages file."""
        os.remove(self.messages_file)

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_messages.get_messages(unread_only=True, limit=20)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("No messages", output)

    def test_get_messages_no_matching(self):
        """Test when no messages match the filter."""
        # Mark all messages as read
        messages = []
        with open(self.messages_file, "r") as f:
            for line in f:
                msg = json.loads(line)
                msg["read"] = True
                messages.append(msg)

        with open(self.messages_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_messages.get_messages(unread_only=True, limit=20)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("No messages", output)


if __name__ == "__main__":
    unittest.main()
