#!/usr/bin/env python3
"""Tests for get_state.py"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts"))

import get_state


class TestGetState(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.swarm_dir = Path(self.test_dir) / ".claude/swarm"
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

        get_state.SWARM_DIR = self.swarm_dir

        # Create test data
        self.create_test_data()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir)

    def create_test_data(self):
        """Create test data files."""
        # Create agents
        agents_file = self.swarm_dir / "agents.jsonl"
        agents = [
            {
                "id": "agent-1",
                "session_id": "session-1",
                "started_at": datetime.utcnow().isoformat(),
                "pid": 1234,
            },
            {
                "id": "agent-2",
                "session_id": "session-2",
                "started_at": datetime.utcnow().isoformat(),
                "pid": 5678,
            },
            {
                "id": "agent-3",
                "session_id": "session-3",
                "started_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "pid": 9012,
            },
            {
                "id": "agent-3",
                "terminated_at": datetime.utcnow().isoformat(),
            },
        ]

        with open(agents_file, "w") as f:
            for agent in agents:
                f.write(json.dumps(agent) + "\n")

        # Create tasks
        tasks_file = self.swarm_dir / "tasks.jsonl"
        tasks = [
            {
                "id": "task-001",
                "description": "Task 1",
                "status": "pending",
                "dependencies": [],
                "priority": 10,
            },
            {
                "id": "task-002",
                "description": "Task 2",
                "status": "pending",
                "dependencies": [],
                "priority": 5,
            },
            {
                "task_id": "task-002",
                "agent_id": "agent-1",
                "claimed_at": datetime.utcnow().isoformat(),
                "status": "in_progress",
            },
            {
                "task_id": "task-001",
                "agent_id": "agent-2",
                "claimed_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "status": "completed",
            },
        ]

        with open(tasks_file, "w") as f:
            for task in tasks:
                f.write(json.dumps(task) + "\n")

        # Create locks
        locks_file = self.swarm_dir / "locks.jsonl"
        locks = [
            {
                "file_path": "src/api.ts",
                "holder": "agent-1",
                "reason": "editing via Edit",
                "acquired_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            },
            {
                "file_path": "src/utils.ts",
                "holder": "agent-2",
                "reason": "editing via Write",
                "acquired_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
                "expires_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),  # Expired
            },
            {
                "file_path": "src/config.ts",
                "holder": "agent-2",
                "reason": "editing",
                "acquired_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=3)).isoformat(),
            },
            {
                "file_path": "src/config.ts",
                "holder": "agent-2",
                "released_at": datetime.utcnow().isoformat(),
                "status": "released",
            },
        ]

        with open(locks_file, "w") as f:
            for lock in locks:
                f.write(json.dumps(lock) + "\n")

    def test_get_agents(self):
        """Test getting active agents."""
        agents = get_state.get_agents()

        # agent-3 was terminated, so only 2 should be active
        self.assertEqual(len(agents), 2)
        self.assertIn("agent-1", agents)
        self.assertIn("agent-2", agents)
        self.assertNotIn("agent-3", agents)

    def test_get_tasks(self):
        """Test getting task state."""
        tasks = get_state.get_tasks()

        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks["task-001"]["status"], "completed")
        self.assertEqual(tasks["task-002"]["status"], "in_progress")
        self.assertEqual(tasks["task-002"]["agent_id"], "agent-1")

    def test_get_locks(self):
        """Test getting active locks."""
        locks = get_state.get_locks()

        # Only src/api.ts should be locked (src/utils.ts expired, src/config.ts released)
        self.assertEqual(len(locks), 1)
        self.assertIn("src/api.ts", locks)
        self.assertEqual(locks["src/api.ts"]["holder"], "agent-1")

    def test_print_agents(self):
        """Test printing agent information."""
        agents = get_state.get_agents()

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.print_agents(agents)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("Active Agents (2)", output)
        self.assertIn("agent-1", output)
        self.assertIn("agent-2", output)

    def test_print_tasks(self):
        """Test printing task information."""
        tasks = get_state.get_tasks()

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.print_tasks(tasks)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("Pending: 0", output)
        self.assertIn("In Progress: 1", output)
        self.assertIn("Completed: 1", output)
        self.assertIn("task-002", output)
        self.assertIn("agent-1", output)

    def test_print_locks(self):
        """Test printing lock information."""
        locks = get_state.get_locks()

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.print_locks(locks)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("Active File Locks (1)", output)
        self.assertIn("src/api.ts", output)
        self.assertIn("agent-1", output)
        self.assertIn("editing via Edit", output)

    def test_get_state_all(self):
        """Test getting all state."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.get_state("all")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("Active Agents", output)
        self.assertIn("Tasks", output)
        self.assertIn("Active File Locks", output)

    def test_get_state_agents_only(self):
        """Test getting only agents."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.get_state("agents")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("Active Agents", output)
        self.assertNotIn("Tasks", output)
        self.assertNotIn("Active File Locks", output)

    def test_get_state_tasks_only(self):
        """Test getting only tasks."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.get_state("tasks")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertNotIn("Active Agents", output)
        self.assertIn("Tasks", output)
        self.assertNotIn("Active File Locks", output)

    def test_get_state_locks_only(self):
        """Test getting only locks."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        get_state.get_state("locks")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertNotIn("Active Agents", output)
        self.assertNotIn("📋 Tasks", output)  # Using emoji to distinguish
        self.assertIn("Active File Locks", output)


if __name__ == "__main__":
    unittest.main()
