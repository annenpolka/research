# Coding Agent Test Tasks

This file contains a series of tasks designed to test the capabilities of coding agents (like Claude Code, GitHub Copilot, etc.) in a devcontainer environment.

## Setup Tasks

### Task 0: Environment Verification
**Objective**: Verify that the devcontainer environment is properly set up.

**Instructions**:
1. Run the verification script: `bash agent-verification.sh`
2. Ensure all checks pass
3. Report any failures or issues

**Expected Outcome**: All verification checks should pass.

---

## Basic Tasks

### Task 1: Bug Fixing
**Objective**: Identify and fix bugs in the calculator module.

**Instructions**:
1. Examine the file `test-projects/buggy-calculator.py`
2. Read the test file `test-projects/test_calculator.py`
3. Identify the bugs in the calculator
4. Fix all bugs
5. Ensure all tests pass

**Expected Outcome**:
- All bugs in the calculator are fixed
- All tests pass when running `pytest test-projects/test_calculator.py`

**Hints**:
- There are at least 3 bugs in arithmetic operations
- There's a missing error handling case
- Check the comments marked with "BUG"

---

### Task 2: Code Refactoring
**Objective**: Refactor poorly written JavaScript code to follow best practices.

**Instructions**:
1. Examine the file `test-projects/refactor-me.js`
2. Identify code smells and anti-patterns
3. Refactor the code to improve:
   - Use of modern JavaScript features (ES6+)
   - Separation of concerns
   - Reduction of code duplication
   - Removal of global variables
   - Better naming and structure

**Expected Outcome**:
- Code uses modern JavaScript (const/let, arrow functions, classes, etc.)
- No global variables
- Functions have single responsibilities
- Code is DRY (Don't Repeat Yourself)
- Magic numbers are replaced with named constants

**Bonus**:
- Add TypeScript type definitions
- Add JSDoc comments
- Create unit tests

---

## Intermediate Tasks

### Task 3: Test Generation
**Objective**: Generate comprehensive unit tests for the refactored code.

**Instructions**:
1. After completing Task 2, generate unit tests for your refactored code
2. Use a testing framework (Jest, Mocha, or similar)
3. Ensure good test coverage (>80%)
4. Include edge cases and error scenarios

**Expected Outcome**:
- Complete test suite for refactored code
- All tests pass
- Good coverage of edge cases

---

### Task 4: Documentation Generation
**Objective**: Generate comprehensive documentation for the codebase.

**Instructions**:
1. Create API documentation for the refactored calculator and user management code
2. Add JSDoc/Python docstrings where missing
3. Create a user guide with examples
4. Document the architecture and design decisions

**Expected Outcome**:
- Complete API documentation
- Code comments and docstrings
- User guide with examples
- Architecture documentation

---

## Advanced Tasks

### Task 5: Feature Addition
**Objective**: Add a new feature to the calculator with proper TDD approach.

**Instructions**:
1. Add a new feature to calculate statistics (mean, median, mode) for a list of numbers
2. Follow Test-Driven Development:
   - Write tests first
   - Implement the feature
   - Refactor if needed
3. Ensure the new feature integrates well with existing code

**Expected Outcome**:
- New statistics module with mean, median, and mode functions
- Complete test coverage for new features
- Integration with existing calculator
- Documentation for new features

---

### Task 6: Performance Optimization
**Objective**: Optimize the factorial function for better performance.

**Instructions**:
1. The current factorial implementation uses recursion
2. Analyze potential performance issues
3. Implement an optimized version (consider memoization, iteration, or other techniques)
4. Create benchmarks to compare performance
5. Document the improvements

**Expected Outcome**:
- Optimized factorial implementation
- Performance benchmarks showing improvement
- Documentation of optimization techniques used

---

### Task 7: Error Handling and Validation
**Objective**: Add comprehensive error handling and input validation.

**Instructions**:
1. Review all calculator functions
2. Add input validation for all functions
3. Add appropriate error messages
4. Create custom exception classes
5. Add tests for error cases

**Expected Outcome**:
- All functions have input validation
- Custom exceptions for different error types
- Helpful error messages
- Tests for all error scenarios

---

## Integration Tasks

### Task 8: CI/CD Setup
**Objective**: Set up continuous integration for the project.

**Instructions**:
1. Create a GitHub Actions workflow (or similar)
2. Run tests on every commit
3. Run linters and formatters
4. Generate coverage reports
5. Add status badges to README

**Expected Outcome**:
- Working CI/CD pipeline
- Automated testing and linting
- Coverage reports
- Status badges

---

### Task 9: Code Quality Tools
**Objective**: Set up and configure code quality tools.

**Instructions**:
1. Configure ESLint for JavaScript code
2. Configure Pylint/Flake8 for Python code
3. Set up Prettier for code formatting
4. Configure pre-commit hooks
5. Ensure all code passes quality checks

**Expected Outcome**:
- Configured linters and formatters
- Pre-commit hooks working
- All code passes quality checks
- Configuration files committed

---

## Completion Checklist

After completing all tasks, verify:

- [ ] All bugs are fixed
- [ ] Code is refactored and follows best practices
- [ ] Comprehensive tests are written and passing
- [ ] Documentation is complete
- [ ] New features are implemented
- [ ] Performance is optimized
- [ ] Error handling is robust
- [ ] CI/CD is set up
- [ ] Code quality tools are configured
- [ ] All code is properly formatted and linted

---

## Notes for Agent Operators

When testing your coding agent:

1. **Start Simple**: Begin with Task 1 (bug fixing) to verify basic capabilities
2. **Progress Gradually**: Move through tasks in order
3. **Document Observations**: Note what works well and what doesn't
4. **Time Tracking**: Record how long each task takes
5. **Quality Assessment**: Evaluate the quality of generated code
6. **Iterative Testing**: Try tasks multiple times to assess consistency

## Evaluation Criteria

Rate the coding agent on:

1. **Correctness**: Does the code work as intended?
2. **Code Quality**: Is the code clean and well-structured?
3. **Completeness**: Are all requirements met?
4. **Efficiency**: How quickly can the agent complete tasks?
5. **Documentation**: Are explanations clear and helpful?
6. **Error Recovery**: Can the agent handle mistakes and iterate?
7. **Best Practices**: Does the code follow industry standards?

Good luck testing your coding agent!
