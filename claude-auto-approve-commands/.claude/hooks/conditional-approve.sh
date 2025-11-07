#!/bin/bash
# Conditional auto-approve hook for Claude Code
# Approves based on tool type and input parameters

TOOL_NAME="${CLAUDE_TOOL_NAME}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT}"

# Parse tool input (simplified - in production use jq)
if [[ "${TOOL_NAME}" == "Bash" ]]; then
    # Check if command is safe (read-only operations)
    if echo "${TOOL_INPUT}" | grep -qE "^(ls|pwd|echo|cat|head|tail|grep|find|git status|git diff|git log)"; then
        cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "permissionDecisionReason": "Safe read-only command approved automatically"
  }
}
EOF
        exit 0
    else
        # Ask user for confirmation on potentially dangerous commands
        cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "ask",
    "permissionDecisionReason": "Command requires user confirmation"
  }
}
EOF
        exit 0
    fi
fi

# For Read tool, check file patterns
if [[ "${TOOL_NAME}" == "Read" ]]; then
    # Auto-approve reading documentation and code files
    if echo "${TOOL_INPUT}" | grep -qE "\.(md|txt|json|js|ts|py|go|rs|sh)"; then
        cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "permissionDecisionReason": "Safe file type approved automatically"
  }
}
EOF
        exit 0
    fi
fi

# Default: ask for approval
cat << 'EOF'
{
  "hookSpecificOutput": {
    "permissionDecision": "ask",
    "permissionDecisionReason": "Default: requesting user confirmation"
  }
}
EOF
exit 0
