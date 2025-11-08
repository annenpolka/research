# Installation Guide

## Method 1: Direct GitHub Install (Recommended)

```bash
claude-code plugin install https://github.com/annenpolka/research/tree/main/multi-agent-coordinator/plugin-v2
```

## Method 2: Via Marketplace

### Add the marketplace:

```bash
claude-code plugin marketplace add https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/marketplace.json
```

### Install the plugin:

```bash
claude-code plugin install swarm-coordinator
```

## Method 3: Local Installation (Development)

```bash
# Clone the repository
git clone https://github.com/annenpolka/research.git
cd research/multi-agent-coordinator/plugin-v2

# Install locally
claude-code plugin install .
```

## Verification

After installation, verify it works:

```bash
# Start Claude Code
claude-code

# In Claude, try:
# "Check the swarm state"
# Claude should automatically use the swarm-coordinator skill
```

## Configuration

### Set Agent Name (Optional)

```bash
# Set a custom agent name
export CLAUDE_AGENT_NAME="MyAgent"
claude-code
```

### Define Tasks (Optional)

Create `.claude/swarm/tasks.jsonl`:

```jsonl
{"id":"task-001","description":"Example task","status":"pending","dependencies":[],"priority":10,"files":["src/**"]}
```

## Troubleshooting

### Plugin not found

Ensure the URL is accessible:
```bash
curl -I https://raw.githubusercontent.com/annenpolka/research/main/multi-agent-coordinator/plugin-v2/.claude-plugin/plugin.json
```

### Scripts not executable

```bash
chmod +x ~/.claude/plugins/swarm-coordinator/skills/swarm-coordinator/scripts/*.py
```

### Python version

Requires Python 3.7+:
```bash
python3 --version
```

## Uninstallation

```bash
claude-code plugin uninstall swarm-coordinator

# Optionally remove data
rm -rf .claude/swarm
```
