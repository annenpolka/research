# Installation Guide

## Prerequisites

1. **Claude Code CLI installed**
   ```bash
   # macOS / Linux / WSL
   curl -fsSL https://claude.ai/install.sh | bash

   # Or via npm (requires Node.js 18+)
   npm install -g @anthropic-ai/claude-code

   # Windows PowerShell
   irm https://claude.ai/install.ps1 | iex
   ```

2. **Python 3.7+**
   ```bash
   python3 --version
   ```

3. **Verify installation**
   ```bash
   claude doctor
   ```

## Installation Methods

### Method 1: Local Installation (Recommended)

This is the most reliable method and works for development/testing.

**Step 1**: Clone the repository
```bash
git clone https://github.com/annenpolka/research.git
cd research/multi-agent-coordinator/plugin-v2
```

**Step 2**: Start Claude Code in the plugin directory
```bash
claude
```

**Step 3**: Add the marketplace and install (in Claude)
```
/plugin marketplace add .
/plugin install swarm-coordinator
```

**Verification**:
```
/plugin
```
You should see "swarm-coordinator" installed.

### Method 2: Direct Plugin Installation (Alternative)

If you already cloned the repository, you can install the plugin directly:

**In Claude Code (from any directory):**
```
/plugin install /absolute/path/to/research/multi-agent-coordinator/plugin-v2
```

Replace `/absolute/path/to/` with the actual path.

## Verification

After installation, verify it works:

**In Claude:**
```
/help
```

You should see swarm-coordinator commands available.

**Test the skill:**
```
Check the swarm state
```

Claude should automatically use the swarm-coordinator skill and show:
```
## 🤖 Active Agents (0)
No active agents.

## 📋 Tasks
...
```

## Configuration

### Set Agent Name (Optional)

```bash
# Set a custom agent name before starting Claude
export CLAUDE_AGENT_NAME="MyAgent"
claude
```

### Define Tasks (Optional)

Create `.claude/swarm/tasks.jsonl` in your project:

```jsonl
{"id":"task-001","description":"Example task","status":"pending","dependencies":[],"priority":10,"files":["src/**"]}
```

### Team Setup (Automatic Installation)

Add to your project's `.claude/settings.json` (Claude Code looks for the `extraKnownMarketplaces` and `enabledPlugins` keys):

```json
{
  "extraKnownMarketplaces": {
    "swarm-coordinator-marketplace": {
      "source": {
        "type": "json",
        "url": "https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json"
      }
    }
  },
  "enabledPlugins": {
    "swarm-coordinator": {
      "enabled": true,
      "settings": {
        "lockTimeoutMinutes": 5,
        "maxAgents": 10
      }
    }
  }
}
```

Team members will automatically have access to the plugin when they open the project.

### Hook & Skill Definitions

- `hooks/hooks.json` keeps the PascalCase hook names (`SessionStart`, `PreToolUse`, `PostToolUse`, `SessionEnd`) that Claude Code documents, so the runtime delivers the standard `hook_event_name` + `tool_input` payloads straight into `hooks/coordination.py`. If you need to customize the locking behavior, edit this file instead of the manifest so you stay within the supported schema.
- `skills/swarm-coordinator/SKILL.md` provides the skill metadata (name, description, allowed-tools) and the `scripts/` directory contains the Python entry points, which is exactly how Claude Code expects marketplace skills to be laid out. This is the spot to add new scripts or update the YAML front matter before publishing.

## Plugin Management Commands

**In Claude Code:**

```
/plugin                              # Interactive plugin menu
/plugin marketplace list             # List marketplaces
/plugin marketplace update <name>    # Update marketplace
/plugin marketplace remove <name>    # Remove marketplace
/plugin install <name>               # Install plugin
/plugin enable <name>                # Enable plugin
/plugin disable <name>               # Disable plugin
/plugin uninstall <name>             # Uninstall plugin
```

## Troubleshooting

### "command not found: claude"

Claude Code is not installed. Install it:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then open a new terminal or:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### "/plugin: unknown command"

You may be using an old version of Claude Code. Update it:

```bash
# If installed via npm
npm update -g @anthropic-ai/claude-code

# If installed natively
curl -fsSL https://claude.ai/install.sh | bash
```

### "Invalid marketplace schema" or schema validation errors

If you see errors such as:
```
Error: Invalid marketplace schema from URL: name: Marketplace name cannot contain spaces...
```

Claude Code does accept HTTP/HTTPS marketplaces, but the document must match the schema published in the official docs. Double-check that your URL points directly to the `.../.claude-plugin/marketplace.json` file, then run:

```
/plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
/plugin marketplace list
```

If the schema error persists (for example, due to a partially cached file), fall back to Method 1 (clone the repo locally and run `/plugin marketplace add .`) or Method 2 (`/plugin install /absolute/path/...`).

### Scripts not executable

```bash
chmod +x ~/.claude/plugins/swarm-coordinator/skills/swarm-coordinator/scripts/*.py
```

### Python version

Requires Python 3.7+:
```bash
python3 --version
```

### Plugin not working

1. Restart Claude Code:
   ```
   /exit
   ```
   Then start again: `claude`

2. Check plugin status:
   ```
   /plugin
   ```

3. Verify skills directory:
   ```bash
   ls -la ~/.claude/plugins/swarm-coordinator/skills/
   ```

## Uninstallation

**In Claude:**
```
/plugin uninstall swarm-coordinator
```

Optionally remove data:
```bash
rm -rf .claude/swarm
```

## Quick Reference

| Action | Command |
|--------|---------|
| Start Claude | `claude` |
| Add marketplace | `/plugin marketplace add <url>` |
| Install plugin | `/plugin install swarm-coordinator` |
| Interactive install | `/plugin` |
| Check swarm | "Check the swarm state" (natural language) |
| Send message | "Send message to AgentB: ..." (natural language) |
| Claim task | "Claim a task" (natural language) |
| Help | `/help` |
| Exit | `/exit` |

## See Also

- [README.md](./README.md) - Plugin overview
- [CORRECT_INSTALLATION.md](../CORRECT_INSTALLATION.md) - Detailed installation guide
- [tests/README.md](./tests/README.md) - Test suite documentation
