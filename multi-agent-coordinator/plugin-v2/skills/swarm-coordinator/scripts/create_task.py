#!/usr/bin/env python3
"""Create a new task with hash-based ID."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from id_generator import generate_task_id

SWARM_DIR = Path(".claude/swarm")


def create_task(
    description: str,
    files: list = None,
    dependencies: list = None,
    priority: int = 5,
):
    """Create a new task with hash-based ID."""
    SWARM_DIR.mkdir(parents=True, exist_ok=True)

    # Generate collision-resistant ID
    task_id = generate_task_id(SWARM_DIR)

    task = {
        "id": task_id,
        "description": description,
        "status": "pending",
        "files": files or [],
        "dependencies": dependencies or [],
        "priority": priority,
        "created_at": datetime.utcnow().isoformat(),
    }

    tasks_file = SWARM_DIR / "tasks.jsonl"
    with open(tasks_file, "a") as f:
        f.write(json.dumps(task) + "\n")

    print(f"✓ Created task **{task_id}**")
    print(f"  Description: {description}")
    print(f"  Priority: {priority}")
    if files:
        print(f"  Files: {', '.join(files)}")
    if dependencies:
        print(f"  Dependencies: {', '.join(dependencies)}")

    return task_id


def main():
    parser = argparse.ArgumentParser(description="Create a new task")
    parser.add_argument("--description", required=True, help="Task description")
    parser.add_argument(
        "--files",
        nargs="+",
        help="File patterns this task affects (e.g., src/auth/**)",
    )
    parser.add_argument(
        "--dependencies",
        nargs="+",
        help="Task IDs that must be completed first",
    )
    parser.add_argument(
        "--priority",
        type=int,
        default=5,
        help="Task priority (0-10, higher = more urgent)",
    )

    args = parser.parse_args()

    create_task(
        description=args.description,
        files=args.files,
        dependencies=args.dependencies,
        priority=args.priority,
    )


if __name__ == "__main__":
    main()
