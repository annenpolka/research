#!/bin/bash
# Auto-approve hook for Claude Code
# Automatically approves tool calls without user confirmation

# Get environment variables provided by Claude Code
TOOL_NAME="${CLAUDE_TOOL_NAME}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT}"

# Log the auto-approval (optional, for debugging)
# echo "[AUTO-APPROVE] Tool: ${TOOL_NAME}" >&2

# Return JSON with approval decision
cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "permissionDecisionReason": "Auto-approved by configuration"
  }
}
EOF

# Exit with success (0 = allow, 2 = block)
exit 0
