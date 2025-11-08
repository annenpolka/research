#!/usr/bin/env python3
"""Tests for id_generator module."""

import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts")
)

import id_generator


class TestIDGenerator(unittest.TestCase):
    """Test hash-based ID generation."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir)

    def test_generate_task_id_format(self):
        """Test that task IDs have correct format."""
        task_id = id_generator.generate_task_id(self.test_path)
        self.assertTrue(task_id.startswith("task-"))
        hash_part = task_id.split("-")[1]
        self.assertGreaterEqual(len(hash_part), 4)
        self.assertLessEqual(len(hash_part), 6)

    def test_generate_message_id_format(self):
        """Test that message IDs have correct format."""
        msg_id = id_generator.generate_message_id(self.test_path)
        self.assertTrue(msg_id.startswith("msg-"))
        hash_part = msg_id.split("-")[1]
        self.assertGreaterEqual(len(hash_part), 4)

    def test_generate_agent_id_format(self):
        """Test that agent IDs have correct format."""
        agent_id = id_generator.generate_agent_id()
        self.assertTrue(agent_id.startswith("agent-"))
        hash_part = agent_id.split("-")[1]
        self.assertEqual(len(hash_part), 8)  # Agent IDs always 8 chars

    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = set()
        for _ in range(100):
            task_id = id_generator.generate_task_id(self.test_path)
            self.assertNotIn(task_id, ids, "Duplicate ID generated")
            ids.add(task_id)

    def test_hash_length_scaling_small(self):
        """Test hash length for small projects (0-500 records)."""
        # Create empty file (0 records)
        tasks_file = self.test_path / "tasks.jsonl"
        tasks_file.touch()

        task_id = id_generator.generate_task_id(self.test_path)
        hash_part = task_id.split("-")[1]
        self.assertEqual(len(hash_part), 4, "Small projects should use 4-char hash")

    def test_hash_length_scaling_medium(self):
        """Test hash length for medium projects (500+ records)."""
        # Create file with 600 records
        tasks_file = self.test_path / "tasks.jsonl"
        with open(tasks_file, "w") as f:
            for i in range(600):
                f.write(json.dumps({"id": f"task-{i:04d}"}) + "\n")

        task_id = id_generator.generate_task_id(self.test_path)
        hash_part = task_id.split("-")[1]
        self.assertEqual(len(hash_part), 5, "Medium projects should use 5-char hash")

    def test_hash_length_scaling_large(self):
        """Test hash length for large projects (1500+ records)."""
        # Create file with 2000 records
        tasks_file = self.test_path / "tasks.jsonl"
        with open(tasks_file, "w") as f:
            for i in range(2000):
                f.write(json.dumps({"id": f"task-{i:04d}"}) + "\n")

        task_id = id_generator.generate_task_id(self.test_path)
        hash_part = task_id.split("-")[1]
        self.assertEqual(len(hash_part), 6, "Large projects should use 6-char hash")

    def test_get_hash_length_thresholds(self):
        """Test hash length determination logic."""
        self.assertEqual(id_generator.get_hash_length(0), 4)
        self.assertEqual(id_generator.get_hash_length(100), 4)
        self.assertEqual(id_generator.get_hash_length(500), 5)
        self.assertEqual(id_generator.get_hash_length(1000), 5)
        self.assertEqual(id_generator.get_hash_length(1500), 6)
        self.assertEqual(id_generator.get_hash_length(10000), 6)

    def test_count_records_in_file(self):
        """Test record counting in JSONL files."""
        test_file = self.test_path / "test.jsonl"

        # Empty file
        test_file.touch()
        self.assertEqual(id_generator.count_records_in_file(test_file), 0)

        # File with records
        with open(test_file, "w") as f:
            f.write('{"id": "1"}\n')
            f.write('{"id": "2"}\n')
            f.write("\n")  # Empty line
            f.write('{"id": "3"}\n')

        self.assertEqual(id_generator.count_records_in_file(test_file), 3)

    def test_nonexistent_file(self):
        """Test handling of non-existent files."""
        nonexistent = self.test_path / "nonexistent.jsonl"
        count = id_generator.count_records_in_file(nonexistent)
        self.assertEqual(count, 0)

        # Should still generate valid ID
        task_id = id_generator.generate_task_id(self.test_path)
        self.assertTrue(task_id.startswith("task-"))


if __name__ == "__main__":
    unittest.main()
