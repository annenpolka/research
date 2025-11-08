# Swarm Coordinator Tests

Comprehensive test suite for swarm-coordinator plugin scripts.

## Test Coverage

**31 tests, 79% code coverage**

- `test_send_message.py` - 6 tests for message sending
- `test_get_messages.py` - 5 tests for message retrieval
- `test_task_management.py` - 10 tests for task claiming and completion
- `test_get_state.py` - 10 tests for state queries

## Running Tests

### Quick Run

```bash
./run_tests.sh
```

### Manual Run

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run all tests
python3 -m pytest -v

# Run with coverage
python3 -m pytest --cov=../skills/swarm-coordinator/scripts --cov-report=term-missing

# Run specific test file
python3 -m pytest test_send_message.py -v
```

## Test Structure

Each test file uses:
- `unittest.TestCase` for test structure
- `tempfile` for isolated test environments
- `setUp/tearDown` for clean test isolation
- Environment variable mocking for agent IDs

### Example Test

```python
def test_send_message_content(self):
    """Test that message has correct content."""
    send_message.send_message("RecipientAgent", "Subject", "Body", "high")

    messages_file = self.swarm_dir / "messages.jsonl"
    with open(messages_file, "r") as f:
        message = json.loads(f.read().strip())

    self.assertEqual(message["from"], "TestAgent")
    self.assertEqual(message["to"], "RecipientAgent")
    self.assertEqual(message["priority"], "high")
```

## Coverage Report

Latest run (2025-11-08):

| Script | Statements | Missing | Coverage |
|--------|-----------|---------|----------|
| claim_task.py | 83 | 18 | 78% |
| complete_task.py | 38 | 13 | 66% |
| get_messages.py | 56 | 13 | 77% |
| get_state.py | 112 | 15 | 87% |
| send_message.py | 37 | 9 | 76% |
| **TOTAL** | **326** | **68** | **79%** |

Missing coverage is primarily in:
- `main()` functions (CLI argument parsing)
- Error handling edge cases
- Print statements

These are acceptable gaps as:
1. `main()` is tested via integration/manual testing
2. Core business logic has high coverage
3. Error paths are defensive code

## CI Integration

For continuous integration, add to `.github/workflows/test.yml`:

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r plugin-v2/tests/requirements.txt
      - name: Run tests
        run: cd plugin-v2/tests && pytest -v --cov
```

## Adding New Tests

When adding new functionality:

1. Create test file: `test_<feature>.py`
2. Follow naming convention: `test_<action>_<scenario>`
3. Use `setUp/tearDown` for isolation
4. Mock file system with `tempfile`
5. Run tests to verify coverage

## Hook Coordination Test List (2025-11-08)

- [x] Session start hook emits onboarding context and records the agent session
- [ ] Pre-tool hook blocks edits on files locked by other agents
- [ ] Session end hook releases lingering locks

## Dependencies

- pytest >= 7.0.0
- pytest-cov >= 4.0.0
- Python 3.7+

## Troubleshooting

### Tests fail with "No such file or directory"

Ensure you're in the `tests/` directory:
```bash
cd plugin-v2/tests
python3 -m pytest
```

### Import errors

Add parent directory to path (already handled in test files):
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "skills/swarm-coordinator/scripts"))
```

### Permission denied on scripts

Make scripts executable:
```bash
chmod +x ../skills/swarm-coordinator/scripts/*.py
```
