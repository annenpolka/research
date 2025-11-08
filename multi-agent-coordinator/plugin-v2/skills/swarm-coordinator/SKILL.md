---
name: swarm-coordinator
description: Multi-agent coordination for managing tasks, messages, and file locks across multiple Claude Code instances
allowed-tools:
  - shell
  - python
---

# Swarm Coordinator

Enables seamless coordination between multiple Claude Code agent instances working on the same project.

## When to Use

Activate this skill when:
- User mentions working with multiple agents or collaboration
- User wants to send messages to other agents
- User asks about available tasks or wants to claim a task
- User wants to check what other agents are doing
- User asks about the swarm state or agent status

## Core Capabilities

### 1. Messaging Between Agents

Send and receive messages between agents in the swarm.

**To send a message:**
```python
python3 ${SKILL_DIR}/scripts/send_message.py --recipient <agent_id> --subject "<subject>" --body "<message>"
```

**To check messages:**
```python
python3 ${SKILL_DIR}/scripts/get_messages.py --unread-only
```

### 2. Task Management

Claim and complete tasks from the shared task queue.

**To claim a task:**
```python
python3 ${SKILL_DIR}/scripts/claim_task.py [--task-id <task_id>]
```

If task_id is omitted, automatically assigns the highest priority available task.

**To complete a task:**
```python
python3 ${SKILL_DIR}/scripts/complete_task.py --task-id <task_id> --summary "<completion summary>"
```

### 3. Swarm State Query

Check the current state of all agents, tasks, and file locks.

**To check swarm state:**
```python
python3 ${SKILL_DIR}/scripts/get_state.py [--query-type all|agents|tasks|locks]
```

## File Lock Management

File locks are automatically managed by hooks - you don't need to explicitly acquire them. When you edit a file:
- PreToolUse hook automatically acquires a lock
- If locked by another agent, you'll be notified
- PostToolUse hook releases the lock when done

## Storage Location

All swarm data is stored in `.claude/swarm/`:
- `agents.jsonl` - Agent registration and activity
- `tasks.jsonl` - Task definitions and state
- `locks.jsonl` - File lock history
- `messages.jsonl` - Inter-agent messages

## Examples

### Example 1: Send a message to another agent

User: "Tell the BackendTeam that the UI is ready"

Response: "I'll send that message to BackendTeam."

Execute:
```bash
python3 ${SKILL_DIR}/scripts/send_message.py \
  --recipient BackendTeam \
  --subject "UI Ready" \
  --body "The UI implementation is complete and ready for integration"
```

Show: "✓ Message sent to BackendTeam"

### Example 2: Check for messages

User: "Check if I have any messages from other agents"

Execute:
```bash
python3 ${SKILL_DIR}/scripts/get_messages.py --unread-only
```

Show the messages in a friendly format.

### Example 3: Claim a task

User: "What tasks are available? I'll take one"

First, check state:
```bash
python3 ${SKILL_DIR}/scripts/get_state.py --query-type tasks
```

Show available tasks, then claim the highest priority:
```bash
python3 ${SKILL_DIR}/scripts/claim_task.py
```

### Example 4: Complete a task

User: "I finished task-001"

Execute:
```bash
python3 ${SKILL_DIR}/scripts/complete_task.py \
  --task-id task-001 \
  --summary "Implemented authentication API with login/logout endpoints"
```

Show: "✓ Task task-001 marked as completed"

### Example 5: Check swarm state

User: "What's the current swarm status?"

Execute:
```bash
python3 ${SKILL_DIR}/scripts/get_state.py --query-type all
```

Show:
- Active agents and their sessions
- Task status (pending/in-progress/completed)
- Active file locks

## Best Practices

1. **Check messages periodically** - Other agents may have important updates
2. **Claim specific tasks** - If you know what you want to work on
3. **Communicate progress** - Send messages when completing major milestones
4. **Check locks before major edits** - See if files are in use
5. **Complete tasks promptly** - Mark tasks done so dependencies can proceed

## Technical Notes

- All scripts use `.claude/swarm/` directory for data storage
- JSONL format ensures Git-friendly, append-only operations
- File locks have a 5-minute TTL (Time To Live) for automatic cleanup
- Agent IDs are read from `.claude/swarm/.session` or `CLAUDE_AGENT_NAME` env var
