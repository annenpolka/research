#!/usr/bin/env python3
"""Get messages sent to this agent."""

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


def get_messages(unread_only: bool = True, limit: int = 20):
    """Get messages for this agent."""
    agent_id = get_agent_id()
    messages_file = SWARM_DIR / "messages.jsonl"

    if not messages_file.exists():
        print("No messages.")
        return

    # Read all messages
    all_messages = []
    with open(messages_file, "r") as f:
        for line in f:
            if line.strip():
                all_messages.append(json.loads(line))

    # Filter messages for this agent
    messages = [
        msg
        for msg in all_messages
        if msg.get("to") == agent_id or msg.get("to") == "all"
    ]

    # Filter unread if requested
    if unread_only:
        messages = [msg for msg in messages if not msg.get("read", False)]

    # Limit results
    messages = messages[-limit:]
    messages.reverse()

    if not messages:
        print("No messages.")
        return

    print(f"📬 {len(messages)} message(s):\n")

    for msg in messages:
        print(f"**From**: {msg.get('from', 'Unknown')}")
        if msg.get("subject"):
            print(f"**Subject**: {msg['subject']}")
        print(f"**Time**: {datetime.fromisoformat(msg['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"**Priority**: {msg.get('priority', 'normal')}")
        print()
        print(msg.get("body", ""))
        print()
        print("---")
        print()


def main():
    parser = argparse.ArgumentParser(description="Get messages sent to this agent")
    parser.add_argument(
        "--unread-only",
        action="store_true",
        help="Only show unread messages",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of messages to show",
    )

    args = parser.parse_args()

    get_messages(args.unread_only, args.limit)


if __name__ == "__main__":
    main()
