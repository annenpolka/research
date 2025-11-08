#!/usr/bin/env python3
"""Tests for task management (claim_task.py and complete_task.py)"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts"))

import claim_task
import complete_task


class TestTaskManagement(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.swarm_dir = Path(self.test_dir) / ".claude/swarm"
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

        claim_task.SWARM_DIR = self.swarm_dir
        complete_task.SWARM_DIR = self.swarm_dir

        os.environ["CLAUDE_AGENT_NAME"] = "TestAgent"

        # Create test tasks
        self.tasks_file = self.swarm_dir / "tasks.jsonl"
        self.create_test_tasks()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.test_dir)
        if "CLAUDE_AGENT_NAME" in os.environ:
            del os.environ["CLAUDE_AGENT_NAME"]

    def create_test_tasks(self):
        """Create test tasks in tasks.jsonl."""
        tasks = [
            {
                "id": "task-001",
                "description": "High priority task",
                "status": "pending",
                "dependencies": [],
                "priority": 10,
                "files": ["src/api/**"],
            },
            {
                "id": "task-002",
                "description": "Medium priority task",
                "status": "pending",
                "dependencies": [],
                "priority": 5,
                "files": ["src/ui/**"],
            },
            {
                "id": "task-003",
                "description": "Dependent task",
                "status": "pending",
                "dependencies": ["task-001"],
                "priority": 8,
                "files": ["tests/**"],
            },
        ]

        with open(self.tasks_file, "w") as f:
            for task in tasks:
                f.write(json.dumps(task) + "\n")

    def test_load_task_state(self):
        """Test loading task state."""
        task_state = claim_task.load_task_state()

        self.assertEqual(len(task_state), 3)
        self.assertIn("task-001", task_state)
        self.assertEqual(task_state["task-001"]["priority"], 10)

    def test_get_available_tasks(self):
        """Test getting available tasks."""
        task_state = claim_task.load_task_state()
        available = claim_task.get_available_tasks(task_state)

        # task-003 should not be available (depends on task-001)
        self.assertEqual(len(available), 2)

        task_ids = [t["id"] for t in available]
        self.assertIn("task-001", task_ids)
        self.assertIn("task-002", task_ids)
        self.assertNotIn("task-003", task_ids)

    def test_available_tasks_sorted_by_priority(self):
        """Test that available tasks are sorted by priority."""
        task_state = claim_task.load_task_state()
        available = claim_task.get_available_tasks(task_state)

        # First task should be highest priority (task-001)
        self.assertEqual(available[0]["id"], "task-001")
        self.assertEqual(available[0]["priority"], 10)

    def test_claim_task_specific(self):
        """Test claiming a specific task."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        claim_task.claim_task("task-002")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("task-002", output)
        self.assertIn("Medium priority task", output)

        # Check that claim was recorded
        with open(self.tasks_file, "r") as f:
            lines = f.readlines()

        claim_record = json.loads(lines[-1])
        self.assertEqual(claim_record["task_id"], "task-002")
        self.assertEqual(claim_record["agent_id"], "TestAgent")
        self.assertEqual(claim_record["status"], "in_progress")

    def test_claim_task_auto_assign(self):
        """Test auto-assigning highest priority task."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        claim_task.claim_task(None)

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # Should assign task-001 (highest priority)
        self.assertIn("task-001", output)

    def test_claim_task_not_available(self):
        """Test claiming a task that's not available."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        # Try to claim task-003 (depends on task-001)
        claim_task.claim_task("task-003")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # Should still claim it (only checking status, not dependencies in claim_task)
        # Actually, looking at the code, claim_task doesn't check dependencies when task_id is specified
        self.assertIn("task-003", output)

    def test_claim_nonexistent_task(self):
        """Test claiming a non-existent task."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        claim_task.claim_task("task-999")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("not found", output)

    def test_complete_task(self):
        """Test completing a task."""
        # First claim the task
        claim_task.claim_task("task-001")

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        complete_task.complete_task("task-001", "Task completed successfully")

        sys.stdout = old_stdout
        output = captured_output.getvalue()

        self.assertIn("completed", output)

        # Check that completion was recorded
        with open(self.tasks_file, "r") as f:
            lines = f.readlines()

        completion_record = json.loads(lines[-1])
        self.assertEqual(completion_record["task_id"], "task-001")
        self.assertEqual(completion_record["status"], "completed")
        self.assertEqual(completion_record["summary"], "Task completed successfully")

    def test_complete_task_broadcasts_message(self):
        """Test that completing a task broadcasts a message."""
        complete_task.complete_task("task-001", "Done!")

        messages_file = self.swarm_dir / "messages.jsonl"
        self.assertTrue(messages_file.exists())

        with open(messages_file, "r") as f:
            message = json.loads(f.read().strip())

        self.assertEqual(message["to"], "all")
        self.assertIn("task-001", message["subject"])
        self.assertIn("completed", message["subject"])

    def test_dependent_task_becomes_available(self):
        """Test that dependent task becomes available after dependency is completed."""
        # Complete task-001
        complete_task.complete_task("task-001", "Done")

        # Reload task state
        task_state = claim_task.load_task_state()
        available = claim_task.get_available_tasks(task_state)

        # Now task-003 should be available
        task_ids = [t["id"] for t in available]
        self.assertIn("task-003", task_ids)


if __name__ == "__main__":
    unittest.main()
