#!/usr/bin/env python3
"""Tests for swarm_cache module."""

import unittest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add scripts directory to path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts")
)

import swarm_cache


class TestSwarmCache(unittest.TestCase):
    """Test SQLite cache functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.swarm_dir = Path(self.test_dir) / ".claude/swarm"
        self.swarm_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir)

    def create_sample_tasks(self):
        """Create sample tasks JSONL file."""
        tasks_file = self.swarm_dir / "tasks.jsonl"
        with open(tasks_file, "w") as f:
            # Task definition
            f.write(
                json.dumps(
                    {
                        "id": "task-001",
                        "description": "Test task 1",
                        "priority": 10,
                        "files": ["src/**"],
                        "dependencies": [],
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                + "\n"
            )
            # Another task
            f.write(
                json.dumps(
                    {
                        "id": "task-002",
                        "description": "Test task 2",
                        "priority": 5,
                        "files": [],
                        "dependencies": ["task-001"],
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                + "\n"
            )
            # Task claim
            f.write(
                json.dumps(
                    {
                        "task_id": "task-001",
                        "agent_id": "agent-123",
                        "claimed_at": datetime.utcnow().isoformat(),
                        "status": "in_progress",
                    }
                )
                + "\n"
            )

    def create_sample_messages(self):
        """Create sample messages JSONL file."""
        messages_file = self.swarm_dir / "messages.jsonl"
        with open(messages_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "id": "msg-001",
                        "from": "agent-123",
                        "to": "agent-456",
                        "subject": "Test",
                        "body": "Hello",
                        "priority": "normal",
                        "timestamp": datetime.utcnow().isoformat(),
                        "read": False,
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "id": "msg-002",
                        "from": "agent-123",
                        "to": "all",
                        "subject": "Broadcast",
                        "body": "Hi everyone",
                        "priority": "high",
                        "timestamp": datetime.utcnow().isoformat(),
                        "read": False,
                    }
                )
                + "\n"
            )

    def test_cache_creation(self):
        """Test that cache is created successfully."""
        cache = swarm_cache.SwarmCache(self.swarm_dir)
        self.assertTrue(cache.db_path.exists())
        self.assertTrue(cache.cache_dir.exists())

    def test_cache_rebuild_on_jsonl_change(self):
        """Test that cache rebuilds when JSONL is newer."""
        # Create initial cache
        cache = swarm_cache.SwarmCache(self.swarm_dir)
        initial_mtime = cache.db_path.stat().st_mtime

        # Wait a bit to ensure different mtime
        time.sleep(0.1)

        # Update JSONL file
        self.create_sample_tasks()

        # Create new cache instance - should rebuild
        cache2 = swarm_cache.SwarmCache(self.swarm_dir)
        new_mtime = cache2.db_path.stat().st_mtime

        self.assertGreater(new_mtime, initial_mtime, "Cache should be rebuilt")

    def test_get_available_tasks_empty(self):
        """Test getting available tasks from empty cache."""
        cache = swarm_cache.SwarmCache(self.swarm_dir)
        tasks = cache.get_available_tasks()
        self.assertEqual(len(tasks), 0)

    def test_get_available_tasks(self):
        """Test getting available tasks."""
        self.create_sample_tasks()
        cache = swarm_cache.SwarmCache(self.swarm_dir)

        tasks = cache.get_available_tasks()

        # Only task-002 should be available (task-001 is in_progress)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "task-002")
        self.assertEqual(tasks[0]["description"], "Test task 2")
        self.assertIsInstance(tasks[0]["files"], list)
        self.assertIsInstance(tasks[0]["dependencies"], list)

    def test_get_task_by_id(self):
        """Test getting specific task by ID."""
        self.create_sample_tasks()
        cache = swarm_cache.SwarmCache(self.swarm_dir)

        task = cache.get_task_by_id("task-001")
        self.assertIsNotNone(task)
        self.assertEqual(task["id"], "task-001")
        self.assertEqual(task["status"], "in_progress")
        self.assertEqual(task["assigned_to"], "agent-123")

    def test_get_task_by_id_not_found(self):
        """Test getting non-existent task."""
        cache = swarm_cache.SwarmCache(self.swarm_dir)
        task = cache.get_task_by_id("task-999")
        self.assertIsNone(task)

    def test_get_messages_for_agent(self):
        """Test getting messages for specific agent."""
        self.create_sample_messages()
        cache = swarm_cache.SwarmCache(self.swarm_dir)

        messages = cache.get_messages_for_agent("agent-456")

        # agent-456 should receive msg-001 directly and msg-002 (broadcast)
        self.assertEqual(len(messages), 2)

        msg_ids = [m["id"] for m in messages]
        self.assertIn("msg-001", msg_ids)
        self.assertIn("msg-002", msg_ids)

    def test_get_messages_unread_only(self):
        """Test filtering unread messages."""
        messages_file = self.swarm_dir / "messages.jsonl"
        with open(messages_file, "w") as f:
            # Unread message
            f.write(
                json.dumps(
                    {
                        "id": "msg-001",
                        "from": "agent-123",
                        "to": "agent-456",
                        "subject": "Unread",
                        "body": "Test",
                        "priority": "normal",
                        "timestamp": datetime.utcnow().isoformat(),
                        "read": False,
                    }
                )
                + "\n"
            )
            # Read message
            f.write(
                json.dumps(
                    {
                        "id": "msg-002",
                        "from": "agent-123",
                        "to": "agent-456",
                        "subject": "Read",
                        "body": "Test",
                        "priority": "normal",
                        "timestamp": datetime.utcnow().isoformat(),
                        "read": True,
                    }
                )
                + "\n"
            )

        cache = swarm_cache.SwarmCache(self.swarm_dir)

        # Unread only
        unread = cache.get_messages_for_agent("agent-456", unread_only=True)
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread[0]["id"], "msg-001")

        # All messages
        all_msgs = cache.get_messages_for_agent("agent-456", unread_only=False)
        self.assertEqual(len(all_msgs), 2)

    def test_get_messages_with_limit(self):
        """Test limiting number of messages returned."""
        messages_file = self.swarm_dir / "messages.jsonl"
        with open(messages_file, "w") as f:
            for i in range(10):
                f.write(
                    json.dumps(
                        {
                            "id": f"msg-{i:03d}",
                            "from": "agent-123",
                            "to": "agent-456",
                            "subject": f"Message {i}",
                            "body": "Test",
                            "priority": "normal",
                            "timestamp": datetime.utcnow().isoformat(),
                            "read": False,
                        }
                    )
                    + "\n"
                )

        cache = swarm_cache.SwarmCache(self.swarm_dir)

        messages = cache.get_messages_for_agent("agent-456", limit=5)
        self.assertEqual(len(messages), 5)

    def test_get_active_locks(self):
        """Test getting active locks."""
        locks_file = self.swarm_dir / "locks.jsonl"
        now = datetime.utcnow()
        future = now + timedelta(minutes=5)
        past = now - timedelta(minutes=5)

        with open(locks_file, "w") as f:
            # Active lock
            f.write(
                json.dumps(
                    {
                        "file_path": "src/main.py",
                        "holder": "agent-123",
                        "reason": "editing",
                        "acquired_at": now.isoformat(),
                        "expires_at": future.isoformat(),
                    }
                )
                + "\n"
            )
            # Expired lock
            f.write(
                json.dumps(
                    {
                        "file_path": "src/old.py",
                        "holder": "agent-456",
                        "reason": "editing",
                        "acquired_at": past.isoformat(),
                        "expires_at": past.isoformat(),
                    }
                )
                + "\n"
            )

        cache = swarm_cache.SwarmCache(self.swarm_dir)

        locks = cache.get_active_locks()

        # Only the active lock should be returned
        self.assertEqual(len(locks), 1)
        self.assertEqual(locks[0]["file_path"], "src/main.py")

    def test_get_active_agents(self):
        """Test getting active agents."""
        agents_file = self.swarm_dir / "agents.jsonl"
        with open(agents_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "id": "agent-123",
                        "session_id": "sess-001",
                        "started_at": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "status": "active",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "id": "agent-456",
                        "session_id": "sess-002",
                        "started_at": datetime.utcnow().isoformat(),
                        "last_seen": datetime.utcnow().isoformat(),
                        "status": "inactive",
                    }
                )
                + "\n"
            )

        cache = swarm_cache.SwarmCache(self.swarm_dir)

        agents = cache.get_active_agents()

        # Only active agent should be returned
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0]["id"], "agent-123")

    def test_task_priority_sorting(self):
        """Test that tasks are sorted by priority."""
        tasks_file = self.swarm_dir / "tasks.jsonl"
        with open(tasks_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "id": "task-001",
                        "description": "Low priority",
                        "priority": 2,
                        "files": [],
                        "dependencies": [],
                        "created_at": "2025-01-01T10:00:00",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "id": "task-002",
                        "description": "High priority",
                        "priority": 10,
                        "files": [],
                        "dependencies": [],
                        "created_at": "2025-01-01T11:00:00",
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "id": "task-003",
                        "description": "Medium priority",
                        "priority": 5,
                        "files": [],
                        "dependencies": [],
                        "created_at": "2025-01-01T09:00:00",
                    }
                )
                + "\n"
            )

        cache = swarm_cache.SwarmCache(self.swarm_dir)
        tasks = cache.get_available_tasks()

        # Should be sorted by priority DESC, then created_at ASC
        self.assertEqual(tasks[0]["id"], "task-002")  # Priority 10
        self.assertEqual(tasks[1]["id"], "task-003")  # Priority 5
        self.assertEqual(tasks[2]["id"], "task-001")  # Priority 2


if __name__ == "__main__":
    unittest.main()
