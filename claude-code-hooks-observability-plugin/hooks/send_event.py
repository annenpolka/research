#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

"""
Multi-Agent Observability Hook Script
Sends Claude Code hook events to the observability server.
"""

import json
import sys
import os
import argparse
import urllib.request
import urllib.error
from datetime import datetime

def send_event_to_server(event_data, server_url='http://localhost:4000/events'):
    """Send event data to the observability server."""
    try:
        req = urllib.request.Request(
            server_url,
            data=json.dumps(event_data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Claude-Code-Hook/1.0'
            }
        )

        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200

    except (urllib.error.URLError, Exception):
        # Silently fail to not interrupt Claude Code
        return False

def main():
    parser = argparse.ArgumentParser(description='Send Claude Code hook events to observability server')
    parser.add_argument('--source-app', required=True, help='Source application name')
    parser.add_argument('--event-type', required=True, help='Hook event type')
    parser.add_argument('--server-url', default='http://localhost:4000/events', help='Server URL')
    parser.add_argument('--add-chat', action='store_true', help='Include chat transcript')
    parser.add_argument('--summarize', action='store_true', help='Generate AI summary (placeholder)')

    args = parser.parse_args()

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    session_id = input_data.get('session_id', 'unknown')

    event_data = {
        'source_app': args.source_app,
        'session_id': session_id,
        'hook_event_type': args.event_type,
        'payload': input_data,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'model_name': ''
    }

    # Add chat if requested
    if args.add_chat and 'transcript_path' in input_data:
        transcript_path = input_data['transcript_path']
        if os.path.exists(transcript_path):
            chat_data = []
            try:
                with open(transcript_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                chat_data.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                event_data['chat'] = chat_data
            except Exception:
                pass

    # Send to server
    send_event_to_server(event_data, args.server_url)

    # Always exit cleanly
    sys.exit(0)

if __name__ == '__main__':
    main()
