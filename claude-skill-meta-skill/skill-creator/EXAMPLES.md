# Skill Creator - Usage Examples

This document provides concrete examples of using the skill-creator meta skill to create various types of Claude Code skills.

## Example 1: Simple Code Reviewer Skill

### User Request
"I want a skill that reviews code for common bugs and security issues"

### skill-creator Workflow

#### Step 1: Clarification Questions
```
- What programming languages should this skill support?
- Should it focus on specific types of issues (security, performance, style)?
- Do you want it to suggest fixes or just identify problems?
- Should this be read-only or can it modify code?
```

#### Step 2: User Responses
```
- Languages: JavaScript and TypeScript
- Focus: Security issues and common bugs
- Just identify problems with explanations
- Read-only (no modifications)
```

#### Step 3: Generated Skill Structure
```
code-reviewer/
└── SKILL.md
```

#### Step 4: Generated SKILL.md
```yaml
---
name: code-reviewer
description: Reviewing JavaScript and TypeScript code for security vulnerabilities and common bugs. Use when the user asks to review code, check for security issues, or audit code quality. Read-only analysis without modifications.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

Reviews JavaScript and TypeScript code for security vulnerabilities and common bugs.

## When to Use This Skill

Activate when the user:
- Asks to review code or files
- Wants to check for security issues
- Needs code quality audit
- Mentions vulnerabilities or bugs

## Workflow

Make a todo list for all the tasks in this workflow and work on them one after another

### 1. Identify Files to Review

Ask the user which files or directories to review, or scan the project for JS/TS files:

```bash
# Find all JavaScript/TypeScript files
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \) ! -path "*/node_modules/*"
```

### 2. Analyze Each File

For each file, check for:

**Security Issues:**
- SQL injection vulnerabilities (string concatenation in queries)
- XSS vulnerabilities (unsafe innerHTML, dangerouslySetInnerHTML)
- Command injection (exec, spawn with user input)
- Path traversal (file operations with user input)
- Hardcoded credentials or API keys
- Weak cryptography (MD5, SHA1 for passwords)

**Common Bugs:**
- Null/undefined dereferencing
- Type coercion issues (== vs ===)
- Async/await error handling
- Memory leaks (event listeners, timers)
- Race conditions

### 3. Generate Report

Create a structured report:

```markdown
## Code Review Report

### File: [filename]

#### Security Issues
- [ ] **[SEVERITY]** [Issue description]
  - Line: [line number]
  - Code: `[code snippet]`
  - Explanation: [why this is an issue]
  - Recommendation: [how to fix]

#### Common Bugs
- [ ] **[SEVERITY]** [Bug description]
  - Line: [line number]
  - Code: `[code snippet]`
  - Explanation: [why this is problematic]
  - Recommendation: [how to fix]

### Summary
- Total files reviewed: X
- Security issues found: Y
- Bugs found: Z
```

### 4. Provide Recommendations

Prioritize findings by severity:
- 🔴 Critical: Immediate security risks
- 🟠 High: Significant bugs or security concerns
- 🟡 Medium: Code quality issues
- 🟢 Low: Minor improvements

## Examples

### Example: SQL Injection Detection

```javascript
// ❌ Vulnerable code
const query = "SELECT * FROM users WHERE id = " + userId;
db.query(query);

// ✅ Safe alternative
const query = "SELECT * FROM users WHERE id = ?";
db.query(query, [userId]);
```

### Example: XSS Vulnerability

```javascript
// ❌ Vulnerable code
element.innerHTML = userInput;

// ✅ Safe alternative
element.textContent = userInput;
// or use a sanitization library
```

## Wrap Up

Provide a summary of the review:
```
✅ Code Review Complete

Files Reviewed: [count]
Issues Found:
  - 🔴 Critical: [count]
  - 🟠 High: [count]
  - 🟡 Medium: [count]
  - 🟢 Low: [count]

Top Priority: [most critical issue]

Detailed report saved to: code-review-report.md
```
```

