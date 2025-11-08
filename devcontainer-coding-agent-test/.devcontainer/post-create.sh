#!/bin/bash

# Post-create script for coding agent devcontainer
# This script sets up the environment for testing coding agents

set -e

echo "🚀 Setting up coding agent test environment..."

# Update package lists
echo "📦 Updating package lists..."
sudo apt-get update

# Install additional tools for testing
echo "🔧 Installing additional tools..."
sudo apt-get install -y \
    curl \
    wget \
    jq \
    vim \
    tmux \
    ripgrep \
    fd-find \
    bat

# Install Python dependencies
echo "🐍 Setting up Python environment..."
pip install --upgrade pip
pip install \
    pytest \
    black \
    flake8 \
    mypy \
    ipython \
    requests

# Install Node.js dependencies globally
echo "📦 Installing Node.js tools..."
npm install -g \
    prettier \
    eslint \
    typescript \
    ts-node

# Create test workspace
echo "📁 Creating test workspace..."
mkdir -p /workspace/test-projects
mkdir -p /workspace/agent-logs

# Create sample test project
echo "✨ Creating sample test project..."
cat > /workspace/test-projects/sample.py << 'EOF'
def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)

def main():
    """Main function to demonstrate the calculator."""
    for i in range(10):
        print(f"Fibonacci({i}) = {calculate_fibonacci(i)}")

if __name__ == "__main__":
    main()
EOF

cat > /workspace/test-projects/sample.js << 'EOF'
// Sample JavaScript file for testing coding agents

function calculateFactorial(n) {
    if (n <= 1) return 1;
    return n * calculateFactorial(n - 1);
}

function main() {
    console.log('Testing factorial calculation:');
    for (let i = 0; i < 10; i++) {
        console.log(`Factorial(${i}) = ${calculateFactorial(i)}`);
    }
}

main();
EOF

# Create agent testing scripts
echo "🤖 Creating agent testing utilities..."
mkdir -p /workspace/agent-utils

cat > /workspace/agent-utils/test-agent.sh << 'EOF'
#!/bin/bash

# Test script for coding agents
# This script provides common tasks to test agent capabilities

echo "=== Coding Agent Test Suite ==="
echo ""
echo "Available test scenarios:"
echo "1. Code analysis and understanding"
echo "2. Bug fixing"
echo "3. Code refactoring"
echo "4. Test generation"
echo "5. Documentation generation"
echo ""
echo "Test files available in: /workspace/test-projects/"
EOF

chmod +x /workspace/agent-utils/test-agent.sh

# Set up git config (if not already set)
if [ -z "$(git config --global user.name)" ]; then
    git config --global user.name "Coding Agent Test"
    git config --global user.email "agent@test.local"
fi

# Create agent verification file
cat > /workspace/AGENT_VERIFICATION.md << 'EOF'
# Coding Agent Verification Checklist

This file helps verify that coding agents can properly interact with the devcontainer environment.

## Basic Capabilities

- [ ] Read files in the workspace
- [ ] Write new files
- [ ] Edit existing files
- [ ] Execute shell commands
- [ ] Install packages (npm, pip)
- [ ] Run tests
- [ ] Access git operations
- [ ] Use language-specific tools (linters, formatters)

## Advanced Capabilities

- [ ] Multi-file refactoring
- [ ] Complex code analysis
- [ ] Test generation
- [ ] Documentation generation
- [ ] Debugging assistance
- [ ] Performance optimization suggestions

## Environment Verification

- [ ] Python is available: $(python --version)
- [ ] Node.js is available: $(node --version)
- [ ] Git is available: $(git --version)
- [ ] Docker is available: $(docker --version)

## Notes

Add any observations or issues encountered during testing here.
EOF

echo "✅ Devcontainer setup complete!"
echo ""
echo "📍 Test workspace: /workspace/test-projects/"
echo "🔧 Agent utilities: /workspace/agent-utils/"
echo "📋 Verification checklist: /workspace/AGENT_VERIFICATION.md"
echo ""
echo "Ready for coding agent testing! 🎉"
