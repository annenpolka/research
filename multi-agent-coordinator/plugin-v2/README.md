# Swarm Coordinator Plugin v2

**Zero-dependency multi-agent coordination - no MCP server, no npm build**

## Key Improvements over v1

| Feature | v1 (MCP) | **v2 (Skills)** |
|---------|----------|-----------------|
| **Install Steps** | 2 (plugin + npm build) | **1 (plugin only)** |
| **Dependencies** | Python + Node.js | **Python only** |
| **Build Required** | Yes (npm build) | **No** |
| **Total Install Time** | ~2 minutes | **~5 seconds** |

## Quick Start

```bash
# Install plugin
claude-code plugin install swarm-coordinator

# That's it! No build step needed.
# Start using immediately:
claude-code
```

## How It Works

### v1 (MCP Server)
- Hooks for file locking
- **MCP server for messaging/tasks** ← Requires Node.js + build

### v2 (Agent Skills)
- Hooks for file locking
- **Agent Skills for messaging/tasks** ← Pure Python, no build

## Architecture

```
plugin-v2/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest (hooks + skills)
├── hooks/
│   └── coordination.py     # File lock management
└── skills/
    └── swarm-coordinator/
        ├── SKILL.md        # Skill definition
        └── scripts/
            ├── send_message.py
            ├── get_messages.py
            ├── claim_task.py
            ├── complete_task.py
            └── get_state.py
```

## Usage Examples

### Send Message

```
User: "Tell BackendTeam that the UI is ready"

Claude automatically:
1. Detects the need to send a message (via skill)
2. Runs scripts/send_message.py
3. Appends to .claude/swarm/messages.jsonl
4. Confirms: "✓ Message sent to BackendTeam"
```

### Check Messages

```
User: "Do I have any messages?"

Claude automatically:
1. Runs scripts/get_messages.py
2. Reads .claude/swarm/messages.jsonl
3. Displays messages
```

### Claim Task

```
User: "What tasks are available? I'll take one"

Claude automatically:
1. Runs scripts/get_state.py --query-type tasks
2. Shows available tasks
3. Runs scripts/claim_task.py
4. Claims highest priority task
```

## File Locks (Automatic)

File locks work exactly the same as v1:

```
# Agent A edits file
PreToolUse hook → Acquires lock

# Agent B tries to edit same file
PreToolUse hook → Detects lock → Blocks edit → Suggests alternatives

# Agent A finishes
PostToolUse hook → Releases lock
```

## Why Skills > MCP?

**MCP Server Approach:**
- Pros: Explicit tools, structured API
- Cons: Requires Node.js, npm build, separate process

**Agent Skills Approach:**
- Pros: No build, no Node.js, Claude decides when to use
- Cons: Less explicit (Claude chooses when to invoke)

For this use case (multi-agent coordination), Skills are superior because:
1. **Zero build step** - Instant installation
2. **Natural language** - "Send a message" just works
3. **Simpler** - Fewer moving parts
4. **Python-only** - Already required for hooks

## Documentation

See parent directory for detailed documentation:
- [Full README](../README.md)
- [Design Details](../DESIGN.md)
- [Comparison with alternatives](../COMPARISON.md)

## Migration from v1

If you're using v1 (MCP version):

```bash
# Uninstall v1
claude-code plugin uninstall swarm-coordinator

# Install v2
claude-code plugin install swarm-coordinator@latest

# Done! No build step needed.
```

Data format is identical - your existing `.claude/swarm/` data works unchanged.

## License

MIT