### Testing
```
User: "Can you review my auth.js file for security issues?"
Expected: skill-creator activates, follows workflow, generates code-reviewer skill
Result: ✅ Pass
```

---

## Example 2: API Test Generator Skill

### User Request
"Create a skill that helps me write integration tests for REST APIs"

### Generated Skill Structure
```
api-test-generator/
├── SKILL.md
├── EXAMPLES.md
└── templates/
    ├── jest-api-test.js
    └── mocha-api-test.js
```

### Key Features
- Generates test files from API specifications
- Supports multiple testing frameworks (Jest, Mocha, Supertest)
- Creates mock data and assertions
- Handles authentication scenarios

### Sample Template (jest-api-test.js)
```javascript
const request = require('supertest');
const app = require('../app');

describe('{{API_NAME}} API', () => {
  describe('{{METHOD}} {{ENDPOINT}}', () => {
    it('should return {{EXPECTED_STATUS}} with valid input', async () => {
      const response = await request(app)
        .{{METHOD_LOWER}}('{{ENDPOINT}}')
        .send({{REQUEST_BODY}})
        .expect({{EXPECTED_STATUS}});

      expect(response.body).toMatchObject({{EXPECTED_RESPONSE}});
    });

    it('should handle authentication', async () => {
      const response = await request(app)
        .{{METHOD_LOWER}}('{{ENDPOINT}}')
        .set('Authorization', 'Bearer {{TOKEN}}')
        .expect({{EXPECTED_STATUS}});
    });

    it('should validate input', async () => {
      const response = await request(app)
        .{{METHOD_LOWER}}('{{ENDPOINT}}')
        .send({{INVALID_INPUT}})
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });
  });
});
```

---

## Example 3: Commit Message Helper Skill

### User Request
"I want a skill that helps me write better git commit messages following conventional commits"

### Generated Skill Structure
```
commit-helper/
├── SKILL.md
└── REFERENCE.md
```

### Key Features
- Analyzes git diff to understand changes
- Suggests conventional commit format
- Validates commit message structure
- Provides examples based on changes

### Workflow Excerpt
```markdown
### 2. Analyze Changes

Run git diff to understand what changed:

```bash
git diff --cached
```

Categorize changes:
- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation changes
- **style**: Code formatting
- **refactor**: Code restructuring
- **test**: Test additions/changes
- **chore**: Build process, dependencies

### 3. Generate Commit Message

Format: `<type>(<scope>): <subject>`

Example:
```
feat(auth): add OAuth2 authentication flow

- Implement OAuth2 client
- Add token refresh logic
- Update user session handling

Closes #123
```
```

---

## Example 4: Database Migration Skill

### User Request
"Create a skill for managing database migrations safely"

### Generated Skill Structure
```
db-migration-manager/
├── SKILL.md
├── REFERENCE.md
├── EXAMPLES.md
└── templates/
    ├── migration-template.sql
    └── rollback-template.sql
```

### Key Features
- Creates migration files with timestamps
- Validates SQL syntax before execution
- Generates rollback scripts automatically
- Tests migrations in transaction mode
- Provides safety checks

### Safety Workflow
```markdown
### 3. Safety Checks

Before applying migration:

- [ ] Backup verification
- [ ] Syntax validation
- [ ] Dependency check
- [ ] Rollback script ready
- [ ] Test in transaction mode

### 4. Apply Migration

```bash
# Test in transaction (will rollback)
psql -d mydb -f migrations/20240101_add_users.sql --single-transaction --set ON_ERROR_STOP=on

# If successful, apply for real
psql -d mydb -f migrations/20240101_add_users.sql
```

### 5. Verify Migration

```sql
-- Check table exists
SELECT * FROM information_schema.tables WHERE table_name = 'users';

-- Check columns
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'users';
```
```

---

## Example 5: Performance Benchmark Skill

### User Request
"I need a skill to benchmark and compare performance of different implementations"

### Generated Skill Structure
```
perf-benchmark/
├── SKILL.md
├── EXAMPLES.md
└── scripts/
    ├── benchmark-runner.js
    └── results-formatter.js
```

