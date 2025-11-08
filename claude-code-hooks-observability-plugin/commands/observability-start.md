---
description: Start the multi-agent observability server
---

Start the multi-agent observability server and dashboard.

Steps:
1. Navigate to the observability server directory in the plugin
2. Install dependencies if needed (bun install)
3. Start the server on port 4000
4. Inform the user that the server is running
5. Provide the dashboard URL (default: http://localhost:5173)

The server will:
- Accept hook events on http://localhost:4000/events
- Provide WebSocket streaming on ws://localhost:4000/stream
- Store events in SQLite database

Remember to run the server in the background so it doesn't block the terminal.
