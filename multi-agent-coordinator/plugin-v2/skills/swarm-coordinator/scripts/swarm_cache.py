#!/usr/bin/env python3
"""
SQLite cache for fast queries on JSONL data.

Inspired by beads' dual persistence strategy:
- JSONL files are the source of truth (Git-managed)
- SQLite cache provides fast queries (gitignored)
- Auto-rebuilds when JSONL is newer than cache
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class SwarmCache:
    """SQLite cache for swarm state with auto-rebuild."""

    def __init__(self, swarm_dir: Path = Path(".claude/swarm")):
        self.swarm_dir = Path(swarm_dir)
        self.cache_dir = self.swarm_dir / ".cache"
        self.db_path = self.cache_dir / "state.db"

        self.tasks_file = self.swarm_dir / "tasks.jsonl"
        self.messages_file = self.swarm_dir / "messages.jsonl"
        self.locks_file = self.swarm_dir / "locks.jsonl"
        self.agents_file = self.swarm_dir / "agents.jsonl"

        self._ensure_cache()

    def _ensure_cache(self):
        """Ensure cache exists and is up-to-date."""
        if not self.db_path.exists():
            self._create_cache()
            self._rebuild_cache()
            return

        # Check if any JSONL file is newer than cache
        db_mtime = self.db_path.stat().st_mtime
        jsonl_files = [
            self.tasks_file,
            self.messages_file,
            self.locks_file,
            self.agents_file,
        ]

        needs_rebuild = any(
            f.exists() and f.stat().st_mtime > db_mtime for f in jsonl_files
        )

        if needs_rebuild:
            self._rebuild_cache()

    def _create_cache(self):
        """Create SQLite cache schema."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency

        # Tasks table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT,
                status TEXT,
                assigned_to TEXT,
                priority INTEGER,
                files TEXT,
                dependencies TEXT,
                created_at TEXT,
                claimed_at TEXT,
                completed_at TEXT,
                summary TEXT
            )
        """
        )

        # Messages table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                from_agent TEXT,
                to_agent TEXT,
                subject TEXT,
                body TEXT,
                priority TEXT,
                timestamp TEXT,
                read INTEGER
            )
        """
        )

        # Locks table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locks (
                file_path TEXT PRIMARY KEY,
                holder TEXT,
                reason TEXT,
                acquired_at TEXT,
                expires_at TEXT
            )
        """
        )

        # Agents table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                started_at TEXT,
                last_seen TEXT,
                status TEXT
            )
        """
        )

        # Indexes for common queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_agent)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_read ON messages(read)")

        conn.commit()
        conn.close()

    def _rebuild_cache(self):
        """Rebuild cache from JSONL files."""
        conn = sqlite3.connect(self.db_path)

        # Clear existing data
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM locks")
        conn.execute("DELETE FROM agents")

        # Load tasks
        if self.tasks_file.exists():
            task_state = {}
            with open(self.tasks_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)

                    # Task definition
                    if "id" in record and "task_id" not in record:
                        task_state[record["id"]] = {
                            "id": record["id"],
                            "description": record.get("description", ""),
                            "status": "pending",
                            "assigned_to": None,
                            "priority": record.get("priority", 0),
                            "files": json.dumps(record.get("files", [])),
                            "dependencies": json.dumps(record.get("dependencies", [])),
                            "created_at": record.get("created_at", ""),
                            "claimed_at": None,
                            "completed_at": None,
                            "summary": None,
                        }
                    # Task state update
                    elif "task_id" in record:
                        task_id = record["task_id"]
                        if task_id in task_state:
                            if record.get("status"):
                                task_state[task_id]["status"] = record["status"]
                            if record.get("agent_id"):
                                task_state[task_id]["assigned_to"] = record["agent_id"]
                            if record.get("claimed_at"):
                                task_state[task_id]["claimed_at"] = record["claimed_at"]
                            if record.get("completed_at"):
                                task_state[task_id]["completed_at"] = record[
                                    "completed_at"
                                ]
                            if record.get("summary"):
                                task_state[task_id]["summary"] = record["summary"]

            # Insert tasks
            for task in task_state.values():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tasks
                    (id, description, status, assigned_to, priority, files, dependencies,
                     created_at, claimed_at, completed_at, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        task["id"],
                        task["description"],
                        task["status"],
                        task["assigned_to"],
                        task["priority"],
                        task["files"],
                        task["dependencies"],
                        task["created_at"],
                        task["claimed_at"],
                        task["completed_at"],
                        task["summary"],
                    ),
                )

        # Load messages
        if self.messages_file.exists():
            with open(self.messages_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    msg = json.loads(line)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO messages
                        (id, from_agent, to_agent, subject, body, priority, timestamp, read)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            msg["id"],
                            msg.get("from", ""),
                            msg.get("to", ""),
                            msg.get("subject", ""),
                            msg.get("body", ""),
                            msg.get("priority", "normal"),
                            msg.get("timestamp", ""),
                            1 if msg.get("read", False) else 0,
                        ),
                    )

        # Load locks
        if self.locks_file.exists():
            with open(self.locks_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    lock = json.loads(line)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO locks
                        (file_path, holder, reason, acquired_at, expires_at)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            lock.get("file_path", ""),
                            lock.get("holder", ""),
                            lock.get("reason", ""),
                            lock.get("acquired_at", ""),
                            lock.get("expires_at", ""),
                        ),
                    )

        # Load agents
        if self.agents_file.exists():
            with open(self.agents_file, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    agent = json.loads(line)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO agents
                        (id, session_id, started_at, last_seen, status)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            agent.get("id", ""),
                            agent.get("session_id", ""),
                            agent.get("started_at", ""),
                            agent.get("last_seen", ""),
                            agent.get("status", "active"),
                        ),
                    )

        conn.commit()
        conn.close()

    # === Query methods ===

    def get_available_tasks(self) -> List[Dict]:
        """Get pending tasks with no dependencies, sorted by priority."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM tasks
            WHERE status = 'pending' AND (assigned_to IS NULL OR assigned_to = '')
            ORDER BY priority DESC, created_at ASC
        """
        )

        tasks = []
        for row in cursor:
            task = dict(row)
            task["files"] = json.loads(task["files"]) if task["files"] else []
            task["dependencies"] = (
                json.loads(task["dependencies"]) if task["dependencies"] else []
            )
            tasks.append(task)

        conn.close()
        return tasks

    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        conn.close()

        if not row:
            return None

        task = dict(row)
        task["files"] = json.loads(task["files"]) if task["files"] else []
        task["dependencies"] = (
            json.loads(task["dependencies"]) if task["dependencies"] else []
        )
        return task

    def get_messages_for_agent(
        self, agent_id: str, unread_only: bool = True, limit: int = None
    ) -> List[Dict]:
        """Get messages for an agent."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM messages WHERE (to_agent = ? OR to_agent = 'all')"
        params = [agent_id]

        if unread_only:
            query += " AND read = 0"

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor = conn.execute(query, params)
        messages = [dict(row) for row in cursor]

        conn.close()
        return messages

    def get_active_locks(self) -> List[Dict]:
        """Get all active locks."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        now = datetime.utcnow().isoformat()
        cursor = conn.execute(
            """
            SELECT * FROM locks
            WHERE expires_at > ?
            ORDER BY acquired_at DESC
        """,
            (now,),
        )

        locks = [dict(row) for row in cursor]
        conn.close()
        return locks

    def get_active_agents(self) -> List[Dict]:
        """Get all active agents."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            """
            SELECT * FROM agents
            WHERE status = 'active'
            ORDER BY last_seen DESC
        """
        )

        agents = [dict(row) for row in cursor]
        conn.close()
        return agents


if __name__ == "__main__":
    # Demo
    cache = SwarmCache()
    print("SQLite cache created/updated")
    print(f"Cache location: {cache.db_path}")
    print()
    print(f"Available tasks: {len(cache.get_available_tasks())}")
    print(f"Active agents: {len(cache.get_active_agents())}")
    print(f"Active locks: {len(cache.get_active_locks())}")
