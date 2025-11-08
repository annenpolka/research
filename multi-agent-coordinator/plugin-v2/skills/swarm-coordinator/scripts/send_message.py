#!/usr/bin/env python3
"""Send a message to another agent in the swarm."""

import argparse
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from id_generator import generate_message_id, generate_agent_id

SWARM_DIR = Path(".claude/swarm")


def get_agent_id() -> str:
    """Get current agent ID."""
    # Check environment variable
    if "CLAUDE_AGENT_NAME" in os.environ:
        return os.environ["CLAUDE_AGENT_NAME"]

    # Check session file
    session_file = SWARM_DIR / ".session"
    if session_file.exists():
        return session_file.read_text().strip()

    # Generate new ID using id_generator
    agent_id = generate_agent_id()
    SWARM_DIR.mkdir(parents=True, exist_ok=True)
    session_file.write_text(agent_id)
    return agent_id


def send_message(recipient: str, subject: str, body: str, priority: str = "normal"):
    """Send a message to another agent."""
    SWARM_DIR.mkdir(parents=True, exist_ok=True)

    message = {
        "id": generate_message_id(SWARM_DIR),
        "from": get_agent_id(),
        "to": recipient,
        "subject": subject,
        "body": body,
        "priority": priority,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
    }

    messages_file = SWARM_DIR / "messages.jsonl"
    with open(messages_file, "a") as f:
        f.write(json.dumps(message) + "\n")

    print(f"✓ Message sent to {recipient}")
    if subject:
        print(f"  Subject: {subject}")
    print(f"  Priority: {priority}")


def main():
    parser = argparse.ArgumentParser(description="Send a message to another agent")
    parser.add_argument("--recipient", required=True, help="Agent ID or 'all' for broadcast")
    parser.add_argument("--subject", default="", help="Message subject")
    parser.add_argument("--body", required=True, help="Message content")
    parser.add_argument(
        "--priority",
        choices=["low", "normal", "high"],
        default="normal",
        help="Message priority",
    )

    args = parser.parse_args()

    send_message(args.recipient, args.subject, args.body, args.priority)


if __name__ == "__main__":
    main()
