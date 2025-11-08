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
# Start Claude Code
claude
```

**In Claude (remote marketplace install):**
```
/plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
/plugin marketplace list
/plugin install swarm-coordinator
```

`/plugin marketplace list` confirms that Claude registered the HTTPS marketplace URL before you install the plugin, matching the flow described in Claude Code's marketplace documentation.

That's it! No build step needed.

See [INSTALL.md](./INSTALL.md) for detailed instructions.

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

## Hook & Skill Definitions

Claude Code expects plugin hooks to be described with PascalCase event names such as `SessionStart`, `PreToolUse`, `PostToolUse`, and `SessionEnd`, and to receive the standard hook payload fields (`hook_event_name`, `tool_name`, `tool_input`, `tool_response`). Our manifest now points to `hooks/hooks.json`, which follows that schema and routes each event to `hooks/coordination.py` so file locks stay in sync with the official runtime contract.

The swarm skill stays under `skills/swarm-coordinator`, where `SKILL.md` provides the required front matter (name, description, allowed-tools) and the `scripts/` directory holds the actual entry points, matching Claude Code's skill packaging rules for marketplace distribution.

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

If you're using v1 (MCP version), uninstall it first:

**In Claude:**
```
/plugin uninstall swarm-coordinator
```

Then install v2 following the Quick Start instructions above.

Data format is identical - your existing `.claude/swarm/` data works unchanged.

## License

MIT
