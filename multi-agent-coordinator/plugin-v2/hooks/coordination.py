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

EVENT_ALIASES = {
    "sessionstart": "session-start",
    "sessionend": "session-end",
    "pretooluse": "pre-tool-use",
    "posttooluse": "post-tool-use",
}


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
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pre-tool-use event (file locking)"""
        if tool_name not in ["Edit", "Write", "MultiEdit"]:
            return {"block": False}

        file_path = self._extract_file_path(tool_input)
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
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_response: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle post-tool-use event (lock release)"""
        if tool_name in ["Edit", "Write", "MultiEdit"]:
            file_path = self._extract_file_path(tool_input)
            if file_path and self._response_succeeded(tool_response):
                self._release_lock(file_path)

        return {"success": True}

    def handle_session_end(self, hook_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session end event"""
        # Release all locks held by this agent
        self._release_all_locks()

        # Mark agent as terminated
        termination_record = {
            "id": self.agent_id,
            "terminated_at": datetime.utcnow().isoformat(),
            "session_duration": hook_context.get("duration_seconds", 0),
        }
        self._append_jsonl("agents.jsonl", termination_record)

        return {"success": True}

    # Helper methods

    def _extract_file_path(self, tool_input: Any) -> Optional[str]:
        """Extract a single file path from tool input payloads."""
        if isinstance(tool_input, str):
            return tool_input

        if not isinstance(tool_input, dict):
            return None

        if tool_input.get("file_path"):
            return tool_input["file_path"]

        if tool_input.get("path"):
            return tool_input["path"]

        paths = tool_input.get("paths")
        if isinstance(paths, list) and paths:
            return paths[0]

        return None

    def _response_succeeded(self, tool_response: Any) -> bool:
        """Normalize success detection from Claude tool responses."""
        if not isinstance(tool_response, dict):
            return True

        if "success" in tool_response:
            return bool(tool_response["success"])

        status = tool_response.get("status")
        if status is None:
            return True

        return str(status).lower() in {"ok", "success", "done"}

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

def _normalize_event_name(event_name: Optional[str]) -> str:
    """Normalize hook event names to kebab-case for routing."""
    if not event_name:
        return ""

    token = event_name.replace("-", "").replace("_", "").lower()
    normalized = EVENT_ALIASES.get(token)
    if normalized:
        return normalized

    if token:
        return event_name.lower()

    return ""


def process_hook_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a Claude Code hook payload and return the hook response."""
    coordinator = SwarmCoordinator()
    event_type = _normalize_event_name(
        event_data.get("hook_event_name") or event_data.get("event")
    )
    hook_context = event_data.get("hook_context") or event_data.get("context") or {}

    try:
        if event_type == "session-start":
            return coordinator.handle_session_start(hook_context)
        if event_type == "pre-tool-use":
            tool_name = event_data.get("tool_name") or hook_context.get("tool_name", "")
            tool_input = event_data.get("tool_input") or hook_context.get("params") or {}
            return coordinator.handle_pre_tool_use(tool_name, tool_input)
        if event_type == "post-tool-use":
            tool_name = event_data.get("tool_name") or hook_context.get("tool_name", "")
            tool_input = event_data.get("tool_input") or hook_context.get("params") or {}
            tool_response = (
                event_data.get("tool_response")
                or hook_context.get("result")
                or {}
            )
            return coordinator.handle_post_tool_use(
                tool_name,
                tool_input,
                tool_response,
            )
        if event_type == "session-end":
            return coordinator.handle_session_end(hook_context)
        return {"error": f"Unknown event type: {event_type}"}
    except Exception as exc:
        return {"error": str(exc)}


def main():
    """Main entry point for hook execution"""
    raw_input = sys.stdin.read().strip() or "{}"
    try:
        event_data = json.loads(raw_input)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        sys.exit(1)

    result = process_hook_event(event_data)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
