# Swarm Coordinator Plugin

**Lightweight multi-agent coordination for Claude Code**

## Quick Start

### Install

```bash
claude-code plugin install swarm-coordinator
```

### Setup

```bash
# Build MCP server (first time only)
cd .claude/plugins/swarm-coordinator/mcp-servers/swarm-coordinator
npm install && npm run build
```

### Use

```bash
# Start Claude Code normally
claude-code

# The plugin automatically:
# ✅ Manages file locks when editing
# ✅ Tracks agent sessions
# ✅ Enables multi-agent coordination tools
```

## Multi-Agent Example

### Terminal 1

```bash
export CLAUDE_AGENT_NAME="BackendTeam"
claude-code
```

### Terminal 2

```bash
export CLAUDE_AGENT_NAME="FrontendTeam"
claude-code
```

### Communication

```
# Agent A sends message
> swarm_send_message
  recipient: FrontendTeam
  body: Auth API is ready

# Agent B receives
> swarm_get_messages

# Check swarm state
> swarm_get_state
```

## Available Tools

- `swarm_send_message` - Send messages between agents
- `swarm_get_messages` - Receive messages
- `swarm_claim_task` - Claim a task
- `swarm_complete_task` - Mark task complete
- `swarm_get_state` - Query swarm state

## Features

- **Automatic file locking** - Prevents editing conflicts
- **Task management** - Coordinate work across agents
- **Messaging** - Agent-to-agent communication
- **Git-native** - All metadata in Git-friendly JSONL
- **Non-invasive** - Only uses `.claude/` directory

## Documentation

See parent directory for detailed documentation:

- [Full README](../README.md)
- [Design Details](../DESIGN.md)
- [Comparison with alternatives](../COMPARISON.md)
- [Plugin Guide](../PLUGIN.md)

## License

MIT
