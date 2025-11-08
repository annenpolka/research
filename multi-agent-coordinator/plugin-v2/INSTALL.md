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

### Method 1: Via Marketplace (Recommended)

**Step 1**: Start Claude Code
```bash
claude
```

**Step 2**: Add the marketplace (in Claude)
```
/plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
```

**Step 3**: Install the plugin (in Claude)
```
/plugin install swarm-coordinator
```

Or use interactive mode:
```
/plugin
```
Then select "Browse Plugins" → "swarm-coordinator"

### Method 2: GitHub Repository

**In Claude Code:**
```
/plugin marketplace add annenpolka/research
/plugin install swarm-coordinator@annenpolka
```

### Method 3: Local Installation (Development)

```bash
# Clone the repository
git clone https://github.com/annenpolka/research.git
cd research/multi-agent-coordinator/plugin-v2

# Start Claude Code in this directory
claude
```

**In Claude:**
```
/plugin marketplace add .
/plugin install swarm-coordinator
```

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

Add to your project's `.claude/settings.json`:

```json
{
  "marketplaces": [
    {
      "url": "https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json",
      "name": "swarm-coordinator-marketplace"
    }
  ],
  "plugins": {
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

### "Marketplace not found"

Verify the URL is accessible:
```bash
curl -I https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
```

Should return HTTP 200.

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
