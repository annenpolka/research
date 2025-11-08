# Multi-Agent Observability Plugin for Claude Code

A comprehensive Claude Code plugin that provides real-time monitoring and visualization for multi-agent workflows through hook event tracking.

## Overview

This plugin transforms the [claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) system into a reusable Claude Code plugin with three main components:

1. **Hook System**: Automatically captures and logs all agent events
2. **MCP Server**: Provides programmatic access to observability data
3. **Management Commands**: Easy server and dashboard management

## Features

### Automatic Event Tracking

The plugin automatically tracks all Claude Code lifecycle events:
- PreToolUse / PostToolUse
- SessionStart / SessionEnd
- UserPromptSubmit
- Stop / SubagentStop
- PreCompact
- Notification

### MCP Server Integration

Access observability data directly from Claude through the MCP server:

**Resources:**
- `observability://events/recent` - Most recent events
- `observability://sessions` - Active sessions
- `observability://apps` - Source applications

**Tools:**
- `query_events` - Filter events by session, app, or type
- `get_session_timeline` - Get chronological event timeline for a session

### Agent Behavior Analysis Skill

Built-in skill for analyzing multi-agent behavior patterns:
- Performance analysis
- Error pattern detection
- Agent collaboration tracking
- User interaction analysis

## Installation

### Prerequisites

- Claude Code CLI
- Python 3.8+
- Bun (for running the observability server)
- uv (Python package manager)

### Plugin Installation

1. **Add plugin to your marketplace**:
   ```bash
   # Add to your local plugin marketplace
   cp -r multi-agent-observability ~/.claude/plugins/
   ```

2. **Install from marketplace**:
   ```bash
   # Or configure in your project's .claude/settings.json
   {
     "plugins": {
       "marketplaces": [
         "file://~/.claude/plugins"
       ],
       "installed": [
         "multi-agent-observability"
       ]
     }
   }
   ```

### Server Setup

The observability server needs to be installed separately:

```bash
# Clone the original repository
git clone https://github.com/disler/claude-code-hooks-multi-agent-observability.git

# Install server dependencies
cd claude-code-hooks-multi-agent-observability/apps/server
bun install

# Install client dependencies
cd ../client
npm install
```

## Usage

### Starting the Observability System

```bash
# In Claude Code, use the command:
/observability-start
```

This will:
- Start the observability server on port 4000
- Start the dashboard on port 5173
- Begin collecting events from hooks

### Viewing the Dashboard

```bash
/observability-dashboard
```

Opens the visualization dashboard in your browser at `http://localhost:5173`.

### Querying Data with MCP

The MCP server provides programmatic access to observability data. Claude can automatically use these resources when analyzing agent behavior:

**Example**: "Show me the recent events from the last session"
- Claude will use the `query_events` tool to retrieve and display events

**Example**: "What happened in session XYZ?"
- Claude will use `get_session_timeline` to show the chronological event sequence

### Analyzing Agent Behavior

Simply ask Claude to analyze agent behavior, and the `analyze-agent-behavior` skill will activate:

- "Why did the agent choose to use the Bash tool here?"
- "Show me the performance bottlenecks in this session"
- "How many times did the agent call subagents?"

### Stopping the Server

```bash
/observability-stop
```

## Architecture

### Plugin Structure

```
multi-agent-observability/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── hooks/
│   ├── hooks.json            # Hook configurations
│   └── send_event.py         # Event sender script
├── mcp-server/
│   └── server.py             # MCP server implementation
├── skills/
│   └── analyze-agent-behavior/
│       └── SKILL.md          # Behavior analysis skill
├── commands/
│   ├── observability-start.md
│   ├── observability-stop.md
│   └── observability-dashboard.md
├── .mcp.json                 # MCP server configuration
└── README.md
```

### Data Flow

```
Claude Agent → Hooks → HTTP POST → Server → SQLite → WebSocket → Dashboard
                                        ↓
                                   MCP Server → Claude (for analysis)
```

## Configuration

### Custom Server URL

