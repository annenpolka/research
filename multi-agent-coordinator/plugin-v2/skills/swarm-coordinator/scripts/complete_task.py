#!/usr/bin/env python3
"""Mark a task as completed."""

import argparse
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

SWARM_DIR = Path(".claude/swarm")


def get_agent_id() -> str:
    """Get current agent ID."""
    if "CLAUDE_AGENT_NAME" in os.environ:
        return os.environ["CLAUDE_AGENT_NAME"]

    session_file = SWARM_DIR / ".session"
    if session_file.exists():
        return session_file.read_text().strip()

    agent_id = f"agent-{hashlib.sha256(os.urandom(16)).hexdigest()[:8]}"
    SWARM_DIR.mkdir(parents=True, exist_ok=True)
    session_file.write_text(agent_id)
    return agent_id


def complete_task(task_id: str, summary: str = ""):
    """Mark task as completed."""
    SWARM_DIR.mkdir(parents=True, exist_ok=True)
    agent_id = get_agent_id()

    # Record completion
    completion = {
        "task_id": task_id,
        "agent_id": agent_id,
        "completed_at": datetime.utcnow().isoformat(),
        "status": "completed",
        "summary": summary,
    }

    tasks_file = SWARM_DIR / "tasks.jsonl"
    with open(tasks_file, "a") as f:
        f.write(json.dumps(completion) + "\n")

    # Broadcast completion message
    message = {
        "id": f"msg-{int(datetime.now().timestamp())}-{hashlib.sha256(os.urandom(8)).hexdigest()[:8]}",
        "from": agent_id,
        "to": "all",
        "subject": f"Task {task_id} completed",
        "body": f"Task **{task_id}** has been completed by {agent_id}."
        + (f"\n\nSummary: {summary}" if summary else ""),
        "priority": "normal",
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
    }

    messages_file = SWARM_DIR / "messages.jsonl"
    with open(messages_file, "a") as f:
        f.write(json.dumps(message) + "\n")

    print(f"✓ Task {task_id} marked as completed")
    print("  Broadcast notification sent to all agents")


def main():
    parser = argparse.ArgumentParser(description="Mark a task as completed")
    parser.add_argument("--task-id", required=True, help="Task ID to complete")
    parser.add_argument("--summary", default="", help="Completion summary")

    args = parser.parse_args()

    complete_task(args.task_id, args.summary)


if __name__ == "__main__":
    main()
