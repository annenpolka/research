#!/usr/bin/env python3
"""
Swarm Coordination Hook for Claude Code

This hook manages file locks and agent registration in a multi-agent environment.
Install: Copy to .claude/hooks/ and configure in hooks.json
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib

# Configuration
SWARM_DIR = Path(".claude/swarm")
LOCK_TIMEOUT_MINUTES = 5
AGENT_NAME_ENV = "CLAUDE_AGENT_NAME"


class SwarmCoordinator:
    """Manages multi-agent coordination"""

    def __init__(self):
        self.swarm_dir = SWARM_DIR
        self.swarm_dir.mkdir(parents=True, exist_ok=True)
        self.agent_id = self._get_agent_id()

    def _get_agent_id(self) -> str:
        """Get or generate agent ID"""
        # Check environment variable
        if AGENT_NAME_ENV in os.environ:
            return os.environ[AGENT_NAME_ENV]

        # Check session file
        session_file = self.swarm_dir / ".session"
        if session_file.exists():
            return session_file.read_text().strip()

        # Generate new ID
        agent_id = f"agent-{hashlib.sha256(os.urandom(16)).hexdigest()[:8]}"
        session_file.write_text(agent_id)
        return agent_id

    def handle_session_start(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session start event"""
        session_id = context.get("session_id", "unknown")

        # Register agent
        agent_record = {
            "id": self.agent_id,
            "session_id": session_id,
            "started_at": datetime.utcnow().isoformat(),
            "pid": os.getpid(),
        }

        self._append_jsonl("agents.jsonl", agent_record)

        # Get available tasks
        tasks = self._get_available_tasks()

        # Build context message
        if tasks:
            task_list = "\n".join(
                f"  - `{t['id']}`: {t['description']}" for t in tasks[:5]
            )
            message = f"""
## 🤝 Swarm Coordination Active

You are agent **{self.agent_id}** in a multi-agent swarm.

**Available tasks** ({len(tasks)} total):
{task_list}

**Tools available**:
- `swarm_claim_task` - Claim a task to work on
- `swarm_send_message` - Message other agents
- `swarm_get_state` - Check swarm status

**Important**: When editing files, locks are automatically managed to prevent conflicts.
"""
        else:
            message = f"""
## 🤝 Swarm Coordination Active

You are agent **{self.agent_id}**. No tasks currently available.
Use `swarm_get_state` to check swarm status.
"""

        return {
            "success": True,
            "context_message": message,
        }

    def handle_pre_tool_use(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pre-tool-use event (file locking)"""
        # Only intercept file editing tools
        if tool_name not in ["Edit", "Write", "MultiEdit"]:
            return {"block": False}

        file_path = params.get("file_path")
        if not file_path:
            return {"block": False}

        # Check if file is locked
        lock_info = self._check_lock(file_path)

        if lock_info and lock_info["holder"] != self.agent_id:
            # File is locked by another agent
            time_remaining = (
                datetime.fromisoformat(lock_info["expires_at"]) - datetime.utcnow()
            )
            minutes = max(1, time_remaining.seconds // 60)

            return {
                "block": True,
                "message": f"""
⚠️  File **{file_path}** is locked by agent **{lock_info['holder']}**

**Reason**: {lock_info.get('reason', 'editing')}
**Time remaining**: ~{minutes} minutes

**Suggestions**:
1. Work on a different file
2. Message {lock_info['holder']} to coordinate: `swarm_send_message`
3. Wait for lock to expire

**Current swarm state**: Use `swarm_get_state` to see all locks
""",
            }

        # Acquire lock
        self._acquire_lock(file_path, f"editing via {tool_name}")

        return {
            "block": False,
            "message": f"✓ Acquired lock on {file_path}",
        }

    def handle_post_tool_use(
        self, tool_name: str, params: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle post-tool-use event (lock release)"""
        if tool_name in ["Edit", "Write", "MultiEdit"]:
            file_path = params.get("file_path")
            if file_path and result.get("success"):
                self._release_lock(file_path)

        return {"success": True}

    def handle_session_end(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session end event"""
        # Release all locks held by this agent
        self._release_all_locks()

        # Mark agent as terminated
        termination_record = {
            "id": self.agent_id,
            "terminated_at": datetime.utcnow().isoformat(),
            "session_duration": context.get("duration_seconds", 0),
        }
        self._append_jsonl("agents.jsonl", termination_record)

        return {"success": True}

    # Helper methods

    def _check_lock(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Check if file is currently locked"""
        locks_file = self.swarm_dir / "locks.jsonl"
        if not locks_file.exists():
            return None

        # Scan backwards for most recent lock record
        lines = locks_file.read_text().strip().split("\n")
        for line in reversed(lines):
            if not line:
                continue

            record = json.loads(line)
            if record["file_path"] != file_path:
                continue

            # Check if lock is released
            if record.get("status") == "released":
                return None

            # Check if lock is expired
            expires_at = datetime.fromisoformat(record["expires_at"])
            if expires_at > datetime.utcnow():
                return record
            else:
                # Expired
                return None

        return None

    def _acquire_lock(self, file_path: str, reason: str):
        """Acquire lock on file"""
        lock_record = {
            "file_path": file_path,
            "holder": self.agent_id,
            "reason": reason,
            "acquired_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + timedelta(minutes=LOCK_TIMEOUT_MINUTES)
            ).isoformat(),
        }
        self._append_jsonl("locks.jsonl", lock_record)

    def _release_lock(self, file_path: str):
        """Release lock on file"""
        release_record = {
            "file_path": file_path,
            "holder": self.agent_id,
            "released_at": datetime.utcnow().isoformat(),
            "status": "released",
        }
        self._append_jsonl("locks.jsonl", release_record)

    def _release_all_locks(self):
        """Release all locks held by this agent"""
        locks_file = self.swarm_dir / "locks.jsonl"
        if not locks_file.exists():
            return

        # Find all active locks for this agent
        active_locks = set()
        lines = locks_file.read_text().strip().split("\n")

        for line in lines:
            if not line:
                continue
            record = json.loads(line)

            if record.get("holder") == self.agent_id:
                if record.get("status") == "released":
                    active_locks.discard(record["file_path"])
                else:
                    active_locks.add(record["file_path"])

        # Release each active lock
        for file_path in active_locks:
            self._release_lock(file_path)

    def _get_available_tasks(self) -> list:
        """Get list of available tasks"""
        tasks_file = self.swarm_dir / "tasks.jsonl"
        if not tasks_file.exists():
            return []

        # Parse tasks (simplified - should use proper task tracking)
        tasks = []
        for line in tasks_file.read_text().strip().split("\n"):
            if not line:
                continue
            task = json.loads(line)
            if task.get("status") == "pending" and not task.get("assigned_to"):
                tasks.append(task)

        return sorted(tasks, key=lambda t: t.get("priority", 0), reverse=True)

    def _append_jsonl(self, filename: str, record: Dict[str, Any]):
        """Append record to JSONL file"""
        filepath = self.swarm_dir / filename
        with open(filepath, "a") as f:
            f.write(json.dumps(record) + "\n")


def main():
    """Main entry point for hook execution"""
    # Parse hook event from stdin
    try:
        event_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        sys.exit(1)

    event_type = event_data.get("event")
    context = event_data.get("context", {})

    coordinator = SwarmCoordinator()

    # Route to appropriate handler
    result = {}
    try:
        if event_type == "session-start":
            result = coordinator.handle_session_start(context)
        elif event_type == "pre-tool-use":
            result = coordinator.handle_pre_tool_use(
                context.get("tool_name", ""),
                context.get("params", {}),
            )
        elif event_type == "post-tool-use":
            result = coordinator.handle_post_tool_use(
                context.get("tool_name", ""),
                context.get("params", {}),
                context.get("result", {}),
            )
        elif event_type == "session-end":
            result = coordinator.handle_session_end(context)
        else:
            result = {"error": f"Unknown event type: {event_type}"}
    except Exception as e:
        result = {"error": str(e)}

    # Output result as JSON
    print(json.dumps(result))


if __name__ == "__main__":
    main()
