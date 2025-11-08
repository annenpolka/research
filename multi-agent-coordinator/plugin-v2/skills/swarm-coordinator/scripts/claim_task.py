#!/usr/bin/env python3
"""Claim a task from the task queue."""

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


def load_task_state():
    """Load current task state."""
    tasks_file = SWARM_DIR / "tasks.jsonl"
    if not tasks_file.exists():
        return {}

    task_state = {}
    with open(tasks_file, "r") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)

            # Task definition
            if "id" in record and "task_id" not in record:
                task_state[record["id"]] = {**record, "status": "pending"}
            # Task state update
            elif "task_id" in record:
                task_id = record["task_id"]
                if task_id in task_state:
                    task_state[task_id].update(record)

    return task_state


def get_available_tasks(task_state):
    """Get list of available tasks."""
    available = []

    for task_id, task in task_state.items():
        # Must be pending and not assigned
        if task.get("status") != "pending" or task.get("assigned_to"):
            continue

        # Check dependencies
        deps = task.get("dependencies", [])
        all_deps_completed = all(
            task_state.get(dep_id, {}).get("status") == "completed" for dep_id in deps
        )

        if all_deps_completed:
            available.append(task)

    # Sort by priority (descending)
    available.sort(key=lambda t: t.get("priority", 0), reverse=True)

    return available


def claim_task(task_id: str = None):
    """Claim a task."""
    SWARM_DIR.mkdir(parents=True, exist_ok=True)
    agent_id = get_agent_id()
    task_state = load_task_state()

    # Find task to claim
    if task_id:
        task = task_state.get(task_id)
        if not task:
            print(f"❌ Task {task_id} not found")
            return
        if task.get("status") != "pending":
            print(f"❌ Task {task_id} is not available (status: {task.get('status')})")
            return
    else:
        # Auto-assign highest priority task
        available = get_available_tasks(task_state)
        if not available:
            print("No available tasks to claim")
            return
        task = available[0]
        task_id = task["id"]

    # Claim the task
    claim = {
        "task_id": task_id,
        "agent_id": agent_id,
        "claimed_at": datetime.utcnow().isoformat(),
        "status": "in_progress",
    }

    tasks_file = SWARM_DIR / "tasks.jsonl"
    with open(tasks_file, "a") as f:
        f.write(json.dumps(claim) + "\n")

    print(f"✓ Claimed task **{task_id}**: {task.get('description', '')}")
    print()
    print(f"**Priority**: {task.get('priority', 0)}")
    if task.get("files"):
        print(f"**Files**: {', '.join(task['files'])}")
    if task.get("dependencies"):
        print(f"**Dependencies**: {', '.join(task['dependencies'])}")
    print()
    print("You can now work on this task. When complete, use complete_task.py")


def main():
    parser = argparse.ArgumentParser(description="Claim a task from the queue")
    parser.add_argument(
        "--task-id",
        help="Specific task ID to claim (omit for auto-assignment)",
    )

    args = parser.parse_args()

    claim_task(args.task_id)


if __name__ == "__main__":
    main()