By default, events are sent to `http://localhost:4000/events`. To use a different server:

Edit `hooks/hooks.json` and add `--server-url` parameter:

```json
{
  "command": "uv run ${CLAUDE_PLUGIN_ROOT}/hooks/send_event.py --server-url http://custom-host:port/events ..."
}
```

### Database Location

The MCP server reads from `./events.db` by default. To use a different location, update `.mcp.json`:

```json
{
  "mcpServers": {
    "observability": {
      "env": {
        "DB_PATH": "/path/to/events.db"
      }
    }
  }
}
```

## Comparison with Original Repository

### Original System
- Manual setup required
- Copy `.claude` directory to each project
- Server must be started manually
- No built-in data querying

### Plugin Version
- One-time installation via plugin system
- Automatic hook registration
- MCP server for programmatic data access
- Built-in analysis skills
- Management commands for easy control
- Reusable across all projects

## Implementation Notes

### What This Plugin Provides

✅ **Automated Hook Registration**: All hooks automatically installed with the plugin

✅ **MCP Server**: Programmatic access to observability data through Claude

✅ **Management Commands**: Easy server lifecycle management

✅ **Analysis Skills**: Built-in agent behavior analysis

### What You Still Need

⚠️ **Observability Server**: The Bun server and Vue dashboard from the original repository must be installed separately

⚠️ **Server Management**: While commands exist, the server process management needs to be implemented based on your environment

### Why Not Include the Server?

The original server and dashboard are complex applications with:
- Bun runtime dependency
- Vue 3 build process
- WebSocket infrastructure
- Database management

Including these in a plugin would:
- Significantly increase plugin size
- Require runtime dependency management
- Complicate installation and updates

Instead, this plugin provides:
- Seamless hook integration
- MCP-based data access
- Commands to manage the external server

## Development

### Testing the Plugin

1. Install the plugin locally
2. Start a Claude Code session
3. Check that hooks are firing: events should appear in the server logs
4. Test MCP server: ask Claude to query observability data
5. Verify commands work: try `/observability-start`

### Extending the Plugin

**Add new hooks**: Edit `hooks/hooks.json`

**Add new MCP tools**: Extend `mcp-server/server.py`

**Add analysis skills**: Create new skill directories in `skills/`

**Add commands**: Create new markdown files in `commands/`

## Troubleshooting

### Hooks Not Firing

1. Check plugin installation: `claude plugins list`
2. Verify server is running: `curl http://localhost:4000/events`
3. Check hook script permissions: `chmod +x hooks/send_event.py`

### MCP Server Not Working

1. Verify Python 3.8+ is installed
2. Check database path in `.mcp.json`
3. Test server manually: `python3 mcp-server/server.py`

### Events Not Appearing in Dashboard

1. Verify server is running on port 4000
2. Check client is running on port 5173
3. Check browser console for WebSocket errors

## Security Considerations

- Events are sent to localhost by default
- No authentication on the observability server
- Database contains full conversation transcripts
- Suitable for local development only

For production use:
- Add authentication to the server
- Use HTTPS for remote servers
- Implement data retention policies
- Sanitize sensitive data from events

## License

MIT (same as original repository)

## Credits

This plugin is based on the excellent work by [@disler](https://github.com/disler) in the [claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) repository.

## Contributing

Contributions are welcome! Please:
1. Test changes thoroughly
2. Update documentation
3. Follow existing code style
4. Submit pull requests with clear descriptions

## Roadmap

- [ ] Built-in server process management
- [ ] Bundled lightweight dashboard
- [ ] Advanced filtering tools in MCP server
- [ ] Performance analytics skill
- [ ] Export/import observability data
- [ ] Remote server support with authentication
- [ ] Real-time event streaming via MCP

## Support

For issues related to:
- **Plugin functionality**: Open an issue in this repository
- **Original server/dashboard**: See the [original repository](https://github.com/disler/claude-code-hooks-multi-agent-observability)
- **Claude Code itself**: Check [Claude Code documentation](https://code.claude.com/docs)
