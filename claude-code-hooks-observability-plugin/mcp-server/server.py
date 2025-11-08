#!/usr/bin/env python3
"""
Multi-Agent Observability MCP Server
Provides access to observability data via Model Context Protocol
"""

import asyncio
import json
import sqlite3
import sys
from typing import Any, Dict, List

class ObservabilityMCPServer:
    """MCP Server for accessing observability data"""

    def __init__(self, db_path: str = "events.db"):
        self.db_path = db_path

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return [
            {
                "uri": "observability://events/recent",
                "name": "Recent Events",
                "description": "Most recent hook events from all agents",
                "mimeType": "application/json"
            },
            {
                "uri": "observability://sessions",
                "name": "Active Sessions",
                "description": "List of active agent sessions",
                "mimeType": "application/json"
            },
            {
                "uri": "observability://apps",
                "name": "Source Applications",
                "description": "List of source applications",
                "mimeType": "application/json"
            }
        ]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource"""
        if uri == "observability://events/recent":
            return await self.get_recent_events()
        elif uri == "observability://sessions":
            return await self.get_sessions()
        elif uri == "observability://apps":
            return await self.get_apps()
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def get_recent_events(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent events"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, source_app, session_id, hook_event_type,
                   payload, timestamp, summary
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append({
                "id": row[0],
                "source_app": row[1],
                "session_id": row[2],
                "hook_event_type": row[3],
                "payload": json.loads(row[4]) if row[4] else {},
                "timestamp": row[5],
                "summary": row[6]
            })

        return {
            "contents": [{
                "uri": "observability://events/recent",
                "mimeType": "application/json",
                "text": json.dumps(events, indent=2)
            }]
        }

    async def get_sessions(self) -> Dict[str, Any]:
        """Get active sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT session_id, MAX(timestamp) as last_activity
            FROM events
            GROUP BY session_id
            ORDER BY last_activity DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()
        conn.close()

        sessions = [{"session_id": row[0], "last_activity": row[1]} for row in rows]

        return {
            "contents": [{
                "uri": "observability://sessions",
                "mimeType": "application/json",
                "text": json.dumps(sessions, indent=2)
            }]
        }

    async def get_apps(self) -> Dict[str, Any]:
        """Get source applications"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT source_app, COUNT(*) as event_count
            FROM events
            GROUP BY source_app
            ORDER BY event_count DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        apps = [{"source_app": row[0], "event_count": row[1]} for row in rows]

        return {
            "contents": [{
                "uri": "observability://apps",
                "mimeType": "application/json",
                "text": json.dumps(apps, indent=2)
            }]
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [
            {
                "name": "query_events",
                "description": "Query events by session, app, or event type",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Filter by session ID"
                        },
                        "source_app": {
                            "type": "string",
                            "description": "Filter by source application"
                        },
                        "event_type": {
                            "type": "string",
                            "description": "Filter by event type"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of events to return",
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "get_session_timeline",
                "description": "Get chronological timeline of events for a session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID to retrieve timeline for"
                        }
                    },
                    "required": ["session_id"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if name == "query_events":
            return await self.query_events(**arguments)
        elif name == "get_session_timeline":
            return await self.get_session_timeline(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def query_events(self, session_id: str = None, source_app: str = None,
                          event_type: str = None, limit: int = 50) -> Dict[str, Any]:
        """Query events with filters"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT id, source_app, session_id, hook_event_type, payload, timestamp, summary FROM events WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if source_app:
            query += " AND source_app = ?"
            params.append(source_app)
        if event_type:
            query += " AND hook_event_type = ?"
            params.append(event_type)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        events = []
        for row in rows:
            events.append({
                "id": row[0],
                "source_app": row[1],
                "session_id": row[2],
                "hook_event_type": row[3],
                "payload": json.loads(row[4]) if row[4] else {},
                "timestamp": row[5],
                "summary": row[6]
            })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(events, indent=2)
            }]
        }

    async def get_session_timeline(self, session_id: str) -> Dict[str, Any]:
        """Get timeline for a specific session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, source_app, session_id, hook_event_type,
                   payload, timestamp, summary
            FROM events
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))

        rows = cursor.fetchall()
        conn.close()

        timeline = []
        for row in rows:
            timeline.append({
                "id": row[0],
                "source_app": row[1],
                "session_id": row[2],
                "hook_event_type": row[3],
                "payload": json.loads(row[4]) if row[4] else {},
                "timestamp": row[5],
                "summary": row[6]
            })

        return {
            "content": [{
                "type": "text",
                "text": json.dumps(timeline, indent=2)
            }]
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        method = request.get("method")

        if method == "resources/list":
            resources = await self.list_resources()
            return {"resources": resources}

        elif method == "resources/read":
            uri = request.get("params", {}).get("uri")
            return await self.read_resource(uri)

        elif method == "tools/list":
            tools = await self.list_tools()
            return {"tools": tools}

        elif method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            return await self.call_tool(name, arguments)

        else:
            raise ValueError(f"Unknown method: {method}")

    async def run(self):
        """Run the MCP server (stdio transport)"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                request = json.loads(line)
                response = await self.handle_request(request)

                # Send response
                output = json.dumps(response)
                print(output, flush=True)

            except Exception as e:
                error_response = {
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    server = ObservabilityMCPServer()
    asyncio.run(server.run())