### Key Features
- Runs multiple iterations for statistical significance
- Compares multiple implementations
- Generates visual charts (ASCII art)
- Provides statistical analysis (mean, median, stddev)
- Exports results in various formats (JSON, CSV, Markdown)

### Sample Output
```markdown
## Benchmark Results: Array vs Set Lookup

### Configuration
- Iterations: 10,000
- Data size: 1,000 items
- Node.js: v18.17.0

### Results

| Implementation | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | Std Dev |
|---------------|-----------|-------------|----------|----------|---------|
| Array.includes| 0.234     | 0.228       | 0.201    | 0.312    | 0.023   |
| Set.has       | 0.012     | 0.011       | 0.009    | 0.019    | 0.002   |

### Winner: Set.has (19.5x faster)

### Chart
```
Array.includes: ████████████████████████████████████████ 0.234ms
Set.has       : ██ 0.012ms
```

### Recommendation
Use Set.has for lookups when dealing with large datasets.
```

---

## Tips for Using skill-creator

### 1. Be Specific About Requirements
Instead of: "Create a testing skill"
Better: "Create a skill that generates unit tests for React components using Jest and React Testing Library"

### 2. Specify Tool Permissions
- Read-only analysis: `allowed-tools: Read, Grep, Glob`
- File generation: Add `Write`
- Code modification: Add `Edit`
- System operations: Add `Bash`

### 3. Provide Examples
If you have a specific workflow in mind, share an example:
```
"When I run the skill, I want it to:
1. Scan my src/ directory
2. Find all .jsx files
3. Generate corresponding .test.jsx files
4. Use this test template: [example]"
```

### 4. Iterate and Refine
After the skill is created:
- Test it with different scenarios
- Ask for modifications if needed
- Add more examples or templates
- Enhance the workflow based on experience

### 5. Share with Team
For project-specific skills:
```bash
# Commit to git for team access
git add .claude/skills/my-skill/
git commit -m "Add my-skill for [purpose]"
git push
```

Team members will automatically get the skill when they pull the repository.

---

## Common Patterns

### Pattern: Multi-Step Validation
```markdown
### N. Validate Result

- [ ] Check 1
- [ ] Check 2
- [ ] Check 3

If any check fails, rollback and report error.
```

### Pattern: User Choice
```markdown
### N. Select Framework

Ask user to choose:
1. Jest
2. Mocha
3. Jasmine

Based on choice, use corresponding template.
```

### Pattern: Progressive Enhancement
```markdown
### N. Basic Implementation

[Simple version]

### N+1. Advanced Features (Optional)

If user needs:
- Feature A: [implementation]
- Feature B: [implementation]
```

### Pattern: Error Recovery
```markdown
### N. Execute Operation

Try:
  [operation]
Catch error:
  - Log error details
  - Attempt recovery: [strategy]
  - If recovery fails, rollback to previous state
  - Report to user with actionable advice
```

---

## Troubleshooting

### My skill isn't activating

**Check:**
1. Is the description clear and specific?
2. Does it mention trigger keywords?
3. Is the YAML frontmatter valid?

**Fix:**
Improve the description to include more trigger scenarios:
```yaml
description: Original description. Use when the user [scenario 1], [scenario 2], or [scenario 3].
```

### Skill has too many/few permissions

**Fix:**
Update `allowed-tools` in frontmatter:
```yaml
# Read-only
allowed-tools: Read, Grep, Glob

# Full development
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite
```

### Skill workflow is confusing

**Fix:**
1. Simplify steps
2. Add more examples
3. Use numbered lists consistently
4. Add validation checkpoints

---

## Next Steps

After using skill-creator:

1. **Test thoroughly**: Try different scenarios
2. **Document edge cases**: Add to EXAMPLES.md
3. **Share with team**: Commit to project repo
4. **Iterate**: Improve based on feedback
5. **Contribute**: Consider sharing useful skills with the community

For more information, see the main [README.md](../README.md).
