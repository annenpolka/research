#!/usr/bin/env python3
"""Query current swarm state."""

import argparse
import json
from datetime import datetime
from pathlib import Path

SWARM_DIR = Path(".claude/swarm")


def get_agents():
    """Get active agents."""
    agents_file = SWARM_DIR / "agents.jsonl"
    if not agents_file.exists():
        return {}

    active_agents = {}
    with open(agents_file, "r") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            agent_id = record.get("id")

            if not agent_id:
                continue

            if record.get("terminated_at"):
                # Agent terminated
                active_agents.pop(agent_id, None)
            else:
                # Agent started
                active_agents[agent_id] = record

    return active_agents


def get_tasks():
    """Get task state."""
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


def get_locks():
    """Get active file locks."""
    locks_file = SWARM_DIR / "locks.jsonl"
    if not locks_file.exists():
        return {}

    active_locks = {}
    with open(locks_file, "r") as f:
        for line in f:
            if not line.strip():
                continue

            record = json.loads(line)
            file_path = record.get("file_path")

            if not file_path:
                continue

            if record.get("status") == "released":
                # Lock released
                active_locks.pop(file_path, None)
            elif record.get("holder"):
                # Check if expired
                expires_at = datetime.fromisoformat(record["expires_at"])
                if expires_at > datetime.utcnow():
                    active_locks[file_path] = record
                else:
                    # Expired
                    active_locks.pop(file_path, None)

    return active_locks


def print_agents(agents):
    """Print agent information."""
    print(f"## 🤖 Active Agents ({len(agents)})\n")
    if agents:
        for agent_id, agent in agents.items():
            started = datetime.fromisoformat(agent["started_at"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            print(f"- **{agent_id}** (started: {started})")
    else:
        print("No active agents.")
    print()


def print_tasks(tasks):
    """Print task information."""
    by_status = {"pending": [], "in_progress": [], "completed": []}

    for task in tasks.values():
        status = task.get("status", "pending")
        by_status[status].append(task)

    print(f"## 📋 Tasks\n")
    print(f"- Pending: {len(by_status['pending'])}")
    print(f"- In Progress: {len(by_status['in_progress'])}")
    print(f"- Completed: {len(by_status['completed'])}")
    print()

    if by_status["in_progress"]:
        print("**In Progress**:")
        for task in by_status["in_progress"]:
            print(
                f"- {task['id']} (by {task.get('agent_id', 'unknown')}): {task.get('description', '')}"
            )
        print()


def print_locks(locks):
    """Print lock information."""
    print(f"## 🔒 Active File Locks ({len(locks)})\n")
    if locks:
        for file_path, lock in locks.items():
            expires_at = datetime.fromisoformat(lock["expires_at"])
            remaining = int((expires_at - datetime.utcnow()).total_seconds() / 60)
            print(f"- **{file_path}**")
            print(f"  - Holder: {lock['holder']}")
            print(f"  - Reason: {lock.get('reason', 'unknown')}")
            print(f"  - Expires in: {max(0, remaining)} min")
    else:
        print("No active locks.")
    print()


def get_state(query_type: str = "all"):
    """Get and print swarm state."""
    if query_type in ["agents", "all"]:
        agents = get_agents()
        print_agents(agents)

    if query_type in ["tasks", "all"]:
        tasks = get_tasks()
        print_tasks(tasks)

    if query_type in ["locks", "all"]:
        locks = get_locks()
        print_locks(locks)


def main():
    parser = argparse.ArgumentParser(description="Query swarm state")
    parser.add_argument(
        "--query-type",
        choices=["all", "agents", "tasks", "locks"],
        default="all",
        help="Type of state to query",
    )

    args = parser.parse_args()

    get_state(args.query_type)


if __name__ == "__main__":
    main()
