#!/bin/bash

# Agent Verification Script
# This script helps verify that a coding agent can successfully interact with the devcontainer

set -e

COLORS_RED='\033[0;31m'
COLORS_GREEN='\033[0;32m'
COLORS_YELLOW='\033[1;33m'
COLORS_BLUE='\033[0;34m'
COLORS_NC='\033[0m' # No Color

echo -e "${COLORS_BLUE}================================${COLORS_NC}"
echo -e "${COLORS_BLUE}Coding Agent Verification Script${COLORS_NC}"
echo -e "${COLORS_BLUE}================================${COLORS_NC}"
echo ""

# Function to check command existence
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${COLORS_GREEN}✓${COLORS_NC} $1 is installed: $(command -v $1)"
        return 0
    else
        echo -e "${COLORS_RED}✗${COLORS_NC} $1 is NOT installed"
        return 1
    fi
}

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo ""
    echo -e "${COLORS_YELLOW}Testing: ${test_name}${COLORS_NC}"

    if eval "$test_command"; then
        echo -e "${COLORS_GREEN}✓ ${test_name} passed${COLORS_NC}"
        return 0
    else
        echo -e "${COLORS_RED}✗ ${test_name} failed${COLORS_NC}"
        return 1
    fi
}

# Check essential commands
echo -e "${COLORS_BLUE}Checking essential tools...${COLORS_NC}"
check_command python3
check_command pip
check_command node
check_command npm
check_command git
check_command docker || echo -e "${COLORS_YELLOW}Warning: Docker may not be available in all devcontainer configurations${COLORS_NC}"

# Check Python version
echo ""
echo -e "${COLORS_BLUE}Python version:${COLORS_NC}"
python3 --version

# Check Node version
echo ""
echo -e "${COLORS_BLUE}Node.js version:${COLORS_NC}"
node --version

# Check Git version
echo ""
echo -e "${COLORS_BLUE}Git version:${COLORS_NC}"
git --version

# Verify file operations
echo ""
echo -e "${COLORS_BLUE}Testing file operations...${COLORS_NC}"

# Create test directory
TEST_DIR="/tmp/agent-test-$$"
mkdir -p "$TEST_DIR"

# Test file writing
run_test "Write file" "echo 'Hello from coding agent' > $TEST_DIR/test.txt"

# Test file reading
run_test "Read file" "grep 'Hello' $TEST_DIR/test.txt > /dev/null"

# Test file editing
run_test "Edit file" "sed -i 's/Hello/Goodbye/' $TEST_DIR/test.txt && grep 'Goodbye' $TEST_DIR/test.txt > /dev/null"

# Test file deletion
run_test "Delete file" "rm $TEST_DIR/test.txt && [ ! -f $TEST_DIR/test.txt ]"

# Clean up
rmdir "$TEST_DIR"

# Test Python execution
echo ""
echo -e "${COLORS_BLUE}Testing Python execution...${COLORS_NC}"
run_test "Run Python script" "python3 -c 'print(\"Python execution works\")'"

# Test Node execution
echo ""
echo -e "${COLORS_BLUE}Testing Node.js execution...${COLORS_NC}"
run_test "Run Node.js script" "node -e 'console.log(\"Node.js execution works\")'"

# Test package installation (Python)
echo ""
echo -e "${COLORS_BLUE}Testing Python package installation...${COLORS_NC}"
run_test "Install Python package" "pip install --quiet requests && python3 -c 'import requests'"

# Test package installation (Node)
echo ""
echo -e "${COLORS_BLUE}Testing Node.js package installation...${COLORS_NC}"
run_test "Install Node.js package" "cd /tmp && npm install --silent lodash && node -e 'require(\"lodash\")'"

# Test git operations
echo ""
echo -e "${COLORS_BLUE}Testing Git operations...${COLORS_NC}"
GIT_TEST_DIR="/tmp/git-test-$$"
mkdir -p "$GIT_TEST_DIR"
cd "$GIT_TEST_DIR"

run_test "Git init" "git init"
run_test "Git config" "git config user.email 'test@example.com' && git config user.name 'Test User'"
run_test "Git add" "echo 'test' > test.txt && git add test.txt"
run_test "Git commit" "git commit -m 'Test commit'"

# Clean up
cd /
rm -rf "$GIT_TEST_DIR"

# Summary
echo ""
echo -e "${COLORS_BLUE}================================${COLORS_NC}"
echo -e "${COLORS_GREEN}Verification complete!${COLORS_NC}"
echo -e "${COLORS_BLUE}================================${COLORS_NC}"
echo ""
echo "The devcontainer environment is ready for coding agent testing."
echo ""
echo "Next steps:"
echo "1. Test your coding agent with the sample projects in test-projects/"
echo "2. Try the buggy calculator fixing task"
echo "3. Try the code refactoring task"
echo "4. Check if the agent can generate tests"
echo ""
