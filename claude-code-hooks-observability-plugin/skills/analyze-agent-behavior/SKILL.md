---
name: analyze-agent-behavior
description: Analyze multi-agent behavior patterns and interactions using observability data. Use this when investigating agent performance, debugging multi-agent workflows, or understanding agent decision-making patterns.
---

# Analyze Agent Behavior

This skill helps analyze multi-agent behavior using the observability system.

## When to Use

Use this skill when:
- Investigating why an agent made certain decisions
- Debugging multi-agent workflows
- Understanding performance bottlenecks
- Analyzing tool usage patterns
- Reviewing session timelines

## Available Data

The observability system tracks:
- PreToolUse/PostToolUse events
- Session start/end events
- User prompts and agent responses
- Subagent lifecycle events
- Tool execution details

## How to Access Data

Use the observability MCP server resources:
- `observability://events/recent` - Recent events across all agents
- `observability://sessions` - Active sessions
- `observability://apps` - Source applications

Or use the tools:
- `query_events` - Filter events by session, app, or type
- `get_session_timeline` - Get chronological event timeline

## Analysis Patterns

1. **Performance Analysis**: Look for time gaps between PreToolUse and PostToolUse
2. **Error Patterns**: Identify recurring failures or blocked tools
3. **Agent Collaboration**: Track SubagentStop events to understand delegation
4. **User Interaction**: Analyze UserPromptSubmit patterns

## Example Queries

To analyze a specific session:
```
Use the get_session_timeline tool with the session_id to see all events in order
```

To find all errors:
```
Use query_events with event_type filter to find specific event patterns
```
