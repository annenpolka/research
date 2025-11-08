#!/usr/bin/env python3
"""
Hash-based ID generator for collision-resistant identifiers.

Inspired by beads' progressive hash length scaling:
- Small projects (0-500 items): 4-char hash
- Medium projects (500-1,500): 5-char hash
- Large projects (1,500-10,000): 6-char hash

This ensures minimal collision probability while keeping IDs readable.
"""

import hashlib
import time
import os
from pathlib import Path

# Count threshold for hash length scaling
HASH_LENGTH_THRESHOLDS = [
    (0, 4),      # 0-500 items: 4 chars (16^4 = 65,536 combinations)
    (500, 5),    # 500-1,500: 5 chars (16^5 = 1,048,576 combinations)
    (1500, 6),   # 1,500+: 6 chars (16^6 = 16,777,216 combinations)
]


def count_records_in_file(filepath: Path) -> int:
    """Count number of non-empty lines in a JSONL file."""
    if not filepath.exists():
        return 0

    with open(filepath, 'r') as f:
        return sum(1 for line in f if line.strip())


def get_hash_length(record_count: int) -> int:
    """Determine appropriate hash length based on record count."""
    for threshold, length in reversed(HASH_LENGTH_THRESHOLDS):
        if record_count >= threshold:
            return length
    return 4  # Default for small projects


def generate_id(prefix: str, context_file: Path = None) -> str:
    """
    Generate a collision-resistant hash-based ID.

    Args:
        prefix: ID prefix (e.g., "task", "msg", "agent")
        context_file: Optional JSONL file to determine hash length based on record count

    Returns:
        ID string like "task-a1b2c3" or "msg-f4e5d6"

    Example:
        >>> generate_id("task")
        'task-a1b2'
        >>> generate_id("msg", Path(".claude/swarm/messages.jsonl"))
        'msg-f4e5d6'
    """
    # Determine hash length
    if context_file and context_file.exists():
        record_count = count_records_in_file(context_file)
        hash_length = get_hash_length(record_count)
    else:
        hash_length = 4  # Start with 4 chars for new files

    # Generate hash from current time + random data for uniqueness
    data = f"{time.time()}-{os.urandom(16).hex()}"
    hash_val = hashlib.sha256(data.encode()).hexdigest()[:hash_length]

    return f"{prefix}-{hash_val}"


def generate_task_id(swarm_dir: Path = Path(".claude/swarm")) -> str:
    """Generate task ID with progressive hash length."""
    tasks_file = swarm_dir / "tasks.jsonl"
    return generate_id("task", tasks_file)


def generate_message_id(swarm_dir: Path = Path(".claude/swarm")) -> str:
    """Generate message ID with progressive hash length."""
    messages_file = swarm_dir / "messages.jsonl"
    return generate_id("msg", messages_file)


def generate_agent_id() -> str:
    """Generate agent ID (always 8 chars for clarity)."""
    data = f"{time.time()}-{os.urandom(16).hex()}"
    hash_val = hashlib.sha256(data.encode()).hexdigest()[:8]
    return f"agent-{hash_val}"


if __name__ == "__main__":
    # Demo
    print("ID Generation Examples:")
    print(f"Task ID:    {generate_task_id()}")
    print(f"Message ID: {generate_message_id()}")
    print(f"Agent ID:   {generate_agent_id()}")
    print()
    print("Hash length scales with project size:")
    for threshold, length in HASH_LENGTH_THRESHOLDS:
        print(f"  {threshold:>5} records -> {length}-char hash")
