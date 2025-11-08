#!/bin/bash
# Run all tests for swarm-coordinator plugin

set -e

cd "$(dirname "$0")"

echo "Installing test dependencies..."
pip3 install -q -r requirements.txt

echo ""
echo "Running tests..."
python3 -m pytest -v --tb=short --cov=../skills/swarm-coordinator/scripts --cov-report=term-missing

echo ""
echo "All tests passed!"
